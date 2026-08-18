#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
from aeo_revamp import copy_live_structure, build_revamp_package, _iter_rich_text_targets, _is_hero_rich_text, _collect_rich_text, patch_layout_sections
from hubspot_pages import load_dotenv, pages_api, hubspot_request
from run_aeo_revamp_batch import list_pages_fn_factory, resolve_live_page
import copy

load_dotenv(ROOT)
live = resolve_live_page("resources/facilities-management-and-company-news", "https://www.vixxo.com/resources/facilities-management-and-company-news")
package = build_revamp_package(live, list_pages_fn_factory())

layout = copy.deepcopy(live.get("layoutSections") or {})
print("live layout len", len(_collect_rich_text(layout)))
for entry in _iter_rich_text_targets(layout):
    text = entry["obj"].get("rich_text","")
    print(" target", entry.get("module_label"), "len", len(text), "hero", _is_hero_rich_text(text, entry.get("module_label","")))

patched = patch_layout_sections(layout, package)
for entry in _iter_rich_text_targets(patched):
    text = entry["obj"].get("rich_text","")
    if _is_hero_rich_text(text, entry.get("module_label","")) or "case study" in text[:100]:
        print(" patched", entry.get("module_label"), "len", len(text), "hero", _is_hero_rich_text(text, entry.get("module_label","")))
        print("  ", text[:120])

payload = copy_live_structure(live, package)
print("payload layout len", len(_collect_rich_text(payload.get("layoutSections") or {})))
