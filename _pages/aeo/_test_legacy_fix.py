#!/usr/bin/env python3
"""Test live-structure restore on one legacy page."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))

from aeo_revamp import (  # noqa: E402
    _collect_rich_text,
    build_revamp_package,
    build_stage_payload,
    verify_clone_content,
)
from hubspot_pages import (  # noqa: E402
    _find_page_by_slug,
    hubspot_request,
    load_config,
    load_dotenv,
    pages_api,
)
from run_aeo_revamp_batch import list_pages_fn_factory, patch_clone_page  # noqa: E402

load_dotenv(ROOT)
cfg = load_config()
api = pages_api("site-page")

slug = "privacy-policy"
clone_id = "367604474599"  # will lookup from audit if wrong

# get clone id from audit
audit = json.loads((ROOT / "_pages/aeo/_live_match_audit.json").read_text())
for r in audit["results"]:
    if r["slug"] == slug:
        clone_id = r["clone_id"]
        break

live = _find_page_by_slug(slug, "site-page")
live_full = hubspot_request("GET", f"{api}/{live['id']}")
package = build_revamp_package(live_full, list_pages_fn_factory())
payload = build_stage_payload({}, package, cfg, live_page=live_full, clone_slug=f"{slug}-0")
print("payload keys:", list(payload.keys()))
print("template live:", (live_full.get("templatePath") or "")[-60:])
print("template payload:", (payload.get("templatePath") or "")[-60:])
updated, mode = patch_clone_page(clone_id, live_full, package, cfg, clone_slug=f"{slug}-0")
ver = verify_clone_content(updated)
text = _collect_rich_text(updated.get("layoutSections") or {}) + _collect_rich_text(updated.get("widgetContainers") or {})
h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
print("mode:", mode)
print("h1:", re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else None)
print("verification:", ver)
