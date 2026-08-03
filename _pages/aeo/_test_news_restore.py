#!/usr/bin/env python3
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))

from aeo_revamp import (
    build_revamp_package,
    build_stage_payload,
    _iter_rich_text_targets,
    _is_hero_rich_text,
    layout_has_content,
    _collect_rich_text,
)
from hubspot_pages import hubspot_request, load_config, load_dotenv, pages_api
from run_aeo_revamp_batch import list_pages_fn_factory, resolve_live_page

load_dotenv(ROOT)
cfg = load_config()
api = pages_api("site-page")

slug = "resources/facilities-management-and-company-news"
clone_id = "367618900707"
live = resolve_live_page(slug, "https://www.vixxo.com/resources/facilities-management-and-company-news")
clone = hubspot_request("GET", f"{api}/{clone_id}")
package = build_revamp_package(live, list_pages_fn_factory())

print("live layout content:", layout_has_content(live), "len", len(_collect_rich_text(live.get("layoutSections") or {})))
print("clone layout content:", layout_has_content(clone), "len", len(_collect_rich_text(clone.get("layoutSections") or {})))

payload = build_stage_payload(clone, package, cfg, live_page=live)
print("payload keys:", list(payload.keys()))
print("layout len in payload:", len(_collect_rich_text(payload.get("layoutSections") or {})))

for entry in _iter_rich_text_targets(payload.get("layoutSections") or {}):
    text = entry["obj"].get("rich_text", "")
    if _is_hero_rich_text(text, entry.get("module_label", "")):
        print("PAYLOAD hero len", len(text), "aeo", "Vixxo helps" in text or "case study" in text[:200])
        print("  start:", text[:150])

updated = hubspot_request("PATCH", f"{api}/{clone_id}", payload)
for entry in _iter_rich_text_targets(updated.get("layoutSections") or {}):
    text = entry["obj"].get("rich_text", "")
    if _is_hero_rich_text(text, entry.get("module_label", "")):
        print("UPDATED hero len", len(text))
        print("  start:", text[:150])
