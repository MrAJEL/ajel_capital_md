"""Generate PWA icons (180, 192, 512 px) for this app.

Usage:  python3 generar_iconos.py [LETTERS] [BG_HEX] [FG_HEX]
Example: python3 generar_iconos.py DT 0f172a 22c55e

Requires Pillow (pip install pillow). Icons are written to ./icons next to this script.
Square, full-bleed background (iOS rounds corners itself; also safe as "maskable").
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZES = (180, 192, 512)
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def load_font(size: int) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def make_icon(size: int, text: str, bg: tuple[int, int, int], fg: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)
    # Accent ring inside the maskable safe zone (inner 80%).
    margin = int(size * 0.16)
    draw.ellipse((margin, margin, size - margin, size - margin), outline=fg, width=max(2, size // 24))
    font = load_font(int(size * (0.34 if len(text) > 1 else 0.42)))
    draw.text((size / 2, size / 2), text, fill=fg, font=font, anchor="mm")
    return img


def main() -> None:
    text = sys.argv[1] if len(sys.argv) > 1 else "P"
    bg = hex_to_rgb(sys.argv[2] if len(sys.argv) > 2 else "0f172a")
    fg = hex_to_rgb(sys.argv[3] if len(sys.argv) > 3 else "22c55e")
    out = Path(__file__).resolve().parent / "icons"
    out.mkdir(exist_ok=True)
    for size in SIZES:
        path = out / f"icon-{size}.png"
        make_icon(size, text, bg, fg).save(path, optimize=True)
        print(f"wrote {path} ({size}x{size})")


if __name__ == "__main__":
    main()
