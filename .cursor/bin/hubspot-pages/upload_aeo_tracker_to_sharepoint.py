#!/usr/bin/env python3
"""Upload the AEO status workbook to SharePoint via Microsoft Graph."""
from __future__ import annotations

import base64
import json
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKBOOK = ROOT / "_pages" / "aeo" / "Vixxo-AEO-Website-Revamp-Status.xlsx"
SITE_HOST = "vixxo.sharepoint.com"
SITE_PATH = "/sites/Marketing919"
FOLDER_PATH = "General/Website & SEO/AEO Website Updates"
FILE_NAME = "Vixxo-AEO-Website-Revamp-Status.xlsx"
GRAPH = "https://graph.microsoft.com/v1.0"


def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def run_ms365(args: list[str]) -> dict | list | str:
    cmd = ["npx", "-y", "@softeria/ms-365-mcp-server@latest", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    out = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        raise SystemExit(out or f"ms-365 command failed: {' '.join(args)}")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def graph_request(token: str, method: str, url: str, data: bytes | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if data is not None:
        headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=120) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {url}: {err}") from exc


def get_access_token() -> str:
    verify = run_ms365(["--org-mode", "--verify-login"])
    if not isinstance(verify, dict) or not verify.get("success"):
        raise SystemExit(
            "Microsoft 365 org-mode login required for SharePoint.\n"
            "Run: npx -y @softeria/ms-365-mcp-server@latest --org-mode --login\n"
            "Then complete the device code at https://login.microsoft.com/device"
        )
    # Use Graph through the MCP server's selected account by invoking a lightweight read.
    # Fallback: ask user to ensure org-mode login completed.
    accounts = run_ms365(["--org-mode", "--list-accounts"])
    if not isinstance(accounts, dict) or not accounts.get("accounts"):
        raise SystemExit("No org-mode accounts found after verify-login.")

    # The MCP server stores tokens internally; use Graph via upload session helper below
    # by shelling a one-off node snippet if needed. For now, use device-auth token endpoint
    # exposed by running verify-login with env MS365_MCP_DEBUG - not available.
    raise SystemExit(
        "Org-mode login verified, but direct token export is unavailable from CLI. "
        "Use MCP upload-file-content after Cursor ms365 org-mode login."
    )


def upload_with_token(token: str) -> dict:
    if not WORKBOOK.is_file():
        raise SystemExit(f"Workbook not found: {WORKBOOK}")

    site_url = urllib.parse.quote(f"{SITE_HOST}:{SITE_PATH}:", safe=":/")
    site = graph_request(token, "GET", f"{GRAPH}/sites/{site_url}")
    site_id = site.get("id")
    if not site_id:
        raise SystemExit(f"Could not resolve site id: {json.dumps(site)}")

    drives = graph_request(token, "GET", f"{GRAPH}/sites/{site_id}/drives")
    drive_items = drives.get("value", [])
    if not drive_items:
        raise SystemExit("No document libraries found on site.")
    drive_id = drive_items[0]["id"]

    folder_segments = [urllib.parse.quote(part, safe="") for part in FOLDER_PATH.split("/")]
    folder_url = "/".join(folder_segments)
    file_segment = urllib.parse.quote(FILE_NAME, safe="")
    upload_path = f"{GRAPH}/drives/{drive_id}/root:/{folder_url}/{file_segment}:/content"

    content = WORKBOOK.read_bytes()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    req = urllib.request.Request(upload_path, data=content, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=120) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} upload failed: {err}") from exc


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--token-stdin":
        token = sys.stdin.read().strip()
        result = upload_with_token(token)
        print(json.dumps({"status": "uploaded", "webUrl": result.get("webUrl"), "id": result.get("id")}, indent=2))
        return
    get_access_token()


if __name__ == "__main__":
    main()
