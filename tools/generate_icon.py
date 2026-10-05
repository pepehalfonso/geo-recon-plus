"""Generate the GeoRecon+ launcher icons (run: python tools/generate_icon.py)."""

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 4096
CENTER = SIZE // 2
RADIUS = 1150
TEAL = (0, 179, 164, 255)
MINT = (160, 255, 240, 255)
BACKGROUND = (11, 31, 28, 255)


def draw_globe(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, width: int) -> None:
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        outline=TEAL,
        width=width,
    )
    for factor in (0.42, 0.78):
        inner = int(radius * factor)
        draw.ellipse(
            (cx - inner, cy - radius, cx + inner, cy + radius),
            outline=TEAL,
            width=width,
        )
    chord = int(radius * 0.866)
    for offset in (-radius // 2, radius // 2):
        draw.line(
            (cx - chord, cy + offset, cx + chord, cy + offset),
            fill=TEAL,
            width=width,
        )
    draw.ellipse(
        (cx - radius // 2, cy - radius // 2, cx + radius // 2, cy + radius // 2),
        outline=MINT,
        width=width,
    )
    dot = int(radius * 0.16)
    draw.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=MINT)


def draw_crosshair(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, width: int) -> None:
    gap = radius + width * 2
    length = radius // 4
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        draw.line(
            (
                cx + dx * gap,
                cy + dy * gap,
                cx + dx * (gap + length),
                cy + dy * (gap + length),
            ),
            fill=TEAL,
            width=width,
        )


def build_foreground() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    width = 74
    draw_globe(draw, CENTER, CENTER, RADIUS, width)
    draw_crosshair(draw, CENTER, CENTER, RADIUS, width)
    return image


def rounded_background() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, SIZE, SIZE), radius=760, fill=BACKGROUND)
    return image


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "mobile" / "assets" / "icon"
    target.mkdir(parents=True, exist_ok=True)

    foreground = build_foreground()
    foreground.resize((1024, 1024), Image.LANCZOS).save(target / "foreground.png")

    composite = rounded_background()
    scale = int(SIZE * 0.92)
    overlay = build_foreground().resize((scale, scale), Image.LANCZOS)
    composite.alpha_composite(overlay, ((SIZE - scale) // 2, (SIZE - scale) // 2))
    composite.resize((1024, 1024), Image.LANCZOS).save(target / "icon.png")

    print(f"icons written to {target}")


if __name__ == "__main__":
    main()
