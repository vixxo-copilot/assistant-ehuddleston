#!/usr/bin/env python3
"""Regenerate SharePoint upload payload from a fixed AEO tracker workbook."""
from __future__ import annotations

import argparse
import base64
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKBOOK = ROOT / "_pages" / "aeo" / "Vixxo-AEO-Website-Revamp-Status.xlsx"
DEFAULT_FIXED = ROOT / "_pages" / "aeo" / "Vixxo-AEO-Website-Revamp-Status-fixed.xlsx"
UPLOAD_ARGS = ROOT / "_pages" / "aeo" / "upload-mcp-args.json"
DRIVE_ID = "b!RUUz293X_EC18LYvkmcolkdHB25X00xHirWbk4ejWSAkn2z2REgVTbm6ZMFdID_h"
ITEM_ID = "01M5HJQD2D2CGYFAJFDZAYP5SWFPQTFAZV"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", nargs="?", default=str(DEFAULT_WORKBOOK))
    parser.add_argument("--fixed-copy", default=str(DEFAULT_FIXED))
    args = parser.parse_args()

    source = Path(args.workbook)
    fixed = Path(args.fixed_copy)
    if not source.is_file():
        raise SystemExit(f"Workbook not found: {source}")

    try:
        shutil.copy2(source, fixed)
        copied = True
    except PermissionError:
        copied = False

    upload_source = fixed if fixed.is_file() else source
    payload = {
        "driveId": DRIVE_ID,
        "driveItemId": ITEM_ID,
        "body": base64.b64encode(upload_source.read_bytes()).decode("ascii"),
    }
    UPLOAD_ARGS.write_text(json.dumps(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ready",
                "source": str(source),
                "fixedCopy": str(fixed),
                "fixedCopyUpdated": copied,
                "uploadArgs": str(UPLOAD_ARGS),
                "bytes": upload_source.stat().st_size,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
