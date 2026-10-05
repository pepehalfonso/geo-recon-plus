import json

import georecon.cli as cli
from georecon.cli import build_parser, main

from tests.conftest import IPWHOIS_OK, FakeGet

GOOD_ROUTES = {
    "ipwho.is/": IPWHOIS_OK,
    "dns.google/resolve": {"Status": 3},
}


def install(monkeypatch, routes):
    fake = FakeGet(routes)
    monkeypatch.setattr(cli, "build_getter", lambda **kwargs: fake)
    return fake


def test_parser_accepts_targets_and_flags():
    args = build_parser().parse_args(["8.8.8.8", "1.1.1.1", "--json", "--no-color"])
    assert args.targets == ["8.8.8.8", "1.1.1.1"]
    assert args.json and args.no_color


def test_missing_target_prints_usage(capsys):
    assert main([]) == 1
    assert "usage:" in capsys.readouterr().err


def test_invalid_target_exits_with_code_2(capsys):
    assert main(["not-an-ip"]) == 2
    assert "not-an-ip" in capsys.readouterr().err


def test_json_output_is_parseable(monkeypatch, capsys):
    install(monkeypatch, GOOD_ROUTES)
    assert main(["8.8.8.8", "--json", "--no-color"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ip"] == "8.8.8.8"
    assert payload["schema_version"] == 2
    assert payload["geo"]["city"] == "San Jose"
    assert payload["reputation"]["verdict"] == "clean"


def test_report_output_contains_verdict(monkeypatch, capsys):
    install(monkeypatch, GOOD_ROUTES)
    assert main(["8.8.8.8", "--no-color"]) == 0
    out = capsys.readouterr().out
    assert "San Jose" in out
    assert "CLEAN" in out
    assert "Google LLC" in out
    assert "openstreetmap.org" in out


def test_local_target_is_treated_as_me(monkeypatch, capsys):
    fake = install(
        monkeypatch,
        {
            "ipwho.is/200.45.10.7": IPWHOIS_OK,
            "ipwho.is": {"ip": "200.45.10.7", "success": True},
            "dns.google/resolve": {"Status": 3},
        },
    )
    assert main(["localhost", "--json"]) == 0
    assert "https://ipwho.is/" in fake.urls


def test_network_failure_maps_to_exit_code(monkeypatch, capsys):
    install(monkeypatch, {"": {"error": "network unreachable"}})
    assert main(["8.8.8.8"]) == 3
    assert "network unreachable" in capsys.readouterr().err


def test_nmap_missing_is_reported(monkeypatch, capsys):
    from georecon.nmap import NmapMissing

    install(monkeypatch, GOOD_ROUTES)

    def boom(ip, extra):
        raise NmapMissing("nmap is not installed")

    monkeypatch.setattr(cli, "run_nmap", boom)
    assert main(["8.8.8.8", "--nmap"]) == 5
    assert "nmap is not installed" in capsys.readouterr().err


def test_multiple_targets_produce_a_batch_document(monkeypatch, capsys):
    install(monkeypatch, GOOD_ROUTES)
    code = main(["8.8.8.8", "1.1.1.1", "nope", "--json", "--no-color"])
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["results"]) == 2
    assert payload["errors"][0]["target"] == "nope"
    assert payload["errors"][0]["exit_code"] == 2


def test_targets_can_come_from_a_file(monkeypatch, capsys, tmp_path):
    handle = tmp_path / "targets.txt"
    handle.write_text("# comentario\n8.8.8.8\n\n1.1.1.1  # con nota\n", encoding="utf-8")
    install(monkeypatch, GOOD_ROUTES)
    assert main(["--file", str(handle), "--json", "--no-color"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["ip"] for item in payload["results"]] == ["8.8.8.8", "1.1.1.1"]


def test_missing_file_is_reported(capsys):
    assert main(["--file", "does-not-exist.txt"]) == 1
    assert "cannot read" in capsys.readouterr().err


def test_map_flag_prints_only_the_link(monkeypatch, capsys):
    install(monkeypatch, GOOD_ROUTES)
    assert main(["8.8.8.8", "--map", "--no-color"]) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("https://www.openstreetmap.org/")
    assert "San Jose" not in out


def test_map_without_coordinates_is_reported(monkeypatch, capsys):
    install(
        monkeypatch,
        {
            "ipwho.is/8.8.8.8": {"success": True, "ip": "8.8.8.8"},
            "dns.google/resolve": {"Status": 3},
        },
    )
    assert main(["8.8.8.8", "--map", "--no-color"]) == 0
    assert "no coordinates to map" in capsys.readouterr().out


def test_selftest_passes_when_providers_answer(monkeypatch, capsys):
    install(
        monkeypatch,
        {
            "ipwho.is": {"success": True, "ip": "8.8.8.8"},
            "api.ipify.org": {"ip": "203.0.113.9"},
            "dns.google/resolve": {"Status": 0},
        },
    )
    assert main(["--selftest", "--no-color"]) == 0
    out = capsys.readouterr().out
    assert "OK" in out
    assert "SKIP" in out
    assert "AbuseIPDB" in out


def test_selftest_fails_when_a_provider_is_down(monkeypatch, capsys):
    install(
        monkeypatch,
        {
            "ipwho.is": {"error": "connection refused"},
            "api.ipify.org": {"ip": "203.0.113.9"},
            "dns.google/resolve": {"Status": 0},
        },
    )
    assert main(["--selftest", "--no-color"]) == 1
    assert "FAIL" in capsys.readouterr().out
