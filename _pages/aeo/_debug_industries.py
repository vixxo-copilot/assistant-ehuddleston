#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
from aeo_revamp import _iter_rich_text_targets, _is_hero_rich_text
from hubspot_pages import load_dotenv, pages_api, hubspot_request
from run_aeo_revamp_batch import resolve_live_page

load_dotenv(ROOT)
live = resolve_live_page("industries", "https://www.vixxo.com/industries")
api = pages_api("site-page")
clone = hubspot_request("GET", f"{api}/367618900692")
for label, page in [("LIVE", live), ("CLONE", clone)]:
    print("===", label)
    for entry in _iter_rich_text_targets(page.get("layoutSections") or {}):
        text = entry["obj"].get("rich_text","")
        hero = _is_hero_rich_text(text, entry.get("module_label",""))
        if hero or len(text) > 400:
            print(entry.get("module_label"), "len", len(text), "hero", hero)
            print(" ", text[:200])
