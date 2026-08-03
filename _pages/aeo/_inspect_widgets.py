#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "bin" / "hubspot-pages"))
from hubspot_pages import hubspot_request, _find_page_by_slug, load_dotenv, pages_api
load_dotenv(ROOT)
api = pages_api("site-page")
live = _find_page_by_slug("privacy-policy", "site-page")
p = hubspot_request("GET", f"{api}/{live['id']}")

def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("content", "rich_text", "text", "html") and isinstance(v, str) and len(v) > 50:
                print(f"{path}.{k}: {v[:150].replace(chr(10), ' ')}")
            else:
                walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            walk(item, f"{path}[{i}]")

print("WIDGETS:")
walk(p.get("widgets"))
print("\nCONTAINERS:")
walk(p.get("widgetContainers"))
