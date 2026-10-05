from georecon.lookup import Lookup

from tests.conftest import ABUSE_BAD, IPWHOIS_OK, FakeGet


def test_public_ip_returns_geo_without_key():
    lookup = Lookup(get=FakeGet({"ipwho.is": IPWHOIS_OK, "dns.google/resolve": {"Status": 3}}), abuseipdb_key="")
    result = lookup.run("8.8.8.8")
    assert result.ip == "8.8.8.8"
    assert result.is_private is False
    assert result.geo.city == "San Jose"
    assert result.connection.isp == "Google LLC"
    assert result.reputation.source == "dnsbl"
    assert result.reputation.verdict == "clean"
    assert result.warnings == []


def test_private_ip_never_touches_the_network():
    get = FakeGet({})
    result = Lookup(get=get).run("192.168.1.4")
    assert result.is_private is True
    assert get.calls == []
    assert result.reputation.verdict == "unknown"
    assert "private" in result.reputation.notes[0]


def test_key_enables_abuseipdb_and_is_sent_as_header():
    get = FakeGet({"ipwho.is": IPWHOIS_OK, "abuseipdb": ABUSE_BAD, "dns.google/resolve": {"Status": 3}})
    result = Lookup(get=get, abuseipdb_key="secret").run("8.8.8.8")
    assert result.reputation.source == "abuseipdb"
    assert result.reputation.verdict == "malicious"
    abuse_calls = [c for c in get.calls if "abuseipdb" in c["url"]]
    assert abuse_calls[0]["headers"]["Key"] == "secret"


def test_abuseipdb_failure_degrades_to_dnsbl_instead_of_crashing():
    get = FakeGet(
        {
            "ipwho.is": IPWHOIS_OK,
            "abuseipdb": {"errors": [{"detail": "quota exceeded"}]},
            "dns.google/resolve": {"Status": 3},
        }
    )
    result = Lookup(get=get, abuseipdb_key="expired").run("8.8.8.8")
    assert result.reputation.verdict == "clean"
    assert any("AbuseIPDB skipped" in warning for warning in result.warnings)


def test_reputation_can_be_disabled():
    get = FakeGet({"ipwho.is": IPWHOIS_OK, "dns.google/resolve": {"Status": 3}})
    result = Lookup(get=get, with_reputation=False).run("8.8.8.8")
    assert result.reputation.source == "none"
    assert not any("abuseipdb" in url for url in get.urls)
    assert result.hostname is None


def test_own_ip_lookup_uses_self_endpoint():
    get = FakeGet(
        {
            # First match wins, so the specific geo route goes first.
            "ipwho.is/200.45.10.7": IPWHOIS_OK,
            "ipwho.is": {"ip": "200.45.10.7", "success": True},
            "dns.google/resolve": {"Status": 3},
        }
    )
    result = Lookup(get=get, abuseipdb_key="").run_own()
    assert result.ip == "200.45.10.7"
    assert result.is_private is False
    assert result.geo.city == "San Jose"
    assert not any("ipify" in url for url in get.urls)
