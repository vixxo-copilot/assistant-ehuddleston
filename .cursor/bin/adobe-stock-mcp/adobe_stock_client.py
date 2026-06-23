#!/usr/bin/env python3
"""Adobe Stock API client — search and download for campaign image pipeline.

Search requires ADOBE_STOCK_API_KEY (Client ID from Adobe Developer Console).
Full-resolution licensed download requires ADOBE_STOCK_ACCESS_TOKEN (OAuth or
service account) plus license API calls.

Without access token, downloads the largest available thumbnail/comp URL from
search results (suitable for HubSpot draft staging; license before publish).

Docs: https://developer.adobe.com/stock/docs/api/
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ADOBE_STOCK_SEARCH = "https://stock.adobe.io/Rest/Media/1/Search/Files"
ADOBE_STOCK_LICENSE = "https://stock.adobe.io/Rest/Libraries/1/Content/License"
ADOBE_IMS_TOKEN = "https://ims-na1.adobe.com/ims/token/v3"
X_PRODUCT = "VixxoHubSpotCampaign/1.0"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_dotenv(root: Path | None = None) -> None:
    env_path = (root or repo_root()) / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def api_key() -> str:
    key = (
        os.environ.get("ADOBE_STOCK_API_KEY", "").strip()
        or os.environ.get("ADOBE_STOCK_CLIENT_ID", "").strip()
    )
    if not key:
        raise SystemExit(
            "ADOBE_STOCK_API_KEY (Adobe Developer Console Client ID) is required."
        )
    return key


def stock_headers(access_token: str | None = None) -> dict[str, str]:
    headers = {
        "x-api-key": api_key(),
        "x-product": X_PRODUCT,
        "Accept": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def get_access_token() -> str | None:
    token = os.environ.get("ADOBE_STOCK_ACCESS_TOKEN", "").strip()
    if token:
        return token
    client_id = os.environ.get("ADOBE_STOCK_CLIENT_ID", "").strip() or api_key()
    client_secret = os.environ.get("ADOBE_STOCK_CLIENT_SECRET", "").strip()
    if not client_secret:
        return None
    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid,AdobeID,read_organizations,additional_info.projectedProductContext",
        }
    ).encode()
    req = urllib.request.Request(
        ADOBE_IMS_TOKEN,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("access_token")
    except urllib.error.HTTPError:
        return None


def search_files(
    words: str,
    limit: int = 1,
    orientation: str = "horizontal",
    content_type: str = "photo",
) -> list[dict]:
    """Search Adobe Stock. Returns list of file objects from API."""
    params = {
        "locale": "en_US",
        "search_parameters[words]": words,
        "search_parameters[limit]": str(limit),
        "search_parameters[offset]": "0",
        "search_parameters[order]": "relevance",
        "search_parameters[filters][content_type:photo]": "1" if content_type == "photo" else "0",
    }
    if orientation == "horizontal":
        params["search_parameters[filters][orientation]"] = "horizontal"
    elif orientation == "vertical":
        params["search_parameters[filters][orientation]"] = "vertical"

    url = f"{ADOBE_STOCK_SEARCH}?{urllib.parse.urlencode(params)}"
    token = get_access_token()
    req = urllib.request.Request(url, headers=stock_headers(token), method="GET")
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Adobe Stock search failed HTTP {exc.code}: {err}") from exc

    files = data.get("files") or []
    return files if isinstance(files, list) else []


def pick_download_url(file_obj: dict) -> tuple[str, str]:
    """Pick best available URL from search result. Returns (url, quality_label)."""
    for key, label in (
        ("comp_url", "comp"),
        ("thumbnail_1000_url", "thumbnail_1000"),
        ("thumbnail_500_url", "thumbnail_500"),
        ("thumbnail_240_url", "thumbnail_240"),
        ("thumbnail_url", "thumbnail"),
    ):
        url = file_obj.get(key)
        if url:
            return url, label
    # nested thumbnail object in some responses
    thumb = file_obj.get("thumbnail") or {}
    if isinstance(thumb, dict):
        for k in ("1000", "500", "240"):
            if thumb.get(k):
                return thumb[k], f"thumbnail_{k}"
    raise SystemExit(f"No download URL in Adobe Stock result id={file_obj.get('id')}")


def license_and_download(content_id: int, access_token: str) -> dict:
    """Request Standard license and return download URL."""
    params = urllib.parse.urlencode(
        {
            "content_id": str(content_id),
            "license": "Standard",
            "locale": "en_US",
        }
    )
    url = f"{ADOBE_STOCK_LICENSE}?{params}"
    req = urllib.request.Request(url, headers=stock_headers(access_token), method="GET")
    with urllib.request.urlopen(req, context=ssl_context(), timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_bytes(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "VixxoAdobeStockClient/1.0"},
    )
    with urllib.request.urlopen(req, context=ssl_context(), timeout=120) as resp:
        content = resp.read()
        ctype = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    ext = "jpg"
    if "png" in ctype:
        ext = "png"
    elif "webp" in ctype:
        ext = "webp"
    return content, ext


def search_and_download(
    query: str,
    placement: str = "hero",
    limit: int = 1,
) -> dict:
    """Search Adobe Stock and download best available asset bytes metadata."""
    load_dotenv()
    files = search_files(query, limit=limit)
    if not files:
        raise SystemExit(f"No Adobe Stock results for query: {query}")

    file_obj = files[0]
    content_id = file_obj.get("id")
    title = file_obj.get("title") or query
    access_token = get_access_token()
    download_url = None
    quality = None
    license_info = None

    if access_token and content_id:
        try:
            license_info = license_and_download(int(content_id), access_token)
            download_url = license_info.get("download_url") or license_info.get("url")
            quality = "licensed_standard"
        except urllib.error.HTTPError:
            pass

    if not download_url:
        download_url, quality = pick_download_url(file_obj)

    content, ext = download_bytes(download_url)
    return {
        "adobe_stock_id": content_id,
        "title": title,
        "search_query": query,
        "placement": placement,
        "download_url": download_url,
        "quality": quality,
        "license_info": license_info,
        "file_bytes_len": len(content),
        "extension": ext,
        "content": content,
        "creator_name": file_obj.get("creator_name"),
        "license_note": (
            "Licensed via API" if quality == "licensed_standard"
            else "Preview/comp/thumbnail only — license in Adobe Stock before publish"
        ),
    }


if __name__ == "__main__":
    import argparse
    import base64

    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--placement", default="hero")
    parser.add_argument("--save", help="Save downloaded bytes to path")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    result = search_and_download(args.query, placement=args.placement)
    content = result.pop("content")
    if args.save:
        Path(args.save).write_bytes(content)
        result["saved_to"] = args.save
    if args.json_only:
        print(json.dumps(result, indent=2))
    else:
        result["content_base64"] = base64.b64encode(content).decode("ascii")
        print(json.dumps(result, indent=2))
