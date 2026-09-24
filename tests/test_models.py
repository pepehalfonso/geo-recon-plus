import ipaddress

import pytest

from georecon.errors import InvalidTargetError
from georecon.models import GeoInfo, parse_target, scope_of


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("8.8.8.8", "8.8.8.8"),
        (" 8.8.8.8 ", "8.8.8.8"),
        ("2001:4860:4860::8888", "2001:4860:4860::8888"),
        ("[2001:db8::1]", "2001:db8::1"),
        ("1.2.3.4:8080", "1.2.3.4"),
    ],
)
def test_parse_target_accepts_valid_values(raw, expected):
    assert str(parse_target(raw)) == expected


@pytest.mark.parametrize("raw", ["", "not-an-ip", "999.1.1.1", "1.2.3", "host"])
def test_parse_target_rejects_garbage(raw):
    with pytest.raises(InvalidTargetError):
        parse_target(raw)


@pytest.mark.parametrize(
    "raw,label",
    [
        ("192.168.1.10", "private"),
        ("10.0.0.1", "private"),
        ("127.0.0.1", "loopback"),
        ("169.254.1.1", "link-local"),
        ("224.0.0.1", "multicast"),
        ("203.0.113.10", "documentation"),
        ("100.64.0.1", "carrier-grade NAT"),
        ("8.8.8.8", None),
    ],
)
def test_scope_of(raw, label):
    assert scope_of(ipaddress.ip_address(raw)) == label


def test_geo_place_joins_available_parts():
    geo = GeoInfo(city="Rome", region="Lazio", country="Italy")
    assert geo.place == "Rome, Lazio, Italy"
    assert GeoInfo().place == "unknown"
