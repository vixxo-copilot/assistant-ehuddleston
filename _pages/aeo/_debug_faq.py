#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
from aeo_revamp import _iter_rich_text_targets, _is_hero_rich_text
from hubspot_pages import load_dotenv, pages_api, hubspot_request
from run_aeo_revamp_batch import resolve_live_page

load_dotenv(ROOT)
live = resolve_live_page("faq", "https://www.vixxo.com/faq")
api = pages_api("site-page")
clone = hubspot_request("GET", f"{api}/367618900684")
for label, page in [("LIVE", live), ("CLONE", clone)]:
    print("===", label)
    for entry in _iter_rich_text_targets(page.get("layoutSections") or {}):
        text = entry["obj"].get("rich_text","")
        print(entry.get("module_label"), "len", len(text), "hero", _is_hero_rich_text(text, entry.get("module_label","")))
        if "Vixxo" in text[:80] or len(text) < 300:
            print(" ", text[:160])
