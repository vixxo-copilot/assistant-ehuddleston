#!/usr/bin/env python3
"""Merge Profound citation path pulls into _phase0_citations.json."""
import json
from pathlib import Path

AEO = Path(__file__).resolve().parent
rows = json.loads((AEO / "_phase0_citations_page1.json").read_text(encoding="utf-8"))
page2 = json.loads((AEO / "_phase0_citations_page2.json").read_text(encoding="utf-8"))
merged = {r["dimensions"][0]: r for r in rows + page2}
out = {"rows": list(merged.values())}
(AEO / "_phase0_citations.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(len(out["rows"]))
