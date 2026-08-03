#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))
from hubspot_pages import hubspot_request, _find_page_by_slug, load_dotenv, pages_api
from aeo_revamp import _collect_rich_text
load_dotenv(ROOT)
api = pages_api("site-page")

# Pick a legacy issue page
slugs = ["privacy-policy", "thank-you", "solutions/commercial-pest-control-services"]
for slug in slugs:
    live = _find_page_by_slug(slug, "site-page")
    if not live:
        print(f"NO LIVE {slug}")
        continue
    p = hubspot_request("GET", f"{api}/{live['id']}")
    print(f"\n=== LIVE {slug} ===")
    print("template:", (p.get("templatePath") or "")[-80:])
    print("layout:", len(_collect_rich_text(p.get("layoutSections") or {})))
    print("widgets:", len(_collect_rich_text(p.get("widgets") or {})))
    print("containers:", len(_collect_rich_text(p.get("widgetContainers") or {})))
