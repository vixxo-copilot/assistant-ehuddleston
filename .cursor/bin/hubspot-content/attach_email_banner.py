#!/usr/bin/env python3
"""Build and attach a branded email header banner for a staged campaign."""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw
SCRIPTS_DIR = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "hubspot-content" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hubspot-campaign-images"))

from brand_image import FONT_DIR, TARGET_DPI, cover_fill, fetch_rgba, load_extra_bold, scale  # noqa: E402
from hubspot_campaign_images import upload_to_hubspot  # noqa: E402
from hubspot_content import (  # noqa: E402
    TRADE_HERO_IMAGES,
    hubspot_request,
    load_dotenv,
    plain_html_to_email_module_html,
)

DISPLAY_WIDTH, DISPLAY_HEIGHT = 600, 169
WIDTH, HEIGHT = scale(DISPLAY_WIDTH), scale(DISPLAY_HEIGHT)
GRAY = (62, 69, 67)
OVERLAY_ALPHA = min(255, int(145 * 1.3))
WHITE = "#FFFFFF"
LOGO_URL = "https://www.vixxo.com/hubfs/Vixxo%20Logo%20White%20RGB-2.png"


def fetch_image(url: str) -> Image.Image:
    return fetch_rgba(url)


def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], []
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


def scaled_triangle_height(logo, display_width):
    w, h = logo.size
    left = logo.crop((0, 0, max(1, w // 3), h))
    bbox = left.split()[3].getbbox()
    if not bbox:
        return int(h * display_width / w)
    return max(1, int((bbox[3] - bbox[1]) * display_width / w))


def cover_fill_img(img, width, height):
    return cover_fill(img, width, height)


def build_banner(bg_url: str, headline: str, font_dir: Path | None = None) -> bytes:
    font_root = font_dir or FONT_DIR
    base = cover_fill_img(fetch_image(bg_url), WIDTH, HEIGHT)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), GRAY + (OVERLAY_ALPHA,))
    composed = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(composed)
    logo_src = fetch_image(LOGO_URL)
    logo_w = scale(130)
    logo_h = int(logo_src.height * (logo_w / logo_src.width))
    logo = logo_src.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
    logo_y = scale(16)
    composed.paste(logo, (scale(24), logo_y), logo)
    triangle_gap = scaled_triangle_height(logo_src, logo_w)
    font = load_extra_bold(scale(20), font_root)
    y = logo_y + logo_h + triangle_gap
    for line in wrap_text(draw, headline, font, WIDTH - scale(48))[:2]:
        draw.text((scale(24), y), line, font=font, fill=WHITE)
        y += scale(24)
    buf = BytesIO()
    composed.convert("RGB").save(buf, format="JPEG", quality=95, dpi=(TARGET_DPI, TARGET_DPI))
    return buf.getvalue()


def body_widget(html: str) -> dict:
    return {
        "body": {
            "css_class": "dnd-module",
            "html": html,
            "path": "@hubspot/rich_text",
            "schema_version": 2,
        },
        "child_css": {},
        "css": {},
        "id": "module-0-0-0",
        "label": None,
        "module_id": 1155639,
        "name": "module-0-0-0",
        "order": 2,
        "smart_type": None,
        "styles": {"breakpointStyles": {"default": {}, "mobile": {}}},
        "type": "module",
    }


def body_section() -> dict:
    return {
        "columns": [{"id": "column-0-0", "widgets": ["module-0-0-0"], "width": 12}],
        "id": "section-0",
        "style": {
            "backgroundColor": "",
            "backgroundType": "CONTENT",
            "paddingBottom": "40px",
            "paddingTop": "40px",
            "stack": "LEFT_TO_RIGHT",
        },
    }


def banner_widget(url: str, alt: str) -> dict:
    return {
        "body": {
            "alignment": "center",
            "css_class": "dnd-module",
            "hs_enable_module_padding": False,
            "img": {
                "alt": alt,
                "height": DISPLAY_HEIGHT,
                "src": url,
                "width": DISPLAY_WIDTH,
            },
            "module_id": 1367093,
            "path": "@hubspot/image_email",
            "schema_version": 2,
        },
        "child_css": {},
        "css": {},
        "id": "module-0-1-0",
        "label": None,
        "module_id": 1367093,
        "name": "module-0-1-0",
        "order": 1,
        "smart_type": None,
        "styles": {"breakpointStyles": {"default": {}, "mobile": {}}},
        "type": "module",
    }


def patch_email(
    email_id: str,
    banner_url: str,
    alt: str,
    *,
    html_body: str | None = None,
    subject: str | None = None,
    name: str | None = None,
    preheader: str | None = None,
) -> dict:
    draft = hubspot_request("GET", f"/marketing/emails/2026-03/{email_id}/draft")
    content = deepcopy(draft.get("content") or {})
    widgets = content.get("widgets") or {}
    flex = content.get("flexAreas") or {}
    main = flex.get("main") or {}
    sections = main.get("sections") or []

    if html_body:
        widgets["module-0-0-0"] = body_widget(plain_html_to_email_module_html(html_body))
        if not any(
            "module-0-0-0" in (col.get("widgets") or [])
            for sec in sections
            for col in sec.get("columns") or []
        ):
            sections.append(body_section())

    widgets["module-0-1-0"] = banner_widget(banner_url, alt)
    if not any(
        "module-0-1-0" in (col.get("widgets") or [])
        for sec in sections
        for col in sec.get("columns") or []
    ):
        banner_section = {
            "columns": [{"id": "column-0-1", "widgets": ["module-0-1-0"], "width": 12}],
            "id": "section-banner",
            "style": {
                "backgroundType": "CONTENT",
                "paddingBottom": "0px",
                "paddingTop": "0px",
                "stack": "LEFT_TO_RIGHT",
            },
        }
        sections = [banner_section] + [s for s in sections if s.get("id") != "section-banner"]

    if "preview_text" in widgets and preheader:
        widgets["preview_text"]["body"]["value"] = preheader

    main["sections"] = sections
    flex["main"] = main
    content["widgets"] = widgets
    content["flexAreas"] = flex
    payload: dict = {"content": content}
    if subject:
        payload["subject"] = subject
    if name:
        payload["name"] = name
    return hubspot_request("PATCH", f"/marketing/emails/2026-03/{email_id}/draft", payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email-id", required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--headline", required=True)
    parser.add_argument("--trade", default="plumbing", choices=sorted(TRADE_HERO_IMAGES))
    parser.add_argument("--bg-url")
    parser.add_argument("--filename", help="Upload filename (default: {campaign}-email-header-v2.jpg)")
    parser.add_argument("--html-body-file", help="Restore rich-text body module from HTML file")
    parser.add_argument("--banner-url", help="Skip upload; attach an existing HubSpot CDN banner URL")
    parser.add_argument("--subject")
    parser.add_argument("--name")
    parser.add_argument("--preheader")
    args = parser.parse_args()
    load_dotenv()
    bg = args.bg_url or TRADE_HERO_IMAGES[args.trade]
    slug = args.campaign.replace(" ", "-").lower()
    if args.banner_url:
        url = args.banner_url
    else:
        filename = args.filename or f"{slug}-email-header-v2.jpg"
        banner_bytes = build_banner(bg, args.headline)
        uploaded = upload_to_hubspot(
            banner_bytes,
            filename,
            folder_path=f"/campaign-images/{slug}",
        )
        url = uploaded.get("url") or uploaded.get("defaultHostingUrl")
    html_body = None
    if args.html_body_file:
        html_body = Path(args.html_body_file).read_text(encoding="utf-8")
    patch_email(
        args.email_id,
        str(url),
        args.headline,
        html_body=html_body,
        subject=args.subject,
        name=args.name,
        preheader=args.preheader,
    )
    print(
        json.dumps(
            {
                "bannerUrl": url,
                "emailId": args.email_id,
                "bgUrl": bg,
                "pixelSize": [WIDTH, HEIGHT],
                "dpi": TARGET_DPI,
                "displaySize": [DISPLAY_WIDTH, DISPLAY_HEIGHT],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
