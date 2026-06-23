#!/usr/bin/env python3
"""Generate 300x300 branded social image — photo bg, gray overlay, Vixxo logo."""
from __future__ import annotations

import argparse
import ssl
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 300
GRAY = (62, 69, 67)
OVERLAY_ALPHA = 189
WHITE = "#FFFFFF"
GREEN = "#8E992E"
BG_URL = (
    "https://7718689.fs1.hubspotusercontent-na2.net/hubfs/7718689/"
    "IMAGES/HVAC/Vixxo-Facilities-Management-HVAC-1173822860-600.jpg"
)
LOGO_URL = "https://www.vixxo.com/hubfs/Vixxo%20Logo%20White%20RGB-2.png"


def fetch_rgba(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=60) as resp:
        return Image.open(BytesIO(resp.read())).convert("RGBA")


def load_font(font_dir: Path, size: int) -> ImageFont.FreeTypeFont:
    extra_bold = font_dir / "WixMadeforText-ExtraBold.ttf"
    variable = font_dir / "WixMadeforText.ttf"
    if extra_bold.is_file():
        return ImageFont.truetype(str(extra_bold), size)
    font = ImageFont.truetype(str(variable), size)
    try:
        font.set_variation_by_axes([800])
    except Exception:
        pass
    return font


def wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
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
    w, h = img.size
    scale = max(size / w, size / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - size) // 2
    top = (nh - size) // 2
    return img.crop((left, top, left + size, top + size))


def scaled_triangle_height(logo: Image.Image, display_width: int) -> int:
    w, h = logo.size
    left = logo.crop((0, 0, max(1, w // 3), h))
    bbox = left.split()[3].getbbox()
    if not bbox:
        return int(h * display_width / w)
    return max(1, int((bbox[3] - bbox[1]) * display_width / w))


def render_card(headline: str, out_path: Path, font_dir: Path) -> None:
    base = cover_crop(fetch_rgba(BG_URL), SIZE)
    overlay = Image.new("RGBA", (SIZE, SIZE), GRAY + (OVERLAY_ALPHA,))
    composed = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(composed)

    logo_src = fetch_rgba(LOGO_URL)
    logo_w = 168
    logo_h = int(logo_src.height * (logo_w / logo_src.width))
    logo = logo_src.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
    logo_y = 20
    composed.paste(logo, (20, logo_y), logo)

    headline_font = load_font(font_dir, 18)
    footer_font = load_font(font_dir, 11)
    triangle_gap = scaled_triangle_height(logo_src, logo_w)
    y = logo_y + logo_h + triangle_gap
    for line in wrap_text(draw, headline, headline_font, SIZE - 40)[:3]:
        draw.text((20, y), line, font=headline_font, fill=WHITE)
        y += 21

    draw.text((20, SIZE - 26), "vixxo.com", font=footer_font, fill=GREEN)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(out_path, format="PNG", dpi=(72, 72))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 300x300 Vixxo social image")
    parser.add_argument("--headline", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--font-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets" / "fonts",
    )
    args = parser.parse_args()
    render_card(args.headline, args.output, args.font_dir)
    print(args.output)


if __name__ == "__main__":
    main()
