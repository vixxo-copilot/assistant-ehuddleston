#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))

from hubspot_pages import hubspot_request, load_dotenv, pages_api
from aeo_revamp import _iter_rich_text_targets, _is_hero_rich_text
from run_aeo_revamp_batch import resolve_live_page

load_dotenv(ROOT)

def show_hero(label, page):
    for entry in _iter_rich_text_targets(page.get("layoutSections") or {}):
        text = str(entry["obj"].get("rich_text") or "")
        if _is_hero_rich_text(text, entry.get("module_label") or ""):
            print(f"{label} hero len={len(text)} label={entry.get('module_label')!r}")
            print(f"  start: {text[:200]}")
            return text
    print(f"{label}: no hero found")
    return None

# Homepage
try:
    live = resolve_live_page("(homepage)", None)
    print("LIVE homepage id", live.get("id"))
    show_hero("LIVE", live)
except Exception as e:
    print("Homepage live error:", e)

api = pages_api("site-page")
clone = hubspot_request("GET", f"{api}/367618899703")
show_hero("CLONE", clone)

# News page
print("\n--- NEWS ---")
live2 = resolve_live_page("resources/facilities-management-and-company-news", "https://www.vixxo.com/resources/facilities-management-and-company-news")
live_h = show_hero("LIVE", live2)
clone2 = hubspot_request("GET", f"{api}/367618900707")
clone_h = show_hero("CLONE", clone2)
print("match:", live_h == clone_h)
