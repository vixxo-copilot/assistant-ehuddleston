#!/usr/bin/env python3
import json
from pathlib import Path

base = Path(__file__).resolve().parent
chunks = sorted(base.glob("_chunk_*.json"))
requests = []
for i, fp in enumerate(chunks, 1):
    chunk = json.loads(fp.read_text(encoding="utf-8"))
    addr = chunk["address"]
    url = (
        "/drives/b!RUUz293X_EC18LYvkmcolkdHB25X00xHirWbk4ejWSAkn2z2REgVTbm6ZMFdID_h/"
        "items/01M5HJQD2D2CGYFAJFDZAYP5SWFPQTFAZV/workbook/worksheets/"
        "{00000000-0001-0000-0000-000000000000}/range(address='"
        + addr
        + "')"
    )
    requests.append(
        {
            "id": str(i),
            "method": "PATCH",
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": {"formulas": chunk["formulas"]},
        }
    )
(base / "_graph_batch_patch_d.json").write_text(
    json.dumps({"requests": requests}), encoding="utf-8"
)
print("requests", len(requests))
