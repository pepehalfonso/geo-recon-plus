import pytest
import requests
from georecon.errors import NetworkError, ProviderError
from georecon.http import build_getter


class FakeResponse:
    def __init__(self, status=200, payload=None, invalid_json=False):
        self.status_code = status
        self._payload = payload if payload is not None else {"ok": True}
        self._invalid_json = invalid_json

    def json(self):
        if self._invalid_json:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    """Returns or raises each queued outcome in order, then repeats the last."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def getter_for(outcomes, **kwargs):
    session = FakeSession(outcomes)
    return build_getter(session=session, sleep=lambda _: None, **kwargs), session


def test_returns_json_on_success():
    get, session = getter_for([FakeResponse(payload={"ip": "8.8.8.8"})])
    assert get("https://example.test") == {"ip": "8.8.8.8"}
    assert session.calls == 1


def test_retries_connection_errors_then_succeeds():
    get, session = getter_for([requests.ConnectionError("boom"), FakeResponse()])
    assert get("https://example.test") == {"ok": True}
    assert session.calls == 2


def test_gives_up_after_the_retry_budget():
    get, session = getter_for([requests.ConnectionError("boom")], retries=2)
    with pytest.raises(NetworkError, match="could not reach"):
        get("https://example.test")
    assert session.calls == 3


def test_retries_server_errors():
    get, session = getter_for([FakeResponse(status=503), FakeResponse(payload={"ok": 1})])
    assert get("https://example.test") == {"ok": 1}
    assert session.calls == 2


def test_client_errors_are_not_retried():
    get, session = getter_for([FakeResponse(status=429)])
    with pytest.raises(ProviderError, match="HTTP 429"):
        get("https://example.test")
    assert session.calls == 1


def test_non_json_body_is_reported():
    get, _ = getter_for([FakeResponse(invalid_json=True)])
    with pytest.raises(ProviderError, match="did not return JSON"):
        get("https://example.test")


def test_extra_headers_are_merged_over_defaults():
    captured = {}

    class Recorder(FakeSession):
        def get(self, *args, **kwargs):
            captured.update(kwargs["headers"])
            return FakeResponse()

    session = Recorder([FakeResponse()])
    get = build_getter(session=session, sleep=lambda _: None)
    get("https://example.test", headers={"Key": "secret"})
    assert captured["Key"] == "secret"
    assert captured["Accept"] == "application/json"
    assert "georecon-plus" in captured["User-Agent"]
