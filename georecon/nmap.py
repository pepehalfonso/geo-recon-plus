"""Optional nmap integration. Never installs anything behind your back."""

from __future__ import annotations

import shutil
import subprocess
from typing import Optional, Sequence

from georecon.errors import GeoReconError

DEFAULT_ARGS: tuple[str, ...] = ("-Pn", "-sV", "--traceroute")


class NmapMissing(GeoReconError):
    exit_code = 5


def nmap_available() -> bool:
    return shutil.which("nmap") is not None


def run_nmap(ip: str, extra_args: Optional[Sequence[str]] = None) -> int:
    """Run nmap against *ip* and stream its output to the terminal."""
    if not nmap_available():
        raise NmapMissing(
            "nmap is not installed (or not on PATH). "
            "Install it yourself, e.g. 'sudo apt install nmap' or "
            "'choco install nmap', then retry."
        )
    args = list(DEFAULT_ARGS if not extra_args else extra_args)
    command = ["nmap", *args, ip]
    try:
        completed = subprocess.run(command, check=False)
    except OSError as exc:  # pragma: no cover - platform specific
        raise GeoReconError(f"could not run nmap: {exc}") from exc
    return completed.returncode
