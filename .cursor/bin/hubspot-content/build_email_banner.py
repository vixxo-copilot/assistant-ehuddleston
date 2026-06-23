#!/usr/bin/env python3
"""Build email header banner: HVAC photo + Vixxo Gray overlay + logo + Wix Extra Bold headline."""
from __future__ import annotations

import json
import ssl
import sys
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hubspot-campaign-images"))
from hubspot_campaign_images import upload_to_hubspot  # noqa: E402
from hubspot_content import hubspot_request, load_dotenv  # noqa: E402

WIDTH, HEIGHT = 600, 169
GRAY = (62, 69, 67)
OVERLAY_ALPHA = min(255, int(145 * 1.3))  # 30% more opaque than prior banner
WHITE = "#FFFFFF"
HVAC_BG = (
    "https://7718689.fs1.hubspotusercontent-na2.net/hubfs/7718689/"
    "IMAGES/HVAC/Vixxo-Facilities-Management-HVAC-1173822860-600.jpg"
)
LOGO_URL = "https://www.vixxo.com/hubfs/Vixxo%20Logo%20White%20RGB-2.png"
HEADLINE = "Regular facilities management starts with HVAC PM"
EMAIL_ID = "360403230394"
FONT_DIR = Path(__file__).resolve().parents[3] / "_content/staging/hvac-pm-fm-2026/fonts"
EXTRA_BOLD = FONT_DIR / "WixMadeforText-ExtraBold.ttf"
VARIABLE = FONT_DIR / "WixMadeforText.ttf"


def fetch_image(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=60) as resp:
        return Image.open(BytesIO(resp.read())).convert("RGBA")


def load_font(size: int) -> ImageFont.FreeTypeFont:
    if EXTRA_BOLD.is_file():
        return ImageFont.truetype(str(EXTRA_BOLD), size)
    font = ImageFont.truetype(str(VARIABLE), size)
    try:
        font.set_variation_by_axes([800])
    except Exception:
        pass
    return font


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        trial = " ".join(cur + [word])
        if draw.textlength(trial, font=font) <= max_w:
            cur.append(word)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines


def scaled_triangle_height(logo: Image.Image, display_width: int) -> int:
    """Height of the left triangle mark at the scaled logo width."""
    w, h = logo.size
    left = logo.crop((0, 0, max(1, w // 3), h))
    bbox = left.split()[3].getbbox()
    if not bbox:
        return int(h * display_width / w)
    return max(1, int((bbox[3] - bbox[1]) * display_width / w))


def cover_fill(img: Image.Image, width: int, height: int) -> Image.Image:
    """Scale to fill frame while preserving aspect ratio, then center-crop."""
    w, h = img.size
    scale = max(width / w, height / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - width) // 2
    top = (nh - height) // 2
    return img.crop((left, top, left + width, top + height))


def build_banner() -> bytes:
    base = cover_fill(fetch_image(HVAC_BG), WIDTH, HEIGHT)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), GRAY + (OVERLAY_ALPHA,))
    composed = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(composed)

    logo_src = fetch_image(LOGO_URL)
    logo_w = 130
    logo_h = int(logo_src.height * (logo_w / logo_src.width))
    logo = logo_src.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
    logo_y = 16
    composed.paste(logo, (24, logo_y), logo)

    triangle_gap = scaled_triangle_height(logo_src, logo_w)
    font = load_font(20)
    lines = wrap_text(draw, HEADLINE, font, WIDTH - 48)[:2]
    y = logo_y + logo_h + triangle_gap
    for line in lines:
        draw.text((24, y), line, font=font, fill=WHITE)
        y += 24

    buf = BytesIO()
    composed.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def patch_email(banner_url: str) -> dict:
    draft = hubspot_request("GET", f"/marketing/emails/2026-03/{EMAIL_ID}/draft")
    content = draft.get("content") or {}
    widgets = content.get("widgets") or {}
    banner = widgets.get("module-0-1-0") or {}
    body = banner.get("body") or {}
    body.setdefault("img", {})
    body["img"].update(
        {
            "alt": HEADLINE,
            "height": HEIGHT,
            "src": banner_url,
            "width": WIDTH,
        }
    )
    body["path"] = "@hubspot/image_email"
    banner["body"] = body
    widgets["module-0-1-0"] = banner
    content["widgets"] = widgets
    return hubspot_request(
        "PATCH",
        f"/marketing/emails/2026-03/{EMAIL_ID}/draft",
        {"content": content},
    )


def main() -> None:
    load_dotenv()
    banner_bytes = build_banner()
    uploaded = upload_to_hubspot(
        banner_bytes,
        "hvac-pm-fm-2026-email-header-v5.jpg",
        folder_path="/campaign-images/hvac-pm-fm-2026",
        access="PUBLIC_NOT_INDEXABLE",
    )
    url = uploaded.get("url") or uploaded.get("defaultHostingUrl")
    patch_email(str(url))
    print(json.dumps({"bannerUrl": url, "emailId": EMAIL_ID, "height": HEIGHT}, indent=2))


if __name__ == "__main__":
    main()
