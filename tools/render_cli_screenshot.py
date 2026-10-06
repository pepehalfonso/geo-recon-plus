"""Render a GeoRecon+ CLI session as a terminal-style PNG for the docs.

Usage:
    python tools/render_cli_screenshot.py
    python tools/render_cli_screenshot.py --cmd "georecon 1.1.1.1"
    python tools/render_cli_screenshot.py --text-file out.txt
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots" / "cli.png"

BG = (13, 17, 23)
BORDER = (48, 54, 61)
TEXT = (201, 209, 217)
LABEL = (125, 133, 144)
GREEN = (63, 185, 80)
BLUE = (88, 166, 255)
DIM = (110, 118, 129)
DOTS = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]

PAIR = re.compile(r"^(.*?\S\s\s+)(\S.*)$")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "consolab.ttf" if bold else "consola.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def _parse(line: str) -> tuple[str, str, str] | None:
    """Split a `    Label   value` line into (indent, label, value)."""
    match = PAIR.match(line)
    if not match:
        return None
    head, value = match.groups()
    stripped = head.rstrip()
    return head[: len(head) - len(stripped.lstrip())], stripped.lstrip(), value.strip()


def _value_colour(value: str) -> tuple[int, int, int]:
    if value == "CLEAN":
        return GREEN
    if value.startswith("["):
        return BLUE
    return TEXT


def render(body: str, command: str, dest: Path) -> None:
    prompt = f"PS C:\\geo-recon-plus> {command}"
    lines = ["", prompt, *body.splitlines()]
    size, lh, pad = 17, 26, 24
    font, bold = _font(size), _font(size, bold=True)

    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    advance = probe.textlength("M", font=font)
    parsed = [None if line in ("", prompt) else _parse(line) for line in lines]
    label_col = max(
        (len(indent + label) for p in parsed if p for indent, label, _ in [p]),
        default=0,
    )
    label_col += 2

    cols = max(len(line) for line in lines)
    width = max(int(cols * advance) + pad * 2, 780)
    height = pad * 2 + 44 + lh * len(lines)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=10, outline=BORDER, width=1)
    for i, colour in enumerate(DOTS):
        draw.ellipse([18 + i * 22, 17, 30 + i * 22, 29], fill=colour)
    draw.text((width // 2 - 46, 15), "PowerShell", font=_font(13), fill=DIM)
    draw.line([0, 44, width, 44], fill=BORDER, width=1)

    y = 44 + pad
    for line, item in zip(lines, parsed, strict=True):
        if line == prompt:
            draw.text((pad, y), line, font=bold, fill=GREEN)
        elif line and item:
            indent, label, value = item
            draw.text((pad, y), indent + label, font=font, fill=LABEL)
            draw.text(
                (pad + int(label_col * advance), y),
                value,
                font=font,
                fill=_value_colour(value),
            )
        elif line:
            colour = DIM if line.lstrip().startswith("-") else TEXT
            draw.text((pad, y), line, font=font, fill=colour)
        y += lh

    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    print(f"wrote {dest} ({img.width}x{img.height})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cmd", default="georecon 8.8.8.8")
    parser.add_argument("--text-file", type=Path)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    if args.text_file:
        body = args.text_file.read_text(encoding="utf-8")
    else:
        body = subprocess.run(
            args.cmd, shell=True, capture_output=True, text=True, cwd=ROOT
        ).stdout
        if not body:
            print("command produced no output", file=sys.stderr)
            return 1

    render(body.strip("\n"), args.cmd, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
