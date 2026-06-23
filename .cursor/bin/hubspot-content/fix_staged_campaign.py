#!/usr/bin/env python3
"""Fix staged HVAC PM campaign: blog editor assets, email banner, featured image."""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hubspot_content import (  # noqa: E402
    blog_editor_url,
    email_editor_url,
    hubspot_request,
    load_config,
    load_dotenv,
    patch_drag_drop_email_draft,
)

EMAIL_ID = "360403230394"
BLOG_ID = "360435433204"
HVAC_BANNER = (
    "https://www.vixxo.com/hubfs/campaign-images/hvac-pm-fm-2026/"
    "hvac-pm-fm-2026-email-header-v5.jpg"
)

MODULE_HTML = (
    '<p style="margin-bottom:10px;"><strong>Regular facilities management starts with HVAC PM</strong></p>'
    '<p style="margin-bottom:10px;">Reactive HVAC work orders drain time and budget — especially '
    "across multi-site portfolios. Structured preventative maintenance is the foundation of regular "
    "facilities management that scales.</p>"
    '<p style="margin-bottom:10px;"><strong>Spend less. Stress less. One work order at a time.</strong></p>'
    '<p style="margin-bottom:10px;">See how VP+ facilities leaders build portfolio-wide PM programs '
    "that reduce downtime and control spend.</p>"
    '<p style="margin-bottom:10px;"><a href="https://www.vixxo.com" target="_blank" '
    'rel="noopener">Learn more</a></p>'
)


def banner_widget() -> dict:
    return {
        "body": {
            "alignment": "center",
            "css_class": "dnd-module",
            "hs_enable_module_padding": False,
            "img": {
                "alt": "Commercial HVAC preventative maintenance for multi-site facilities",
                "height": 169,
                "src": HVAC_BANNER,
                "width": 600,
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


def fix_email() -> dict:
    patch_drag_drop_email_draft(
        EMAIL_ID,
        subject="Regular facilities management starts with HVAC PM",
        name="HVAC PM and Regular FM - Nurture",
        html_body=MODULE_HTML,
        preheader="Portfolio-wide PM reduces downtime and spend",
    )

    draft = hubspot_request("GET", f"/marketing/emails/2026-03/{EMAIL_ID}/draft")
    content = deepcopy(draft.get("content") or {})
    widgets = content.get("widgets") or {}
    flex = content.get("flexAreas") or {}
    main = flex.get("main") or {}
    sections = main.get("sections") or []

    widgets["module-0-1-0"] = banner_widget()
    if not any("module-0-1-0" in (col.get("widgets") or []) for sec in sections for col in sec.get("columns") or []):
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
        if sections:
            body_style = sections[0].get("style") or {}
            body_style["paddingTop"] = "24px"
            sections = [banner_section] + sections
        else:
            sections = [banner_section]

    main["sections"] = sections
    flex["main"] = main
    content["widgets"] = widgets
    content["flexAreas"] = flex

    return hubspot_request(
        "PATCH",
        f"/marketing/emails/2026-03/{EMAIL_ID}/draft",
        {
            "subject": "Regular facilities management starts with HVAC PM",
            "name": "HVAC PM and Regular FM - Nurture",
            "content": content,
        },
    )


def fix_blog_image() -> dict:
    return hubspot_request(
        "PATCH",
        f"/cms/blogs/2026-03/posts/{BLOG_ID}",
        {
            "featuredImage": HVAC_BANNER,
            "featuredImageAltText": "Commercial HVAC preventative maintenance",
            "useFeaturedImage": True,
            "state": "DRAFT",
        },
    )


def main() -> None:
    load_dotenv()
    cfg = load_config()
    portal_id = str(cfg.get("portalId") or "7718689")
    email = fix_email()
    blog = fix_blog_image()
    print(
        json.dumps(
            {
                "emailFixed": True,
                "emailEditorUrl": email_editor_url(portal_id, EMAIL_ID, cfg),
                "emailBannerAdded": True,
                "blogFixed": True,
                "blogEditorUrl": blog_editor_url(portal_id, BLOG_ID, cfg),
                "blogFeaturedImage": blog.get("featuredImage") or HVAC_BANNER,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
