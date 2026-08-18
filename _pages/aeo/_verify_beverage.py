#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0, ".cursor/bin/hubspot-pages")
from aeo_revamp import _iter_rich_text_targets, _is_hero_rich_text

pid = "367618900671"
files = sorted(Path("_pages/staging/" + pid).glob("page-backup-*.json"))
data = json.loads(files[-1].read_text(encoding="utf-8"))
for i, entry in enumerate(_iter_rich_text_targets(data.get("layoutSections", {}))):
    text = entry["obj"].get("rich_text", "")
    hero = _is_hero_rich_text(text, entry.get("module_label", ""))
    aeo = "Vixxo helps multi-site operators" in text or "Frequently Asked Questions" in text
    label = entry.get("module_label", "")[:50]
    print(f"{i}: hero={hero} aeo={aeo} label={label!r} len={len(text)}")
    if i <= 2 or aeo:
        print(f"   start: {text[:150]}")
