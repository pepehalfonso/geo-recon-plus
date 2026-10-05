"""Reachability checks for every provider the tool depends on."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from georecon.errors import NetworkError, ProviderError
from georecon.http import Getter
from georecon.providers import (
    ABUSEIPDB_URL,
    DOH_URL,
    IPIFY_URL,
    IPWHOIS_URL,
)


@dataclass
class Probe:
    name: str
    ok: bool
    detail: str
    latency_ms: int | None = None


_PROBE_IP = "8.8.8.8"


def selftest(get: Getter, abuseipdb_key: str | None = None) -> list[Probe]:
    """Check each provider and report latency, without failing fast."""
    probes: list[Probe] = []

    probes.append(_probe("geolocation (ipwho.is)", lambda: get(IPWHOIS_URL.format(ip=_PROBE_IP))))
    probes.append(_probe("public IP (ipify)", lambda: get(IPIFY_URL)))
    probes.append(
        _probe(
            "DNS over HTTPS (dns.google)",
            lambda: get(DOH_URL, params={"name": "8.8.8.8.in-addr.arpa", "type": "PTR"}),
        )
    )
    if abuseipdb_key:
        probes.append(
            _probe(
                "reputation (AbuseIPDB)",
                lambda: get(
                    ABUSEIPDB_URL,
                    params={"ipAddress": _PROBE_IP, "maxAgeInDays": "1"},
                    headers={"Key": abuseipdb_key, "Accept": "application/json"},
                ),
            )
        )
    else:
        probes.append(
            Probe("reputation (AbuseIPDB)", False, "skipped: set ABUSEIPDB_KEY to test it")
        )
    return probes


def _probe(name: str, call: Callable[[], Any]) -> Probe:
    started = time.perf_counter()
    try:
        body = call()
    except (NetworkError, ProviderError) as exc:
        return Probe(name, False, str(exc), _elapsed_ms(started))
    if not isinstance(body, dict):
        return Probe(name, False, "unexpected payload", _elapsed_ms(started))
    return Probe(name, True, "ok", _elapsed_ms(started))


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def worst_status(probes: list[Probe]) -> int:
    """Exit code for a selftest: 0 when every reachable probe worked."""
    hard_failures = [probe for probe in probes if not probe.ok and "skipped" not in probe.detail]
    return 1 if hard_failures else 0
