#!/usr/bin/env python3
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
from hubspot_pages import hubspot_request, _find_page_by_slug, load_dotenv, pages_api
from aeo_revamp import _collect_rich_text
load_dotenv(ROOT)
api = pages_api("site-page")
live = hubspot_request("GET", f"{api}/{_find_page_by_slug('jobs','site-page')['id']}")
clone = hubspot_request("GET", f"{api}/367626505928")

def list_h1_widgets(p, label):
    print(f"\n=== {label} ===")
    containers = p.get("widgetContainers") or {}
    for cid, cdata in containers.items():
        for w in cdata.get("widgets") or []:
            body = w.get("body") or {}
            col1 = body.get("col_1") or {}
            content = str(col1.get("content") or "")
            if "<h1" in content.lower():
                h1 = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.I|re.S)
                text = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else "?"
                print(f"  container={cid[:20]} order={w.get('order')} label={w.get('label')!r} h1={text!r}")

list_h1_widgets(live, "LIVE")
list_h1_widgets(clone, "CLONE")
