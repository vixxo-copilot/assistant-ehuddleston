#!/usr/bin/env python3
"""Generate 300x300 branded social image — photo bg, gray overlay, Vixxo logo."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from brand_image import FONT_DIR, TARGET_DPI, cover_fill, fetch_rgba, load_extra_bold, scale

DISPLAY_SIZE = 300
SIZE = scale(DISPLAY_SIZE)
GRAY = (62, 69, 67)
OVERLAY_ALPHA = 189
WHITE = "#FFFFFF"
GREEN = "#8E992E"
BG_URL = (
    "https://7718689.fs1.hubspotusercontent-na2.net/hubfs/7718689/"
    "IMAGES/HVAC/Vixxo-Facilities-Management-HVAC-1173822860-600.jpg"
)
DEFAULT_PLUMBING_BG_URL = (
    "https://www.vixxo.com/hubfs/IMAGES/Plumbing/"
    "Vixxo-Facilities-Management-Plumbing-1129117534-1400.jpg"
)
LOGO_URL = "https://www.vixxo.com/hubfs/Vixxo%20Logo%20White%20RGB-2.png"


def fetch_rgba_url(url: str) -> Image.Image:
    return fetch_rgba(url)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], []
    for word in words:
        trial = " ".join(current + [word])
        if draw.textlength(trial, font=font) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def cover_crop(img: Image.Image, size: int) -> Image.Image:
    return cover_fill(img, size, size)


def scaled_triangle_height(logo: Image.Image, display_width: int) -> int:
    w, h = logo.size
    left = logo.crop((0, 0, max(1, w // 3), h))
    bbox = left.split()[3].getbbox()
    if not bbox:
        return int(h * display_width / w)
    return max(1, int((bbox[3] - bbox[1]) * display_width / w))


def render_card(
    headline: str,
    out_path: Path,
    font_dir: Path | None = None,
    bg_url: str | None = None,
) -> None:
    font_root = font_dir or FONT_DIR
    base = cover_crop(fetch_rgba_url(bg_url or BG_URL), SIZE)
    overlay = Image.new("RGBA", (SIZE, SIZE), GRAY + (OVERLAY_ALPHA,))
    composed = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(composed)

    logo_src = fetch_rgba_url(LOGO_URL)
    logo_w = scale(168)
    logo_h = int(logo_src.height * (logo_w / logo_src.width))
    logo = logo_src.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
    logo_y = scale(20)
    composed.paste(logo, (scale(20), logo_y), logo)

    headline_font = load_extra_bold(scale(18), font_root)
    footer_font = load_extra_bold(scale(11), font_root)
    triangle_gap = scaled_triangle_height(logo_src, logo_w)
    y = logo_y + logo_h + triangle_gap
    for line in wrap_text(draw, headline, headline_font, SIZE - scale(40))[:3]:
        draw.text((scale(20), y), line, font=headline_font, fill=WHITE)
        y += scale(21)

    draw.text((scale(20), SIZE - scale(26)), "vixxo.com", font=footer_font, fill=GREEN)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_path, format="PNG", dpi=(TARGET_DPI, TARGET_DPI))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 300x300 Vixxo social image at 150 DPI")
    parser.add_argument("--headline", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--font-dir", type=Path, default=FONT_DIR)
    parser.add_argument("--bg-url", help="Background photo URL (defaults to HVAC stock image)")
    args = parser.parse_args()
    render_card(args.headline, args.output, font_dir=args.font_dir, bg_url=args.bg_url)
    print(args.output)


if __name__ == "__main__":
    main()
