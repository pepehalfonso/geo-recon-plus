"""Tiny HTTP helper so providers stay testable and time-bounded."""

from __future__ import annotations

from typing import Any, Callable, Optional

import requests

from georecon.errors import NetworkError, ProviderError

USER_AGENT = "georecon-plus/1.0 (+https://github.com/local/geo-recon-plus)"
DEFAULT_TIMEOUT = 12.0

# A callable: get(url, timeout) -> parsed JSON body.
Getter = Callable[..., Any]


def build_getter(user_agent: str = USER_AGENT, timeout: float = DEFAULT_TIMEOUT) -> Getter:
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})

    def get(url: str, *, params: Optional[dict] = None, timeout: float = timeout) -> Any:
        try:
            response = session.get(url, params=params, timeout=timeout)
        except requests.RequestException as exc:
            raise NetworkError(f"could not reach {url}: {exc}") from exc
        if response.status_code >= 500:
            raise ProviderError(f"{url} answered HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(f"{url} did not return JSON") from exc

    return get
