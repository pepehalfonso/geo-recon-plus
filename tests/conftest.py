from typing import Any

import pytest
from georecon.lookup import Lookup

IPWHOIS_OK = {
    "ip": "8.8.8.8",
    "success": True,
    "type": "IPv4",
    "country": "United States",
    "country_code": "US",
    "region": "California",
    "city": "San Jose",
    "latitude": 37.3393939,
    "longitude": -121.8949553,
    "postal": "95025",
    "connection": {"asn": 15169, "org": "Google LLC", "isp": "Google LLC", "domain": "google.com"},
    "timezone": {"id": "America/Los_Angeles"},
}

IPWHOIS_FAIL = {"ip": "999.1.1.1", "success": False, "message": "Invalid IP address"}

ABUSE_CLEAN = {"data": {"abuseConfidenceScore": 0, "totalReports": 3, "lastReportedAt": "2026-01-01T00:00:00+00:00", "isWhitelisted": True, "usageType": "Data Center", "domain": "google.com"}}
ABUSE_BAD = {"data": {"abuseConfidenceScore": 100, "totalReports": 982, "lastReportedAt": "2026-01-01T00:00:00+00:00", "isWhitelisted": False, "usageType": "Fixed Line ISP", "domain": None}}
ABUSE_ERROR = {"errors": [{"detail": "The provided API key is invalid."}]}


class FakeGet:
    """Stands in for georecon.http.build_getter. First matching route wins.

    A route value of ``{"error": "..."}`` raises NetworkError, which is how
    tests simulate an unreachable provider.
    """

    def __init__(self, routes: dict | None = None, default: Any = None):
        self.routes = routes or {}
        self.default = default
        self.calls: list[dict] = []

    def __call__(self, url: str, *, params: dict | None = None, timeout: float = 0, headers=None, **kwargs):
        self.calls.append({"url": url, "params": params or {}, "headers": headers or {}})
        for pattern, payload in self.routes.items():
            if pattern in url or (params and pattern in str(params.get("name", ""))):
                if callable(payload):
                    return payload()
                if isinstance(payload, dict) and "error" in payload:
                    from georecon.errors import NetworkError

                    raise NetworkError(payload["error"])
                return payload
        if self.default is not None:
            return self.default
        raise AssertionError(f"unexpected url: {url}")

    @property
    def urls(self) -> list[str]:
        return [call["url"] for call in self.calls]


def make_lookup(routes: dict, **kwargs) -> Lookup:
    return Lookup(get=FakeGet(routes), **kwargs)


@pytest.fixture
def routes():
    return {
        "ipwho.is/8.8.8.8": IPWHOIS_OK,
        "dns.google/resolve": {"Status": 3},
    }
