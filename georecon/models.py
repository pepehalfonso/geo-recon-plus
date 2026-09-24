"""Data structures shared by the CLI and the report emitters."""

from __future__ import annotations

import ipaddress
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from georecon.errors import InvalidTargetError

VERDICTS = ("clean", "suspicious", "malicious", "unknown")


def parse_target(raw: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Parse *raw* into an IP address object or raise InvalidTargetError."""
    candidate = raw.strip()
    if candidate.startswith("[") and candidate.endswith("]"):
        candidate = candidate[1:-1]
    try:
        return ipaddress.ip_address(candidate)
    except ValueError:
        pass
    # Allow "host:port" pasted from a browser URL.
    if candidate.count(":") == 1 and not candidate.count("::"):
        host, _, port = candidate.partition(":")
        if port.isdigit():
            try:
                return ipaddress.ip_address(host)
            except ValueError:
                pass
    raise InvalidTargetError(f"'{raw}' is not a valid IP address")


@dataclass
class GeoInfo:
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    postal: Optional[str] = None
    flag: Optional[str] = None

    @property
    def place(self) -> str:
        parts = [p for p in (self.city, self.region, self.country) if p]
        return ", ".join(parts) if parts else "unknown"


@dataclass
class ConnectionInfo:
    asn: Optional[int] = None
    org: Optional[str] = None
    isp: Optional[str] = None
    domain: Optional[str] = None

    @property
    def asn_label(self) -> str:
        return f"AS{self.asn}" if self.asn else "unknown"


@dataclass
class Reputation:
    source: str = "none"
    score: Optional[int] = None
    reports: Optional[int] = None
    last_reported: Optional[str] = None
    whitelisted: Optional[bool] = None
    verdict: str = "unknown"
    notes: list[str] = field(default_factory=list)


@dataclass
class LookupResult:
    ip: str
    version: str = "IPv4"
    geo: GeoInfo = field(default_factory=GeoInfo)
    connection: ConnectionInfo = field(default_factory=ConnectionInfo)
    reputation: Reputation = field(default_factory=Reputation)
    is_private: bool = False
    hostname: Optional[str] = None
    provider: str = "ipwho.is"
    warnings: list[str] = field(default_factory=list)

    @property
    def is_global(self) -> bool:
        return not self.is_private

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_IPV4_SPECIAL_NETWORKS = (
    ("192.0.2.0/24", "documentation"),
    ("198.51.100.0/24", "documentation"),
    ("203.0.113.0/24", "documentation"),
    ("198.18.0.0/15", "benchmarking"),
    ("100.64.0.0/10", "carrier-grade NAT"),
)


def scope_of(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Optional[str]:
    """Return a human label for non-public addresses, else None."""
    if address.is_loopback:
        return "loopback"
    if address.is_link_local:
        return "link-local"
    if address.is_multicast:
        return "multicast"
    if address.is_unspecified:
        return "unspecified"
    if address.version == 4:
        for cidr, label in _IPV4_SPECIAL_NETWORKS:
            if address in ipaddress.ip_network(cidr):
                return label
    if address.is_private:
        return "private"
    if address.is_reserved:
        return "reserved"
    if not address.is_global:
        return "non-global"
    return None
