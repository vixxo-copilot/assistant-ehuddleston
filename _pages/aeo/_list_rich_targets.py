#!/usr/bin/env python3
import json
from pathlib import Path


def list_rich_targets(obj, path="", label_ctx=""):
    results = []
    if isinstance(obj, dict):
        lbl = obj.get("label", label_ctx)
        if "label" in obj and obj["label"]:
            lbl = obj["label"]
        if "rich_text" in obj and isinstance(obj["rich_text"], str):
            rt = obj["rich_text"]
            results.append({
                "label": lbl,
                "path": path,
                "len": len(rt),
                "has_h1": "<h1" in rt.lower(),
                "has_h2": "<h2" in rt.lower(),
                "preview": rt[:120].replace("\n", " "),
            })
        for k, v in obj.items():
            results.extend(list_rich_targets(v, f"{path}.{k}", lbl))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(list_rich_targets(item, f"{path}[{i}]", label_ctx))
    return results


pid = "360125976278"
files = sorted(Path("_pages/staging/" + pid).glob("page-backup-*.json"))
data = json.loads(files[-1].read_text(encoding="utf-8"))
targets = list_rich_targets(data.get("layoutSections", {}))
for i, t in enumerate(targets):
    print(f"{i}: label={t['label']!r} len={t['len']} h1={t['has_h1']} h2={t['has_h2']}")
    print(f"   {t['preview']}")
