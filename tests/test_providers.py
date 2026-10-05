import pytest
from georecon import providers
from georecon.errors import ProviderError
from georecon.models import ConnectionInfo, Reputation

from tests.conftest import ABUSE_BAD, ABUSE_CLEAN, ABUSE_ERROR, IPWHOIS_FAIL, IPWHOIS_OK, FakeGet


def test_geo_lookup_parses_payload():
    geo, conn, provider = providers.geo_lookup("8.8.8.8", FakeGet({"ipwho.is": IPWHOIS_OK}))
    assert provider == "ipwho.is"
    assert geo.country == "United States"
    assert geo.city == "San Jose"
    assert geo.latitude == pytest.approx(37.3393939)
    assert geo.timezone == "America/Los_Angeles"
    assert geo.flag == "\U0001F1FA\U0001F1F8"
    assert conn == ConnectionInfo(asn=15169, org="Google LLC", isp="Google LLC", domain="google.com")


def test_geo_lookup_raises_on_refusal():
    with pytest.raises(ProviderError):
        providers.geo_lookup("999.1.1.1", FakeGet({"ipwho.is": IPWHOIS_FAIL}))


def test_abuseipdb_verdicts():
    clean = providers.abuseipdb_lookup("8.8.8.8", "key", FakeGet({"abuseipdb": ABUSE_CLEAN}))
    assert clean.verdict == "clean"
    assert clean.score == 0
    assert clean.source == "abuseipdb"

    bad = providers.abuseipdb_lookup("1.2.3.4", "key", FakeGet({"abuseipdb": ABUSE_BAD}))
    assert bad.verdict == "malicious"
    assert bad.score == 100
    assert bad.reports == 982


def test_abuseipdb_surfaces_api_errors():
    with pytest.raises(ProviderError, match="API key is invalid"):
        providers.abuseipdb_lookup("8.8.8.8", "bad", FakeGet({"abuseipdb": ABUSE_ERROR}))


def test_dnsbl_clean_when_not_listed():
    rep = providers.dnsbl_lookup("8.8.8.8", FakeGet({"dns.google/resolve": {"Status": 3}}))
    assert rep.verdict == "clean"
    assert rep.source == "dnsbl"
    assert any("not listed" in note for note in rep.notes)


def test_dnsbl_flags_listed_ip():
    answer = {"Status": 0, "Answer": [{"data": "127.0.0.2", "type": 1}]}
    rep = providers.dnsbl_lookup("203.0.113.10", FakeGet({"dns.google/resolve": answer}))
    assert rep.verdict == "suspicious"
    assert any("listed on" in note for note in rep.notes)


def test_dnsbl_skips_ipv6():
    rep = providers.dnsbl_lookup("2001:4860:4860::8888", FakeGet({}))
    assert rep.verdict == "unknown"
    assert any("IPv4-only" in note for note in rep.notes)


def test_dnsbl_survives_unreachable_blocklists():
    get = FakeGet({"dns.google/resolve": {"error": "timeout"}})
    rep = providers.dnsbl_lookup("8.8.8.8", get)
    assert rep.verdict == "unknown"
    assert any("no blocklist reachable" in note for note in rep.notes)


def test_dnsbl_treats_rate_limit_answers_as_refused_not_listed():
    blocked = {"Status": 0, "Answer": [{"data": "127.255.255.254", "type": 1}]}
    rep = providers.dnsbl_lookup("8.8.8.8", FakeGet({"dns.google/resolve": blocked}))
    assert rep.verdict == "unknown"
    assert not any("listed on" in note for note in rep.notes)
    assert any("refused" in note for note in rep.notes)


def test_dnsbl_counts_only_zones_that_answered():
    calls = {"n": 0}

    def payload():
        calls["n"] += 1
        if calls["n"] == 1:
            return {"Status": 0, "Answer": [{"data": "127.255.255.254", "type": 1}]}
        return {"Status": 3}

    rep = providers.dnsbl_lookup("8.8.8.8", FakeGet({"dns.google/resolve": payload}))
    assert rep.verdict == "clean"
    assert any("checked 3 DNS blocklists" in note for note in rep.notes)
    assert any("refused by" in note for note in rep.notes)


def test_merge_reputation_prefers_primary_but_respects_dnsbl():
    primary = Reputation(source="abuseipdb", score=0, verdict="clean")
    listed = Reputation(source="dnsbl", verdict="suspicious", notes=["listed on zen"])
    merged = providers.merge_reputation(primary, listed)
    assert merged.verdict == "suspicious"
    assert merged.source == "abuseipdb"

    empty = Reputation(source="none")
    only_dnsbl = Reputation(source="dnsbl", verdict="clean", notes=["ok"])
    assert providers.merge_reputation(empty, only_dnsbl) is only_dnsbl


def test_detect_own_ip_falls_back_to_ipify():
    get = FakeGet({"ipwho.is": {"success": False}, "api.ipify.org": {"ip": "198.51.100.7"}})
    assert providers.detect_own_ip(get) == "198.51.100.7"


def test_reverse_dns_reads_ptr_answer():
    answer = {"Status": 0, "Answer": [{"data": "dns.google.", "type": 12}]}
    get = FakeGet({"dns.google/resolve": answer})
    assert providers.reverse_dns("8.8.8.8", get) == "dns.google"
    assert get.calls[0]["params"]["name"] == "8.8.8.8.in-addr.arpa"


def test_reverse_dns_handles_ipv6_and_misses():
    assert providers.reverse_dns(
        "2001:4860:4860::8888",
        FakeGet({"dns.google/resolve": {"Status": 3}}),
    ) is None
    # The IPv6 query must use the ip6.arpa form.
    get = FakeGet({"dns.google/resolve": {"Status": 3}})
    providers.reverse_dns("2001:4860:4860::8888", get)
    assert get.calls[0]["params"]["name"].endswith(".ip6.arpa")
