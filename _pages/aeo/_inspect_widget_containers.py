#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))
from hubspot_pages import hubspot_request, _find_page_by_slug, load_dotenv, pages_api
from aeo_revamp import _collect_rich_text
load_dotenv(ROOT)
api = pages_api("site-page")

for slug in ["privacy-policy", "solutions/commercial-pest-control-services", "thank-you"]:
    live = _find_page_by_slug(slug, "site-page")
    p = hubspot_request("GET", f"{api}/{live['id']}")
    text = _collect_rich_text(p.get("widgetContainers") or {})
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    h1_text = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else None
    print(f"\n=== {slug} ===")
    print("H1:", h1_text)
    print("text len:", len(text))
    # list widgets in containers
    containers = p.get("widgetContainers") or {}
    for cid, cdata in list(containers.items())[:3]:
        widgets = cdata.get("widgets") or []
        for w in widgets[:5]:
            label = w.get("label") or w.get("body", {}).get("label") or "?"
            body = w.get("body") or {}
            content = ""
            if isinstance(body.get("col_1"), dict):
                content = str(body["col_1"].get("content") or "")[:80]
            elif isinstance(body.get("content"), dict):
                content = str(body["content"].get("text") or "")[:80]
            print(f"  widget order={w.get('order')} label={label!r} content={content!r}")
