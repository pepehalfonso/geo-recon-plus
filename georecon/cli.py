"""Command line interface for GeoRecon+."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from georecon import __version__
from georecon.errors import GeoReconError
from georecon.http import build_getter
from georecon.lookup import Lookup
from georecon.models import LookupResult
from georecon.nmap import run_nmap
from georecon.output import (
    Palette,
    colors_enabled,
    harden_stream,
    render_json,
    render_report,
)

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
            "  georecon me --json\n"
            "  georecon 203.0.113.10 --nmap\n"
            "\n"
            "Set ABUSEIPDB_KEY to enable real AbuseIPDB reputation data."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="IP address to look up, or 'me' for your own public IP",
    )
    parser.add_argument("-m", "--me", action="store_true", help="look up your own public IP")
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
    parser.add_argument("--no-color", action="store_true", help="disable coloured output")
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        metavar="SECONDS",
        help="per request timeout (default: 12)",
    )
    parser.add_argument("--version", action="version", version=f"georecon {__version__}")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    harden_stream(sys.stdout)
    harden_stream(sys.stderr)
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.target and not args.me:
        parser.print_help(sys.stderr)
        return EXIT_ERROR

    if args.target and args.target.lower() in SELF_TARGETS:
        args.me = True

    palette = Palette(colors_enabled() and not args.no_color)

    try:
        result = _lookup(args)
        if args.json:
            print(render_json(result))
        else:
            print(render_report(result, palette, sys.stdout), end="")

        if args.nmap:
            print(palette("\n  nmap", "bold", "cyan"))
            return run_nmap(result.ip, args.nmap_args)
        return EXIT_OK
    except GeoReconError as exc:
        print(f"georecon: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:  # pragma: no cover
        print("georecon: interrupted", file=sys.stderr)
        return 130


def _lookup(args: argparse.Namespace) -> LookupResult:
    lookup = Lookup(get=build_getter(timeout=args.timeout), with_reputation=not args.no_reputation)
    return lookup.run_own() if args.me else lookup.run(args.target)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
