#!/usr/bin/env python3
import json
from pathlib import Path


def hero_info(data, label):
    layout = data.get("layoutSections", {})

    def walk(obj):
        if isinstance(obj, dict):
            lbl = obj.get("label", "")
            if "Hero" in lbl:
                params = obj.get("params", {})
                col1 = params.get("col_1", {})
                for c in col1.get("content", []):
                    rt = c.get("rich_text", "")
                    print(f"[{label}] hero label={lbl}")
                    print(f"  content_name={c.get('content_name')}")
                    print(f"  rich_text len={len(rt)}")
                    print(f"  START: {rt[:400]}")
                    print(f"  END: {rt[-250:]}")
                for k, v in params.items():
                    if any(x in k.lower() for x in ("image", "bg", "background", "photo")):
                        print(f"  param {k}: {str(v)[:200]}")
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(layout)
    print(f"[{label}] template: {data.get('templatePath')}")
    print(f"[{label}] htmlTitle: {data.get('htmlTitle')}")
    print(f"[{label}] metaDescription: {(data.get('metaDescription') or '')[:120]}")


for label, pid in [("LIVE", "360125976278"), ("CLONE", "367618900671")]:
    files = sorted(Path("_pages/staging/" + pid).glob("page-backup-*.json"))
    data = json.loads(files[-1].read_text(encoding="utf-8"))
    print("=" * 70)
    hero_info(data, label)
    print()
