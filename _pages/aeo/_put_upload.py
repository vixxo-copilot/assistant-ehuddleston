#!/usr/bin/env python3
"""PUT local workbook to SharePoint upload session URL from JSON."""
from __future__ import annotations

import json
import ssl
import sys
import urllib.request
from pathlib import Path

WORKBOOK = Path(__file__).resolve().parent / "Vixxo-AEO-Website-Revamp-Status.xlsx"
SESSION = json.loads(
    (Path(__file__).resolve().parent / "_upload_session.json").read_text(encoding="utf-8")
)


def main() -> None:
    upload_url = SESSION["uploadUrl"]
    data = WORKBOOK.read_bytes()
    req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            "Content-Length": str(len(data)),
            "Content-Range": f"bytes 0-{len(data) - 1}/{len(data)}",
        },
        method="PUT",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(json.dumps({"status": resp.status, "bytes": len(data), "body": body[:800]}))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"error": exc.code, "detail": err[:800]}))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
