"""Shared brand image constants and font loading for campaign assets."""
from __future__ import annotations

import ssl
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFont

SKILL_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = SKILL_DIR / "assets" / "fonts"
EXTRA_BOLD = FONT_DIR / "WixMadeforText-ExtraBold.ttf"

# Render at 150 DPI; HubSpot/email layout uses 72 DPI display dimensions.
TARGET_DPI = 150
DISPLAY_DPI = 72
SCALE = TARGET_DPI / DISPLAY_DPI

# Blog featured hero — 16:9 at 150 DPI (2500×1406 px).
BLOG_DISPLAY_WIDTH = 1200
BLOG_DISPLAY_HEIGHT = 675


def scale(value: float | int) -> int:
    return max(1, round(float(value) * SCALE))


def load_extra_bold(size: int, font_dir: Path | None = None) -> ImageFont.FreeTypeFont:
    """Load Wix Madefor Text Extra Bold — required for branded campaign images."""
    path = (font_dir or FONT_DIR) / "WixMadeforText-ExtraBold.ttf"
    if not path.is_file():
        raise FileNotFoundError(
            f"WixMadeforText-ExtraBold.ttf is required at {path}. "
            "Download from Google Fonts (Wix Madefor Text, ExtraBold 800)."
        )
    return ImageFont.truetype(str(path), size)


def fetch_rgba(source: str | bytes) -> Image.Image:
    if isinstance(source, bytes):
        return Image.open(BytesIO(source)).convert("RGBA")
    req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=60) as resp:
        return Image.open(BytesIO(resp.read())).convert("RGBA")


def cover_fill(img: Image.Image, width: int, height: int) -> Image.Image:
    w, h = img.size
    s = max(width / w, height / h)
    nw, nh = int(w * s), int(h * s)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - width) // 2
    top = (nh - height) // 2
    return img.crop((left, top, left + width, top + height))


def render_photo_at_dpi(
    source: str | bytes,
    *,
    display_width: int = BLOG_DISPLAY_WIDTH,
    display_height: int = BLOG_DISPLAY_HEIGHT,
    image_format: str = "JPEG",
) -> bytes:
    """Cover-crop a photo to 150 DPI pixel dimensions with embedded DPI metadata."""
    width, height = scale(display_width), scale(display_height)
    cropped = cover_fill(fetch_rgba(source), width, height)
    buf = BytesIO()
    if image_format.upper() == "PNG":
        cropped.save(buf, format="PNG", dpi=(TARGET_DPI, TARGET_DPI))
    else:
        cropped.convert("RGB").save(buf, format="JPEG", quality=95, dpi=(TARGET_DPI, TARGET_DPI))
    return buf.getvalue()


def blog_hero_pixel_size() -> tuple[int, int]:
    return scale(BLOG_DISPLAY_WIDTH), scale(BLOG_DISPLAY_HEIGHT)
