"""Command line interface for GeoRecon+."""

from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from collections.abc import Sequence

from georecon import __version__
from georecon.errors import GeoReconError
from georecon.http import Getter, build_getter
from georecon.lookup import ABUSEIPDB_ENV, Lookup
from georecon.models import LookupResult
from georecon.nmap import run_nmap
from georecon.output import (
    Palette,
    colors_enabled,
    harden_stream,
    map_url,
    render_json,
    render_report,
    render_separator,
)
from georecon.selftest import Probe, worst_status
from georecon.selftest import selftest as run_probes

SELF_TARGETS = {"me", "myip", "self", "localhost", "127.0.0.1"}

EXIT_OK = 0
EXIT_ERROR = 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="georecon",
        description="Fast IP geolocation and reputation lookups.",
        epilog=(
            "examples:\n"
            "  georecon 8.8.8.8\n"
            "  georecon example.com 1.1.1.1\n"
            "  georecon --file targets.txt --json\n"
            "  georecon me --map\n"
            "  georecon --selftest\n"
            "\n"
            "Set ABUSEIPDB_KEY to enable real AbuseIPDB reputation data."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "targets",
        nargs="*",
        metavar="TARGET",
        help="IP addresses or hostnames to look up, or 'me' for your own public IP",
    )
    parser.add_argument("-m", "--me", action="store_true", help="look up your own public IP")
    parser.add_argument(
        "-f",
        "--file",
        metavar="PATH",
        help="read targets from a file, one per line ('-' for stdin); '#' starts a comment",
    )
    parser.add_argument("-j", "--json", action="store_true", help="emit machine readable JSON")
    parser.add_argument(
        "--no-reputation",
        action="store_true",
        help="skip reputation checks (geolocation only)",
    )
    parser.add_argument(
        "-n",
        "--nmap",
        action="store_true",
        help="also run an nmap service scan (requires nmap installed)",
    )
    parser.add_argument(
        "--nmap-args",
        nargs=argparse.REMAINDER,
        metavar="ARG",
        help="arguments passed straight to nmap after --nmap-args",
    )
    parser.add_argument("--map", action="store_true", help="print the OpenStreetMap link only")
    parser.add_argument(
        "--open-map",
        action="store_true",
        help="print the OpenStreetMap link and open it in your browser",
    )
    parser.add_argument("--selftest", action="store_true", help="check that every provider answers")
    parser.add_argument("--no-color", action="store_true", help="disable coloured output")
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        metavar="SECONDS",
        help="per request timeout (default: 12)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        metavar="N",
        help="retries per request on network failures (default: 2)",
    )
    parser.add_argument("--version", action="version", version=f"georecon {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    harden_stream(sys.stdout)
    harden_stream(sys.stderr)
    parser = build_parser()
    args = parser.parse_args(argv)

    palette = Palette(colors_enabled() and not args.no_color)

    try:
        getter = build_getter(timeout=args.timeout, retries=max(0, args.retries))

        if args.selftest:
            return _selftest(getter, palette)

        targets = _collect_targets(args)
        if not targets:
            parser.print_help(sys.stderr)
            return EXIT_ERROR

        return _lookup_all(targets, args, getter, palette)
    except GeoReconError as exc:
        print(f"georecon: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:  # pragma: no cover
        print("georecon: interrupted", file=sys.stderr)
        return 130


def _collect_targets(args: argparse.Namespace) -> list[str]:
    targets = [str(target) for target in args.targets]
    if args.me:
        targets.insert(0, "me")
    if args.file:
        targets.extend(_read_targets(args.file))
    return targets


def _read_targets(path: str) -> list[str]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(path, encoding="utf-8") as handle:
                raw = handle.read()
        except OSError as exc:
            raise GeoReconError(f"cannot read {path}: {exc.strerror or exc}") from exc
    collected = []
    for line in raw.splitlines():
        value = line.split("#", 1)[0].strip()
        if value:
            collected.append(value)
    return collected


def _lookup_all(
    targets: list[str],
    args: argparse.Namespace,
    getter: Getter,
    palette: Palette,
) -> int:
    lookup = Lookup(get=getter, with_reputation=not args.no_reputation)
    results: list[LookupResult] = []
    failures: list[dict] = []
    exit_codes: list[int] = []

    for index, target in enumerate(targets):
        if index and not args.json:
            print(render_separator(index + 1, len(targets)))
        try:
            result = lookup.run_own() if target.lower() in SELF_TARGETS else lookup.run(target)
        except GeoReconError as exc:
            print(f"georecon: {target}: {exc}", file=sys.stderr)
            failures.append({"target": target, "error": str(exc), "exit_code": exc.exit_code})
            exit_codes.append(exc.exit_code)
            continue

        results.append(result)

        if args.map or args.open_map:
            link = map_url(result)
            if link:
                print(link)
                if args.open_map:
                    webbrowser.open(link)
            elif not args.json:
                print(f"georecon: {target}: no coordinates to map")
            continue

        if args.json:
            continue

        print(render_report(result, palette, sys.stdout), end="")
        if args.nmap:
            print(palette("\n  nmap", "bold", "cyan"))
            exit_codes.append(run_nmap(result.ip, args.nmap_args))

    if args.json:
        _print_json(results, failures, len(targets))

    return max(exit_codes, default=EXIT_OK)


def _print_json(results: list[LookupResult], failures: list[dict], total: int) -> None:
    if total == 1:
        if results:
            print(render_json(results[0]))
        else:
            print(json.dumps(failures[0], indent=2, ensure_ascii=True))
        return
    print(
        json.dumps(
            {
                "results": [item.to_dict() for item in results],
                "errors": failures,
            },
            indent=2,
            ensure_ascii=True,
        )
    )


def _selftest(getter: Getter, palette: Palette) -> int:
    key = os.environ.get(ABUSEIPDB_ENV, "").strip() or None
    probes: list[Probe] = run_probes(getter, abuseipdb_key=key)
    print("")
    for probe in probes:
        if not probe.ok and "skipped" in probe.detail:
            status = palette("SKIP", "yellow")
        elif probe.ok:
            status = palette("OK  ", "green")
        else:
            status = palette("FAIL", "red")
        latency = f"{probe.latency_ms} ms" if probe.latency_ms is not None else "-"
        print(f"  {status}  {probe.name:<28} {latency:>8}   {probe.detail}")
    print("")
    return worst_status(probes)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
