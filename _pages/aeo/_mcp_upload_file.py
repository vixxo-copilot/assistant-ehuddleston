#!/usr/bin/env python3
"""Upload fixed workbook via MS365 MCP upload-file-content."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARGS = json.loads((Path(__file__).resolve().parent / "upload-mcp-args.json").read_text(encoding="utf-8"))
payload = {
    "body": ARGS["body"],
    "driveId": ARGS["driveId"],
    "driveItemId": ARGS["driveItemId"],
    "excludeResponse": True,
}
cmd = [
    "npx",
    "-y",
    "@softeria/ms-365-mcp-server@latest",
    "--org-mode",
    "upload-file-content",
    json.dumps(payload),
]
proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
out = (proc.stdout or proc.stderr or "").strip()
print(out)
raise SystemExit(proc.returncode)
