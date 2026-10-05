"""Orchestrates providers into a single LookupResult."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from georecon.errors import NetworkError, ProviderError
from georecon.http import Getter, build_getter
from georecon.models import LookupResult, parse_target, scope_of
from georecon.providers import (
    Reputation,
    abuseipdb_lookup,
    detect_own_ip,
    dnsbl_lookup,
    geo_lookup,
    merge_reputation,
    reverse_dns,
)
from georecon.resolver import Resolution
from georecon.resolver import resolve as resolve_target

ABUSEIPDB_ENV = "ABUSEIPDB_KEY"


class Lookup:
    """Runs the provider chain for a target IP."""

    def __init__(
        self,
        get: Getter | None = None,
        abuseipdb_key: str | None = None,
        with_reputation: bool = True,
        resolver: Callable[[str], Resolution] | None = None,
    ) -> None:
        self.get = get or build_getter()
        if abuseipdb_key is None:
            abuseipdb_key = os.environ.get(ABUSEIPDB_ENV, "").strip()
        self.abuseipdb_key = abuseipdb_key
        self.with_reputation = with_reputation
        self._resolve = resolver or resolve_target
        self.warnings: list[str] = []

    def run(self, target: str) -> LookupResult:
        return self.run_resolution(self._resolve(target))

    def run_resolution(self, resolution: Resolution) -> LookupResult:
        self.warnings = []
        address = parse_target(resolution.ip)
        result = LookupResult(ip=str(address), version=f"IPv{address.version}")
        if not resolution.is_direct:
            result.target = resolution.target

        scope = scope_of(address)
        if scope is not None:
            result.is_private = True
            result.reputation.verdict = "unknown"
            result.reputation.notes.append(
                f"{address} is a {scope} address, so there is no public data for it"
            )
            return result

        result.geo, result.connection, result.provider = geo_lookup(str(address), self.get)
        result.hostname = reverse_dns(str(address), self.get)
        if self.with_reputation:
            result.reputation = self._reputation(str(address))
        result.warnings = list(self.warnings)
        return result

    def run_own(self) -> LookupResult:
        return self.run(detect_own_ip(self.get))

    def _reputation(self, ip: str) -> Reputation:
        primary = Reputation(source="none")
        if self.abuseipdb_key:
            try:
                primary = abuseipdb_lookup(ip, self.abuseipdb_key, self.get)
            except (ProviderError, NetworkError) as exc:
                self.warnings.append(f"AbuseIPDB skipped: {exc}")

        try:
            secondary = dnsbl_lookup(ip, self.get)
        except NetworkError as exc:
            self.warnings.append(f"DNSBL skipped: {exc}")
            secondary = Reputation(source="none")

        return merge_reputation(primary, secondary)


def lookup(target: str, **kwargs: Any) -> LookupResult:
    """Convenience wrapper: ``lookup("8.8.8.8")``."""
    return Lookup(**kwargs).run(target)


def lookup_own(**kwargs: Any) -> LookupResult:
    return Lookup(**kwargs).run_own()
