from georecon.selftest import selftest, worst_status

from tests.conftest import FakeGet


def routes(**overrides):
    base = {
        "ipwho.is": {"success": True, "ip": "8.8.8.8"},
        "api.ipify.org": {"ip": "203.0.113.9"},
        "dns.google/resolve": {"Status": 0},
        "api.abuseipdb.com": {"data": {"abuseConfidenceScore": 0}},
    }
    base.update(overrides)
    return base


def test_every_provider_is_probed():
    probes = selftest(FakeGet(routes()))
    assert [probe.name.split(" (")[0] for probe in probes] == [
        "geolocation",
        "public IP",
        "DNS over HTTPS",
        "reputation",
    ]
    assert worst_status(probes) == 0


def test_abuseipdb_is_skipped_without_a_key():
    probes = selftest(FakeGet(routes()))
    abuse = probes[-1]
    assert abuse.ok is False
    assert "skipped" in abuse.detail
    assert abuse.latency_ms is None


def test_abuseipdb_is_probed_with_a_key():
    probes = selftest(FakeGet(routes()), abuseipdb_key="secret")
    abuse = probes[-1]
    assert abuse.ok is True
    assert abuse.latency_ms is not None


def test_unreachable_provider_fails_the_selftest():
    probes = selftest(FakeGet(routes(**{"ipwho.is": {"error": "connection refused"}})))
    assert probes[0].ok is False
    assert probes[0].detail
    assert worst_status(probes) == 1


def test_latency_is_measured_for_successes():
    probes = selftest(FakeGet(routes()))
    assert all(probe.latency_ms is not None for probe in probes[:-1])
