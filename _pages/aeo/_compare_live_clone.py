#!/usr/bin/env python3
"""Compare live published pages vs AEO clone drafts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))

from aeo_revamp import _collect_rich_text  # noqa: E402
from hubspot_pages import (  # noqa: E402
    _find_page_by_slug,
    hubspot_request,
    load_dotenv,
    pages_api,
)

load_dotenv(ROOT)
api = pages_api("site-page")

CLONE_IDS = {
    "beverage-equipment-vixxo": "367618900671",
    "solutions/hvac": "367618900680",
    "industries/retail": "367618900683",
    "about-us/overview": "367619079882",
    "electrical-services": "367618900674",
    "(homepage)": "367618899703",
}


def extract_h1(text: str) -> str | None:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    return re.sub(r"<[^>]+>", "", match.group(1)).strip() if match else None


def extract_hero_imgs(layout: dict) -> list[str]:
    blob = json.dumps(layout)
    return re.findall(r'"src"\s*:\s*"([^"]+)"', blob)[:5]


def analyze(page: dict) -> dict:
    layout = page.get("layoutSections") or {}
    text = _collect_rich_text(layout)
    widget_text = _collect_rich_text(page.get("widgets") or {})
    container_text = _collect_rich_text(page.get("widgetContainers") or {})
    return {
        "id": page.get("id"),
        "slug": page.get("slug"),
        "state": page.get("state") or page.get("currentState"),
        "templatePath": (page.get("templatePath") or "")[-90:],
        "h1": extract_h1(text + widget_text + container_text),
        "layout_text_len": len(text),
        "widget_text_len": len(widget_text + container_text),
        "h2_count": (text + widget_text).lower().count("<h2"),
        "hero_imgs": [u[:120] for u in extract_hero_imgs(layout)[:3]],
        "htmlTitle": page.get("htmlTitle"),
        "body_preview": (text + widget_text)[:250].replace("\n", " "),
    }


def main() -> None:
    results = []
    for slug, clone_id in CLONE_IDS.items():
        live = _find_page_by_slug(slug if slug != "(homepage)" else "", "site-page")
        if slug == "(homepage)":
            data = hubspot_request("GET", f"{api}?limit=50&state__in=PUBLISHED_OR_SCHEDULED")
            for item in data.get("results", []) if isinstance(data, dict) else []:
                if not item.get("slug"):
                    live = item
                    break
        if not live:
            print(f"NO LIVE: {slug}")
            continue
        live_full = hubspot_request("GET", f"{api}/{live['id']}")
        clone_full = hubspot_request("GET", f"{api}/{clone_id}")
        live_a = analyze(live_full)
        clone_a = analyze(clone_full)
        entry = {
            "slug": slug,
            "live": live_a,
            "clone": clone_a,
            "h1_match": live_a["h1"] == clone_a["h1"],
            "template_match": live_a["templatePath"] == clone_a["templatePath"],
            "layout_len_ratio": round(clone_a["layout_text_len"] / max(live_a["layout_text_len"], 1), 2),
        }
        results.append(entry)
        print(f"\n=== {slug} ===")
        print(json.dumps(entry, indent=2))

    out = ROOT / "_pages" / "aeo" / "_live_clone_compare.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
