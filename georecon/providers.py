"""Remote data sources.

Everything here is a pure function of the injected ``get`` callable, which
makes the whole package testable without touching the network.
"""

from __future__ import annotations

import ipaddress
from typing import Any, Optional

from georecon.errors import NetworkError, ProviderError
from georecon.http import Getter
from georecon.models import ConnectionInfo, GeoInfo, Reputation

IPWHOIS_URL = "https://ipwho.is/{ip}"
IPWHOIS_SELF_URL = "https://ipwho.is/"
IPIFY_URL = "https://api.ipify.org?format=json"
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"
DOH_URL = "https://dns.google/resolve"

DNSBL_ZONES = (
    "zen.spamhaus.org",
    "bl.spamcop.net",
    "b.barracudacentral.org",
)


def geo_lookup(ip: str, get: Getter) -> tuple[GeoInfo, ConnectionInfo, str]:
    """Geolocate *ip* with ipwho.is. Returns (geo, connection, provider)."""
    body = get(IPWHOIS_URL.format(ip=ip))
    if not isinstance(body, dict):
        raise ProviderError("ipwho.is returned an unexpected payload")
    if body.get("success") is False:
        message = body.get("message") or body.get("ip") or "lookup refused"
        raise ProviderError(f"ipwho.is: {message}")

    raw_geo = body.get("geo") or body
    connection = body.get("connection") or {}
    timezone = body.get("timezone") or {}

    geo = GeoInfo(
        country=raw_geo.get("country"),
        country_code=raw_geo.get("country_code"),
        region=raw_geo.get("region"),
        city=raw_geo.get("city"),
        latitude=_number(raw_geo.get("latitude")),
        longitude=_number(raw_geo.get("longitude")),
        timezone=timezone.get("id") if isinstance(timezone, dict) else None,
        postal=raw_geo.get("postal"),
        flag=_flag(raw_geo.get("country_code") or body.get("country_code")),
    )
    info = ConnectionInfo(
        asn=_integer(connection.get("asn")),
        org=connection.get("org"),
        isp=connection.get("isp"),
        domain=connection.get("domain"),
    )
    return geo, info, "ipwho.is"


def detect_own_ip(get: Getter) -> str:
    """Return the public IP of the caller, with a fallback provider."""
    try:
        body = get(IPWHOIS_SELF_URL)
        if isinstance(body, dict) and body.get("success") is not False and body.get("ip"):
            return str(body["ip"])
    except (ProviderError, NetworkError):
        pass
    body = get(IPIFY_URL)
    if isinstance(body, dict) and body.get("ip"):
        return str(body["ip"])
    raise ProviderError("could not determine the public IP address")


def reverse_dns(ip: str, get: Getter) -> Optional[str]:
    """Resolve the PTR record for *ip* through DNS-over-HTTPS."""
    name = _ptr_name(ip)
    if name is None:
        return None
    try:
        body = get(DOH_URL, params={"name": name, "type": "PTR"})
    except (ProviderError, NetworkError):
        return None
    if not isinstance(body, dict) or body.get("Status") != 0:
        return None
    for answer in body.get("Answer") or []:
        data = str(answer.get("data", "")).rstrip(".")
        if data:
            return data
    return None


def _ptr_name(ip: str) -> Optional[str]:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if address.version == 4:
        return address.reverse_pointer
    nibbles = ".".join(reversed(address.exploded.replace(":", "")))
    return f"{nibbles}.ip6.arpa"


def abuseipdb_lookup(ip: str, key: str, get: Getter) -> Reputation:
    """Query AbuseIPDB with the caller's own API key."""
    headers = {"Accept": "application/json", "Key": key}
    body = get(
        ABUSEIPDB_URL,
        params={"ipAddress": ip, "maxAgeInDays": "90"},
        headers=headers,
    )
    if not isinstance(body, dict):
        raise ProviderError("AbuseIPDB returned an unexpected payload")
    if body.get("errors"):
        details = "; ".join(
            str(error.get("detail", error)) for error in body["errors"]
        )
        raise ProviderError(f"AbuseIPDB: {details}")

    data = body.get("data") or {}
    score = _integer(data.get("abuseConfidenceScore"))
    reputation = Reputation(
        source="abuseipdb",
        score=score,
        reports=_integer(data.get("totalReports")),
        last_reported=data.get("lastReportedAt"),
        whitelisted=bool(data.get("isWhitelisted")),
        verdict=_verdict_from_score(score),
        notes=[f"usage type: {data.get('usageType') or 'unknown'}"],
    )
    if data.get("domain"):
        reputation.notes.append(f"domain: {data['domain']}")
    return reputation


def dnsbl_lookup(ip: str, get: Getter, zones: tuple[str, ...] = DNSBL_ZONES) -> Reputation:
    """Keyless reputation probe: reverse the IP and ask public DNS blocklists."""
    if ":" in ip:
        # DNSBLs are IPv4-only; IPv6 has no reverse zone in these lists.
        return Reputation(source="dnsbl", verdict="unknown", notes=["DNSBL lists are IPv4-only"])

    octets = ip.split(".")
    if len(octets) != 4:
        return Reputation(source="dnsbl", verdict="unknown")
    reversed_ip = ".".join(reversed(octets))

    listed: list[str] = []
    checked: list[str] = []
    for zone in zones:
        try:
            body = get(DOH_URL, params={"name": f"{reversed_ip}.{zone}", "type": "A"})
        except Exception:
            continue
        checked.append(zone)
        if not isinstance(body, dict):
            continue
        if body.get("Status") == 0:
            answers = body.get("Answer") or []
            for answer in answers:
                data = str(answer.get("data", ""))
                if data.startswith("127."):
                    listed.append(f"{zone} ({data})")
                    break

    if not checked:
        return Reputation(source="dnsbl", verdict="unknown", notes=["no blocklist reachable"])

    reputation = Reputation(source="dnsbl", verdict="clean")
    reputation.notes.append(f"checked {len(checked)} DNS blocklists")
    if listed:
        reputation.verdict = "suspicious"
        reputation.notes.extend(f"listed on {entry}" for entry in listed)
    else:
        reputation.notes.append("not listed on any checked blocklist")
    return reputation


def merge_reputation(primary: Reputation, extra: Reputation) -> Reputation:
    """Combine the authoritative source with the keyless DNSBL signal."""
    if primary.source == "none":
        return extra
    notes = list(primary.notes) + list(extra.notes)
    if extra.verdict == "suspicious" and primary.verdict == "clean":
        primary.verdict = "suspicious"
        primary.notes = notes
        primary.notes.append("upgraded: listed on a DNS blocklist")
        return primary
    primary.notes = notes
    return primary


def _verdict_from_score(score: Optional[int]) -> str:
    if score is None:
        return "unknown"
    if score >= 75:
        return "malicious"
    if score >= 25:
        return "suspicious"
    return "clean"


def _number(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _integer(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _flag(country_code: Any) -> Optional[str]:
    if not isinstance(country_code, str) or len(country_code) != 2:
        return None
    return "".join(chr(0x1F1E6 + ord(char) - ord("A")) for char in country_code.upper())
