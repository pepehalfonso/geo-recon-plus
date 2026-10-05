import socket

import pytest
from georecon.errors import InvalidTargetError
from georecon.resolver import is_hostname, resolve


def _addrinfo(*addresses):
    def getaddrinfo(host, port, family=0, proto=0, **kwargs):
        entries = []
        for address in addresses:
            family_code = socket.AF_INET6 if ":" in address else socket.AF_INET
            entries.append((family_code, socket.SOCK_STREAM, proto, "", (address, 0)))
        return entries

    return getaddrinfo


def test_ip_target_is_returned_untouched():
    resolution = resolve("8.8.8.8")
    assert resolution.ip == "8.8.8.8"
    assert resolution.is_direct
    assert resolution.resolved_from is None


def test_hostname_resolves_preferring_ipv4():
    resolution = resolve("example.com", getaddrinfo=_addrinfo("2606:2800:220:1:248:1893:25c8:1946", "93.184.216.34"))
    assert resolution.ip == "93.184.216.34"
    assert resolution.target == "example.com"
    assert not resolution.is_direct


def test_hostname_resolves_to_ipv6_when_only_v6_available():
    resolution = resolve("v6.example", getaddrinfo=_addrinfo("2001:db8::1"))
    assert resolution.ip == "2001:db8::1"


def test_unresolvable_hostname_raises():
    def failing(host, port, **kwargs):
        raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")

    with pytest.raises(InvalidTargetError, match="could not resolve"):
        resolve("nope.example", getaddrinfo=failing)


def test_resolving_something_that_is_not_a_name_raises():
    with pytest.raises(InvalidTargetError, match="not an IP address or a hostname"):
        resolve("not a host!!")
    with pytest.raises(InvalidTargetError):
        resolve("   ")


@pytest.mark.parametrize(
    "value,expected",
    [
        ("example.com", True),
        ("sub.domain.example.co", True),
        ("localhost", True),
        ("8.8.8.8", False),
        ("2001:db8::1", False),
        ("https://example.com", False),
        ("-bad.com", False),
        ("bad-.com", False),
        ("double..dot", False),
        ("has space.com", False),
        ("".join("a" for _ in range(300)) + ".com", False),
    ],
)
def test_is_hostname(value, expected):
    assert is_hostname(value) is expected
