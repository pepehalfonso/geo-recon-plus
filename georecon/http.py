"""Tiny HTTP helper so providers stay testable, time-bounded and resilient."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

from georecon.errors import NetworkError, ProviderError

USER_AGENT = "georecon-plus/1.1 (+https://github.com/pepehalfonso/geo-recon-plus)"
DEFAULT_TIMEOUT = 12.0
DEFAULT_RETRIES = 2
RETRY_BACKOFF = 0.4

# A callable: get(url, ...) -> parsed JSON body.
Getter = Callable[..., Any]


def build_getter(
    user_agent: str = USER_AGENT,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    session: Any | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Getter:
    """Build a JSON getter that retries transient failures.

    Retries cover connection errors, timeouts and 5xx answers. Client errors
    (4xx) are surfaced immediately: retrying them will not help.
    """
    http = session if session is not None else requests.Session()
    base_headers = {"User-Agent": user_agent, "Accept": "application/json"}

    def get(
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float = timeout,
    ) -> Any:
        merged = dict(base_headers)
        if headers:
            merged.update(headers)

        last_error: Exception = NetworkError(f"could not reach {url}")
        for attempt in range(retries + 1):
            if attempt:
                sleep(RETRY_BACKOFF * attempt)
            try:
                response = http.get(url, params=params, headers=merged, timeout=timeout)
            except requests.RequestException as exc:
                last_error = NetworkError(f"could not reach {url}: {exc}")
                continue
            if response.status_code >= 500:
                last_error = ProviderError(f"{url} answered HTTP {response.status_code}")
                continue
            if response.status_code >= 400:
                raise ProviderError(f"{url} answered HTTP {response.status_code}")
            try:
                return response.json()
            except ValueError as exc:
                raise ProviderError(f"{url} did not return JSON") from exc
        raise last_error

    return get
