#!/usr/bin/env python3
"""Invoke upload-file-content via local MCP JSON-RPC over stdio is unavailable; PUT via upload session."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Emit MCP tool arguments as JSON on stdout for agent consumption.
args = json.loads((Path(__file__).resolve().parent / "upload-mcp-args.json").read_text(encoding="utf-8"))
print(json.dumps({
    "body": args["body"],
    "driveId": args["driveId"],
    "driveItemId": args["driveItemId"],
    "excludeResponse": True,
}))
