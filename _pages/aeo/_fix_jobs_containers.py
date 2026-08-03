#!/usr/bin/env python3
import copy, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
from hubspot_pages import hubspot_request, _find_page_by_slug, load_dotenv, pages_api
from aeo_revamp import build_revamp_package, copy_live_structure
from run_aeo_revamp_batch import list_pages_fn_factory
load_dotenv(ROOT)
api = pages_api("site-page")
clone_id = "367626505928"
live = hubspot_request("GET", f"{api}/{_find_page_by_slug('jobs','site-page')['id']}")
clone = hubspot_request("GET", f"{api}/{clone_id}")
package = build_revamp_package(live, list_pages_fn_factory())
payload = copy_live_structure(live, package)

live_keys = set((live.get("widgetContainers") or {}).keys())
clone_keys = set((clone.get("widgetContainers") or {}).keys())
stale = clone_keys - live_keys
print("stale containers:", stale)
for key in stale:
    payload["widgetContainers"][key] = {"widgets": []}

print("patching with", len(payload.get("widgetContainers", {})), "containers")
updated = hubspot_request("PATCH", f"{api}/{clone_id}", payload)
clone2 = hubspot_request("GET", f"{api}/{clone_id}")
print("after containers:", list((clone2.get("widgetContainers") or {}).keys()))
