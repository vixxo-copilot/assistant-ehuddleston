#!/usr/bin/env python3
"""Restore Beverage Equipment clone layout from live, re-apply AEO in body only."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))

from aeo_revamp import (  # noqa: E402
    build_revamp_package,
    patch_layout_sections,
    verify_clone_content,
    _collect_rich_text,
    _is_hero_rich_text,
)
from hubspot_pages import hubspot_request, load_dotenv, pages_api  # noqa: E402
from run_aeo_revamp_batch import list_pages_fn_factory  # noqa: E402

LIVE_ID = "360125976278"
CLONE_ID = "367618900671"
LIVE_HERO = (
    '<h1 style="color: #fff; text-align: center;">Beverage Equipment</h1>\n'
    '<p style="color: #fff; text-align: center;">Reliable beverage equipment '
    "installation, repair, and maintenance for any business.</p>"
)


def hero_rich_text(layout: dict) -> str | None:
    from aeo_revamp import _iter_rich_text_targets

    for entry in _iter_rich_text_targets(layout):
        text = str(entry["obj"].get("rich_text") or "")
        if _is_hero_rich_text(text, entry.get("module_label") or ""):
            return text
    return None


def main() -> int:
    load_dotenv(ROOT)
    api = pages_api("site-page")

    live = hubspot_request("GET", f"{api}/{LIVE_ID}")
    clone = hubspot_request("GET", f"{api}/{CLONE_ID}")
    if not isinstance(live, dict) or not isinstance(clone, dict):
        raise SystemExit("Could not fetch live or clone page")

    package = build_revamp_package(live, list_pages_fn_factory())
    live_layout = copy.deepcopy(live.get("layoutSections") or {})
    patched = patch_layout_sections(live_layout, package)

    hero = hero_rich_text(patched)
    if hero != LIVE_HERO:
        print("ERROR: hero still wrong after patch")
        print(f"  expected len={len(LIVE_HERO)}")
        print(f"  got len={len(hero or '')}")
        print(f"  got: {(hero or '')[:200]}")
        return 1

    aeo_in_hero = package["answerFirst"][:40] in (hero or "")
    if aeo_in_hero:
        print("ERROR: AEO content still in hero")
        return 1

    payload = {
        "htmlTitle": package["htmlTitle"],
        "metaDescription": package["metaDescription"],
        "layoutSections": patched,
    }

    updated = hubspot_request("PATCH", f"{api}/{CLONE_ID}", payload)
    if not isinstance(updated, dict):
        raise SystemExit("PATCH failed")

    verification = verify_clone_content(updated)
    result = {
        "clone_id": CLONE_ID,
        "editor_url": f"https://app-na2.hubspot.com/page-ui/7718689/management/pages/website-pages/{CLONE_ID}/edit",
        "hero_len": len(hero or ""),
        "hero_matches_live": hero == LIVE_HERO,
        "aeo_in_hero": aeo_in_hero,
        "content_confirmed": verification.get("content_confirmed"),
        "text_len": verification.get("text_len"),
        "htmlTitle": package["htmlTitle"],
        "metaDescription": package["metaDescription"],
    }
    print(json.dumps(result, indent=2))
    return 0 if result["hero_matches_live"] and result["content_confirmed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
