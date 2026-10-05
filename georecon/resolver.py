"""Turns user input (IP or hostname) into something lookups can use."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from dataclasses import dataclass

from georecon.errors import InvalidTargetError
from georecon.models import parse_target

# socket.getaddrinfo(host, port, family, type) -> list[tuple, ...]
Resolver = Callable[..., list]

MAX_HOSTNAME_LENGTH = 253


@dataclass(frozen=True)
class Resolution:
    """What the user typed and the address we will actually query."""

    ip: str
    target: str
    resolved_from: str | None = None

    @property
    def is_direct(self) -> bool:
        return self.resolved_from is None


def is_hostname(value: str) -> bool:
    """Cheap syntactic check: looks like a name but not like an IP."""
    candidate = value.strip().rstrip(".")
    if not candidate or len(candidate) > MAX_HOSTNAME_LENGTH:
        return False
    if "://" in candidate or "/" in candidate or " " in candidate:
        return False
    try:
        ipaddress.ip_address(candidate)
        return False
    except ValueError:
        pass
    labels = candidate.split(".")
    if any(not label for label in labels):
        return False
    return all(
        label.isalnum()
        and label[0] != "-"
        and label[-1] != "-"
        and all(ch.isalnum() or ch == "-" for ch in label)
        for label in labels
    )


def resolve(target: str, getaddrinfo: Resolver = socket.getaddrinfo) -> Resolution:
    """Resolve *target* to an IP address.

    Bare IPs are returned as-is. Hostnames are resolved through the system
    resolver, preferring IPv4 so reputation checks (IPv4-only) still work.
    """
    raw = target.strip()
    if not raw:
        raise InvalidTargetError("no target given")

    try:
        address = parse_target(raw)
    except InvalidTargetError:
        address = None

    if address is not None:
        return Resolution(ip=str(address), target=raw)

    if not is_hostname(raw):
        raise InvalidTargetError(f"'{raw}' is not an IP address or a hostname")

    try:
        infos = getaddrinfo(raw, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise InvalidTargetError(f"could not resolve '{raw}': {exc}") from exc
    except OSError as exc:  # pragma: no cover - platform specific
        raise InvalidTargetError(f"could not resolve '{raw}': {exc}") from exc

    candidates = []
    for _family, _type, _proto, _canon, sockaddr in infos:
        try:
            candidate = ipaddress.ip_address(sockaddr[0])
        except ValueError:
            continue
        candidates.append(candidate)

    if not candidates:
        raise InvalidTargetError(f"'{raw}' did not resolve to any address")

    candidates.sort(key=lambda item: (item.version != 4, str(item)))
    return Resolution(ip=str(candidates[0]), target=raw, resolved_from=raw)
