#!/usr/bin/env python3
"""Patch SharePoint After URL column via Graph Excel API (works when file is locked)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FORMULAS = Path(__file__).resolve().parent / "_d_formulas.json"
DRIVE_ID = "b!RUUz293X_EC18LYvkmcolkdHB25X00xHirWbk4ejWSAkn2z2REgVTbm6ZMFdID_h"
ITEM_ID = "01M5HJQD2D2CGYFAJFDZAYP5SWFPQTFAZV"
SHEET_ID = "{00000000-0001-0000-0000-000000000000}"
CHUNK = 20


def run_ms365_tool(tool: str, arguments: dict) -> dict:
    payload = json.dumps({"tool": tool, "arguments": arguments})
    cmd = [
        "npx",
        "-y",
        "@softeria/ms-365-mcp-server@latest",
        "--org-mode",
        "--call-tool",
        payload,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    out = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        raise SystemExit(f"{tool} failed: {out}")
    return json.loads(out)


def patch_range(address: str, formulas: list[list[str]]) -> None:
    result = run_ms365_tool(
        "update-excel-range",
        {
            "driveId": DRIVE_ID,
            "driveItemId": ITEM_ID,
            "workbookWorksheetId": SHEET_ID,
            "address": address,
            "body": {"formulas": formulas},
        },
    )
    print(json.dumps({"address": address, "rows": len(formulas), "ok": bool(result)}, indent=2))


def main() -> int:
    data = json.loads(FORMULAS.read_text(encoding="utf-8"))
    d_rows = data["d"]
    start_row = 5
    for offset in range(0, len(d_rows), CHUNK):
        chunk = d_rows[offset : offset + CHUNK]
        row_start = start_row + offset
        row_end = row_start + len(chunk) - 1
        patch_range(f"D{row_start}:D{row_end}", chunk)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
