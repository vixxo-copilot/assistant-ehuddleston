#!/usr/bin/env python3
"""HubSpot OAuth — per-user tokens so API edits attribute to the signed-in user."""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

HUBSPOT_AUTH_URL = "https://app.hubspot.com/oauth/authorize"
HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
HUBSPOT_TOKEN_INFO_URL = "https://api.hubapi.com/oauth/v1/access-tokens"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/callback"
DEFAULT_SCOPES = ("content", "files")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def token_path() -> Path:
    override = os.environ.get("HUBSPOT_OAUTH_TOKEN_PATH", "").strip()
    if override:
        return Path(override).expanduser()
    local = repo_root() / ".hubspot" / "oauth-token.json"
    if local.parent.exists() or (repo_root() / ".env").is_file():
        return local
    return Path.home() / ".config" / "hubspot-content" / "oauth-token.json"


def oauth_config() -> dict[str, str]:
    client_id = os.environ.get("HUBSPOT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("HUBSPOT_CLIENT_SECRET", "").strip()
    redirect_uri = os.environ.get("HUBSPOT_REDIRECT_URI", DEFAULT_REDIRECT_URI).strip()
    scopes = os.environ.get("HUBSPOT_OAUTH_SCOPES", " ".join(DEFAULT_SCOPES)).strip()
    if not client_id or not client_secret:
        raise SystemExit(
            "HubSpot OAuth requires HUBSPOT_CLIENT_ID and HUBSPOT_CLIENT_SECRET in .env. "
            "Create a public app at https://developers.hubspot.com/ and register redirect URI "
            f"{redirect_uri}"
        )
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "scopes": scopes,
    }


def _ssl() -> ssl.SSLContext:
    return ssl.create_default_context()


def _form_post(url: str, data: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, context=_ssl(), timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def save_token(token: dict[str, Any]) -> Path:
    path = token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if "expires_at" not in token and token.get("expires_in"):
        token["expires_at"] = int(time.time()) + int(token["expires_in"]) - 60
    path.write_text(json.dumps(token, indent=2), encoding="utf-8")
    return path


def load_token() -> dict[str, Any] | None:
    path = token_path()
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def refresh_access_token(token: dict[str, Any], cfg: dict[str, str]) -> dict[str, Any]:
    refresh = str(token.get("refresh_token") or "").strip()
    if not refresh:
        raise SystemExit("OAuth token expired and no refresh_token is stored. Run: hubspot_content login")
    refreshed = _form_post(
        HUBSPOT_TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "refresh_token": refresh,
        },
    )
    merged = {**token, **refreshed}
    save_token(merged)
    return merged


def get_access_token(*, auto_refresh: bool = True) -> str | None:
    token = load_token()
    if not token:
        return None
    access = str(token.get("access_token") or "").strip()
    if not access:
        return None
    expires_at = int(token.get("expires_at") or 0)
    if auto_refresh and expires_at and time.time() >= expires_at:
        cfg = oauth_config()
        token = refresh_access_token(token, cfg)
        access = str(token.get("access_token") or "").strip()
    return access or None


def token_user_info(access_token: str) -> dict[str, Any]:
    url = f"{HUBSPOT_TOKEN_INFO_URL}/{urllib.parse.quote(access_token, safe='')}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, context=_ssl(), timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def require_oauth_session() -> dict[str, Any]:
    """OAuth access token + HubSpot user identity. Refuses shared private-app tokens."""
    access = get_access_token(auto_refresh=True)
    if not access:
        if os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip():
            raise SystemExit(
                "HUBSPOT_ACCESS_TOKEN is set but OAuth is not connected on this machine. "
                "Private app tokens attribute all edits to one shared account — not the person "
                "using Cursor. Each user must run: "
                "python .cursor/bin/hubspot-content/hubspot_content.py login"
            )
        raise SystemExit(
            "HubSpot OAuth required before staging content. "
            "Run: python .cursor/bin/hubspot-content/hubspot_content.py login"
        )
    stored = load_token() or {}
    user_id = stored.get("user_id")
    user_email = stored.get("user_email")
    hub_id = stored.get("hub_id")
    if not user_id or not user_email:
        info = token_user_info(access)
        user_id = info.get("user_id")
        user_email = info.get("user")
        hub_id = info.get("hub_id")
        enriched = {**stored, "user_id": user_id, "user_email": user_email, "hub_id": hub_id}
        save_token(enriched)
    return {
        "access_token": access,
        "userId": user_id,
        "userEmail": user_email,
        "hubId": hub_id,
    }


def auth_status() -> dict[str, Any]:
    pat = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()
    token = load_token()
    access = get_access_token(auto_refresh=True) if token else None
    status: dict[str, Any] = {
        "tokenPath": str(token_path()),
        "oauthConfigured": bool(
            os.environ.get("HUBSPOT_CLIENT_ID") and os.environ.get("HUBSPOT_CLIENT_SECRET")
        ),
        "oauthConnected": bool(access),
        "privateAppTokenPresent": bool(pat),
        "privateAppAllowedForWrites": False,
        "attributionPolicy": (
            "HubSpot created/updated-by shows the OAuth user on this machine. "
            "Blog public byline uses config blogAuthorId (e.g. Vixxo Management), never the OAuth user."
        ),
    }
    if access:
        try:
            session = require_oauth_session()
            status["hubId"] = session.get("hubId")
            status["userId"] = session.get("userId")
            status["userEmail"] = session.get("userEmail")
            status["readyToStage"] = True
        except Exception as exc:
            status["userLookupError"] = str(exc)[:200]
    elif pat:
        status["readyToStage"] = False
        status["error"] = (
            "HUBSPOT_ACCESS_TOKEN is ignored for writes. Run login so edits attribute to you, "
            "not a shared service account."
        )
    else:
        status["setupRequired"] = True
        status["readyToStage"] = False
        status["loginCommand"] = "python .cursor/bin/hubspot-content/hubspot_content.py login"
    return status


def login(*, open_browser: bool = True) -> dict[str, Any]:
    cfg = oauth_config()
    captured: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != urllib.parse.urlparse(cfg["redirect_uri"]).path:
                self.send_response(404)
                self.end_headers()
                return
            params = urllib.parse.parse_qs(parsed.query)
            if "error" in params:
                captured["error"] = params["error"][0]
                captured["error_description"] = params.get("error_description", [""])[0]
            else:
                captured["code"] = params.get("code", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if captured.get("error"):
                body = f"<h1>HubSpot login failed</h1><p>{captured['error']}</p>"
            else:
                body = "<h1>HubSpot connected</h1><p>You can close this tab and return to Cursor.</p>"
            self.wfile.write(body.encode("utf-8"))

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    redirect = urllib.parse.urlparse(cfg["redirect_uri"])
    host = redirect.hostname or "127.0.0.1"
    port = redirect.port or 8765
    server = HTTPServer((host, port), CallbackHandler)

    params = urllib.parse.urlencode(
        {
            "client_id": cfg["client_id"],
            "redirect_uri": cfg["redirect_uri"],
            "scope": cfg["scopes"],
        }
    )
    auth_url = f"{HUBSPOT_AUTH_URL}?{params}"
    print(f"Open this URL if your browser does not launch automatically:\n{auth_url}")
    if open_browser:
        webbrowser.open(auth_url, new=1, autoraise=True)

    server.handle_request()
    server.server_close()

    if captured.get("error"):
        raise SystemExit(
            f"HubSpot OAuth error: {captured['error']} {captured.get('error_description', '')}".strip()
        )
    code = captured.get("code", "").strip()
    if not code:
        raise SystemExit("HubSpot OAuth did not return an authorization code.")

    token = _form_post(
        HUBSPOT_TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "redirect_uri": cfg["redirect_uri"],
            "code": code,
        },
    )
    access = str(token.get("access_token") or "")
    info: dict[str, Any] = {}
    if access:
        info = token_user_info(access)
        token["user_id"] = info.get("user_id")
        token["user_email"] = info.get("user")
        token["hub_id"] = info.get("hub_id")
    path = save_token(token)

    result = {
        "connected": True,
        "tokenPath": str(path),
        "hubId": info.get("hub_id"),
        "userId": info.get("user_id"),
        "userEmail": info.get("user"),
        "scopes": info.get("scopes"),
        "message": (
            "HubSpot OAuth connected. Created/updated-by in HubSpot will show "
            f"{info.get('user') or 'this user'}. Blog byline stays config blogAuthorId."
        ),
    }
    print(json.dumps(result, indent=2))
    return result


def logout() -> dict[str, Any]:
    path = token_path()
    if path.is_file():
        path.unlink()
    return {"connected": False, "tokenPath": str(path), "message": "HubSpot OAuth token removed."}
