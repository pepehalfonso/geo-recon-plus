"""Terminal rendering: colours, the report and the JSON emitters."""

from __future__ import annotations

import json
import os
import sys
from typing import TextIO

from georecon.models import LookupResult

ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
}

VERDICT_STYLE = {
    "clean": "green",
    "suspicious": "yellow",
    "malicious": "red",
    "unknown": "dim",
}

VERDICT_LABEL = {
    "clean": "CLEAN",
    "suspicious": "SUSPICIOUS",
    "malicious": "MALICIOUS",
    "unknown": "UNKNOWN",
}


def colors_enabled(stream: TextIO = sys.stdout) -> bool:
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def harden_stream(stream: TextIO) -> None:
    """Never let an exotic glyph crash the report on a legacy console."""
    try:
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError, OSError):
        pass


def encodable(text: str, stream: TextIO) -> bool:
    """True when *text* survives a round-trip through the stream encoding."""
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return False
    return True


class Palette:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def __call__(self, text: str, *styles: str) -> str:
        if not self.enabled or not styles:
            return text
        prefix = "".join(ANSI[s] for s in styles if s in ANSI)
        return f"{prefix}{text}{ANSI['reset']}" if prefix else text


def render_report(result: LookupResult, palette: Palette, stream: TextIO = sys.stdout) -> str:
    label = VERDICT_LABEL.get(result.reputation.verdict, "UNKNOWN")
    verdict_color = VERDICT_STYLE.get(result.reputation.verdict, "dim")

    lines: list[str] = []
    lines.append("")
    header = palette(f"  {result.ip}  ", "bold", "blue")
    lines.append(header)
    lines.append("")

    if result.is_private:
        lines.append(palette("  Non-public address", "bold"))
        for note in result.reputation.notes:
            lines.append(f"    {note}")
        lines.append("")
        lines.append(
            f"  Verdict: {palette(label, 'bold', verdict_color)}"
        )
        lines.append("")
        return "\n".join(lines)

    geo = result.geo
    conn = result.connection
    flag = geo.flag or ""
    if flag and not encodable(flag, stream):
        flag = ""

    lines.append(palette("  Geolocation", "bold", "cyan") + palette(f"   [{result.provider}]", "dim"))
    rows = [
        ("Country", f"{flag} {geo.country or 'unknown'}".strip()),
        ("Region", geo.region or "unknown"),
        ("City", geo.city or "unknown"),
        ("Timezone", geo.timezone or "unknown"),
        ("Coordinates", _coordinates(geo.latitude, geo.longitude)),
        ("ASN", conn.asn_label),
        ("Organization", conn.org or "unknown"),
        ("ISP", conn.isp or "unknown"),
        ("Domain", conn.domain or "unknown"),
        ("Reverse DNS", result.hostname or "none"),
    ]
    lines.extend(_rows(rows, palette))

    lines.append("")
    lines.append(palette("  Reputation", "bold", "cyan") + palette(f"   [{result.reputation.source}]", "dim"))
    rep_rows = [
        ("Verdict", palette(label, "bold", verdict_color)),
        ("Abuse score", _score(result.reputation.score)),
        ("Reports", str(result.reputation.reports) if result.reputation.reports is not None else "n/a"),
        ("Last reported", result.reputation.last_reported or "n/a"),
    ]
    lines.extend(_rows(rep_rows, palette))
    for note in result.reputation.notes:
        lines.append(f"    {palette('-', 'dim')} {note}")

    if result.warnings:
        lines.append("")
        for warning in result.warnings:
            lines.append(palette(f"  ! {warning}", "yellow"))

    lines.append("")
    return "\n".join(lines)


def render_json(result: LookupResult) -> str:
    # ASCII-safe: survives any console code page and any pipe encoding.
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=True)


def _coordinates(latitude, longitude) -> str:
    if latitude is None or longitude is None:
        return "unknown"
    return f"{latitude:.4f}, {longitude:.4f}"


def _score(score) -> str:
    if score is None:
        return "n/a"
    return f"{score}/100"


def _rows(rows, palette: Palette) -> list[str]:
    width = max(len(name) for name, _ in rows)
    return [f"    {palette(name.ljust(width), 'dim')}  {value}" for name, value in rows]

