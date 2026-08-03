#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))
from hubspot_pages import hubspot_request, _find_page_by_slug, load_dotenv, pages_api
from aeo_revamp import _collect_rich_text
load_dotenv(ROOT)
api = pages_api("site-page")
live = _find_page_by_slug("about-us/contact-us", "site-page")
live_full = hubspot_request("GET", f"{api}/{live['id']}")
clone = hubspot_request("GET", f"{api}/367619079918")
for label, p in [("LIVE", live_full), ("CLONE", clone)]:
    print("===", label, "===")
    print("template:", (p.get("templatePath") or "")[-80:])
    print("layout len:", len(_collect_rich_text(p.get("layoutSections") or {})))
    print("widgets len:", len(_collect_rich_text(p.get("widgets") or {})))
    print("containers len:", len(_collect_rich_text(p.get("widgetContainers") or {})))
    print("slug:", p.get("slug"))
