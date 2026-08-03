#!/usr/bin/env python3
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor/bin/hubspot-pages"))
from hubspot_pages import load_dotenv, pages_api, hubspot_request
from run_aeo_revamp_batch import resolve_live_page
from aeo_revamp import _collect_rich_text, _iter_rich_text_targets, _iter_content_targets

load_dotenv(ROOT)
live = resolve_live_page("resources/facilities-management-and-company-news", "https://www.vixxo.com/resources/facilities-management-and-company-news")
layout = live.get("layoutSections") or {}
print("layout text len", len(_collect_rich_text(layout)))
print("rich_text targets", len(_iter_rich_text_targets(layout)))
print("content targets", len(_iter_content_targets(layout)))
widgets = live.get("widgets") or {}
containers = live.get("widgetContainers") or {}
print("widget text", len(_collect_rich_text(widgets)))
print("container text", len(_collect_rich_text(containers)))

# dump layout module labels
def walk(obj, depth=0):
    if isinstance(obj, dict):
        if obj.get("label"):
            print(" " * depth + "label:", obj.get("label"), "keys:", list(obj.keys())[:8])
        for v in obj.values():
            walk(v, depth+1)
    elif isinstance(obj, list):
        for item in obj:
            walk(item, depth+1)
walk(layout)
