#!/usr/bin/env python3
"""Reprocess specific slugs after structure-clear fix."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))

from aeo_revamp import build_revamp_package, verify_clone_content  # noqa: E402
from hubspot_pages import _find_page_by_slug, hubspot_request, load_config, load_dotenv, pages_api  # noqa: E402
from run_aeo_revamp_batch import list_pages_fn_factory, patch_clone_page  # noqa: E402

load_dotenv(ROOT)
cfg = load_config()
api = pages_api("site-page")

FIXES = {
    "jobs": "367626505928",
}

for slug, clone_id in FIXES.items():
    live = _find_page_by_slug(slug, "site-page")
    live_full = hubspot_request("GET", f"{api}/{live['id']}")
    package = build_revamp_package(live_full, list_pages_fn_factory())
    updated, mode = patch_clone_page(clone_id, live_full, package, cfg, clone_slug=f"{slug}-0")
    ver = verify_clone_content(updated)
    print(slug, mode, ver)
