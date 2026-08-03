#!/usr/bin/env python3
"""Invoke upload-file-content via ms-365 MCP stdio."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARGS_PATH = Path(__file__).resolve().parent / "upload-mcp-args.json"


def send(proc: subprocess.Popen, msg: dict) -> dict:
    line = json.dumps(msg) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()
    while True:
        resp_line = proc.stdout.readline()
        if not resp_line:
            raise RuntimeError("MCP server closed stdout")
        resp = json.loads(resp_line)
        if resp.get("id") == msg.get("id"):
            return resp


def main() -> None:
    args = json.loads(ARGS_PATH.read_text(encoding="utf-8"))
    cmd = ["npx", "-y", "@softeria/ms-365-mcp-server", "--org-mode"]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        init = send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "aeo-upload", "version": "1.0"},
                },
            },
        )
        if init.get("error"):
            raise SystemExit(json.dumps(init, indent=2))
        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        call = send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "upload-file-content",
                    "arguments": {
                        "driveId": args["driveId"],
                        "driveItemId": args["driveItemId"],
                        "body": args["body"],
                    },
                },
            },
        )
        print(json.dumps(call, indent=2))
        if call.get("error"):
            raise SystemExit(1)
        result = call.get("result", {})
        if result.get("isError"):
            raise SystemExit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
