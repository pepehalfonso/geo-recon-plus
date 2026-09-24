import json

import pytest

from georecon.cli import build_parser, main
from tests.conftest import IPWHOIS_OK, FakeGet
import georecon.cli as cli


def test_parser_accepts_target_and_flags():
    args = build_parser().parse_args(["8.8.8.8", "--json", "--no-color"])
    assert args.target == "8.8.8.8"
    assert args.json and args.no_color


def test_missing_target_prints_usage(capsys):
    assert main([]) == 1
    assert "usage:" in capsys.readouterr().err


def test_invalid_target_exits_with_code_2(capsys):
    assert main(["not-an-ip"]) == 2
    assert "not a valid IP address" in capsys.readouterr().err


def test_json_output_is_parseable(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_lookup", lambda args: _result())
    assert main(["8.8.8.8", "--json", "--no-color"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ip"] == "8.8.8.8"
    assert payload["geo"]["city"] == "San Jose"
    assert payload["reputation"]["verdict"] == "clean"


def test_report_output_contains_verdict(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_lookup", lambda args: _result())
    assert main(["8.8.8.8", "--no-color"]) == 0
    out = capsys.readouterr().out
    assert "San Jose" in out
    assert "CLEAN" in out
    assert "Google LLC" in out


def test_local_target_is_treated_as_me(monkeypatch, capsys):
    seen = {}

    def fake_lookup(args):
        seen["me"] = args.me
        return _result()

    monkeypatch.setattr(cli, "_lookup", fake_lookup)
    assert main(["localhost", "--json"]) == 0
    assert seen["me"] is True


def test_network_failure_maps_to_exit_code(monkeypatch, capsys):
    from georecon.errors import NetworkError

    def boom(args):
        raise NetworkError("could not reach https://ipwho.is")

    monkeypatch.setattr(cli, "_lookup", boom)
    assert main(["8.8.8.8"]) == 3
    assert "could not reach" in capsys.readouterr().err


def test_nmap_missing_is_reported(monkeypatch, capsys):
    from georecon.nmap import NmapMissing

    monkeypatch.setattr(cli, "_lookup", lambda args: _result())
    monkeypatch.setattr(cli, "run_nmap", lambda ip, extra: (_ for _ in ()).throw(NmapMissing("nmap is not installed")))
    assert main(["8.8.8.8", "--nmap"]) == 5
    assert "nmap is not installed" in capsys.readouterr().err


def _result():
    from georecon.lookup import Lookup

    return Lookup(get=FakeGet({"ipwho.is": IPWHOIS_OK, "dns.google/resolve": {"Status": 3}}), abuseipdb_key="").run("8.8.8.8")
