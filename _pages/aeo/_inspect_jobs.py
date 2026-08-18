#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
from hubspot_pages import hubspot_request, _find_page_by_slug, load_dotenv, pages_api
from aeo_revamp import _collect_rich_text
load_dotenv(ROOT)
api = pages_api("site-page")
for slug, cid in [("jobs", "367626505928")]:
    live = _find_page_by_slug(slug, "site-page")
    live_f = hubspot_request("GET", f"{api}/{live['id']}")
    clone = hubspot_request("GET", f"{api}/{cid}")
    for label, p in [("LIVE", live_f), ("CLONE", clone)]:
        text = _collect_rich_text(p.get("widgetContainers") or {})
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
        print(label, "slug:", p.get("slug"), "h1s:", [re.sub(r"<[^>]+>", "", h).strip() for h in h1s])
