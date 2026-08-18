#!/usr/bin/env python3
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
from hubspot_pages import hubspot_request, load_dotenv, pages_api
from aeo_revamp import _collect_rich_text
load_dotenv(ROOT)
api = pages_api("site-page")
clone = hubspot_request("GET", f"{api}/367618899703")
data = hubspot_request("GET", f"{api}?limit=50&state__in=PUBLISHED_OR_SCHEDULED")
live = next(i for i in data["results"] if not i.get("slug"))
live_f = hubspot_request("GET", f"{api}/{live['id']}")
for label, p in [("LIVE", live_f), ("CLONE", clone)]:
    t = _collect_rich_text(p.get("layoutSections") or {})
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.I | re.S)
    print(label, "h1:", re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else None, "len", len(t))
