#!/usr/bin/env python3
"""HubSpot campaign image pipeline: resolve stock, upload to File Manager, emit landing-page insert specs.

HubSpot Breeze AI image generation has no public API (UI-only). This module implements:
  1. hubspot_native_placeholder — validator-safe HubSpot static CDN slot
  2. shutterstock — search + download preview (requires SHUTTERSTOCK_API_TOKEN)
  3. upload — push bytes to HubSpot Files API (requires HUBSPOT_ACCESS_TOKEN)
  4. insert_spec — JSON payload for manage_landing_page SET_MODULE_FIELDS on @hubspot/linked_image
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HUBSPOT_PLACEHOLDER = (
    "https://static.hsappstatic.net/FileManagerImages/static-1.5071/images/image-placeholder.png"
)
HUBSPOT_FILES_API = "https://api.hubapi.com/files/v3/files"
SHUTTERSTOCK_SEARCH_API = "https://api.shutterstock.com/v2/images/search"
PEXELS_SEARCH_API = "https://api.pexels.com/v1/search"
OPENVERSE_SEARCH_API = "https://api.openverse.org/v1/images/"

# Adobe Stock client lives in sibling package
ADOBE_STOCK_DIR = Path(__file__).resolve().parent.parent / "adobe-stock-mcp"

PLACEMENT_QUERY_SUFFIX = {
    "hero": "commercial retail rooftop HVAC units aerial multi-site",
    "section_roi": "facilities executive meeting boardroom retail portfolio",
    "section_scale": "retail store exterior chain nationwide locations",
    "section_technician": "commercial HVAC technician rooftop unit professional",
    "email_header": "commercial building HVAC maintenance professional wide",
}


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


def http_json(method: str, url: str, headers: dict | None = None, data: bytes | None = None) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {url}: {err_body}") from exc


def build_search_query(prompt: str, placement: str) -> str:
    suffix = PLACEMENT_QUERY_SUFFIX.get(placement, "commercial facilities HVAC")
    return f"{prompt} {suffix}".strip()


def resolve_shutterstock_preview(query: str) -> dict | None:
    token = os.environ.get("SHUTTERSTOCK_API_TOKEN", "").strip()
    if not token:
        return None
    params = urllib.parse.urlencode(
        {
            "query": query,
            "image_type": "photo",
            "orientation": "horizontal",
            "people_model_released": "true",
            "safe": "true",
            "per_page": "1",
            "sort": "popular",
        }
    )
    url = f"{SHUTTERSTOCK_SEARCH_API}?{params}"
    result = http_json("GET", url, headers={"Authorization": f"Bearer {token}"})
    data = result.get("data") or []
    if not data:
        return None
    item = data[0]
    assets = item.get("assets") or {}
    preview = assets.get("preview") or assets.get("huge") or {}
    preview_url = preview.get("url")
    if not preview_url:
        return None
    return {
        "source": "shutterstock_preview",
        "image_id": item.get("id"),
        "description": item.get("description") or query,
        "preview_url": preview_url,
        "license_note": (
            "Preview only. License in Shutterstock before production publish, "
            "or save via HubSpot File Manager > Stock Images in UI."
        ),
    }


def resolve_pexels_preview(query: str) -> dict | None:
    token = os.environ.get("PEXELS_API_KEY", "").strip()
    if not token:
        return None
    params = urllib.parse.urlencode({"query": query, "per_page": "1", "orientation": "landscape"})
    url = f"{PEXELS_SEARCH_API}?{params}"
    try:
        result = http_json("GET", url, headers={"Authorization": token})
    except SystemExit:
        return None
    photos = result.get("photos") or []
    if not photos:
        return None
    photo = photos[0]
    src = photo.get("src") or {}
    preview_url = src.get("large2x") or src.get("large") or src.get("original")
    if not preview_url:
        return None
    return {
        "source": "pexels",
        "image_id": photo.get("id"),
        "description": photo.get("alt") or query,
        "preview_url": preview_url,
        "license_note": "Pexels license — verify attribution requirements before publish.",
    }


def resolve_wikimedia_preview(query: str) -> dict | None:
    """Search Wikimedia Commons for a topic-relevant photo (no API key required)."""
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": "8",
            "gsrnamespace": "6",
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": "2500",
        }
    )
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "vixxo-hubspot-content/1.0"})
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None
    pages = (result.get("query") or {}).get("pages") or {}
    for page in pages.values():
        title = str(page.get("title") or "")
        info = (page.get("imageinfo") or [{}])[0]
        mime = str(info.get("mime") or "")
        preview_url = info.get("url") or ""
        if not mime.startswith("image/") or not preview_url:
            continue
        lower = title.lower()
        if any(ext in lower for ext in (".pdf", ".djvu", ".svg", ".tif")):
            continue
        return {
            "source": "wikimedia",
            "image_id": page.get("pageid"),
            "description": title.replace("File:", ""),
            "preview_url": preview_url,
            "license_note": "Wikimedia Commons — verify license and attribution before publish.",
        }
    return None


def resolve_openverse_preview(query: str) -> dict | None:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "page_size": "1",
            "license_type": "commercial,modification",
        }
    )
    url = f"{OPENVERSE_SEARCH_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "vixxo-hubspot-content/1.0"})
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None
    items = result.get("results") or []
    if not items:
        return None
    item = items[0]
    preview_url = item.get("url") or item.get("thumbnail")
    if not preview_url:
        return None
    return {
        "source": "openverse",
        "image_id": item.get("id"),
        "description": item.get("title") or query,
        "preview_url": preview_url,
        "license_note": item.get("license") or "Verify Openverse license before publish.",
    }


def download_bytes(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "vixxo-hubspot-campaign-images/1.0"})
    with urllib.request.urlopen(req, context=ssl_context(), timeout=120) as resp:
        content = resp.read()
        ctype = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    ext = mimetypes.guess_extension(ctype) or ".jpg"
    return content, ext.lstrip(".")


def _resolve_hubspot_auth_token() -> str | None:
    import sys

    oauth_dir = Path(__file__).resolve().parent.parent / "hubspot-content"
    if oauth_dir.is_dir() and str(oauth_dir) not in sys.path:
        sys.path.insert(0, str(oauth_dir))
    try:
        from hubspot_oauth import get_access_token

        oauth_token = get_access_token(auto_refresh=True)
        if oauth_token:
            return oauth_token
    except Exception:
        pass
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()
    return token or None


def _hubspot_auth_token() -> str:
    token = _resolve_hubspot_auth_token()
    if token:
        return token
    raise SystemExit(
        "HubSpot auth required for upload. Run hubspot_content login "
        "or set HUBSPOT_ACCESS_TOKEN."
    )


def upload_to_hubspot(
    file_bytes: bytes,
    filename: str,
    folder_path: str = "/campaign-images",
    access: str = "PUBLIC_NOT_INDEXABLE",
) -> dict:
    token = _hubspot_auth_token()

    boundary = "----VixxoHubSpotCampaignBoundary"
    options = json.dumps({"access": access})
    parts: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode()
        )

    def add_file(name: str, fname: str, content: bytes, content_type: str) -> None:
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"; filename="{fname}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode()
        )
        parts.append(content)
        parts.append(b"\r\n")

    add_field("options", options)
    add_field("folderPath", folder_path)
    add_field("fileName", filename)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    add_file("file", filename, file_bytes, ctype)
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        HUBSPOT_FILES_API,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HubSpot Files upload failed HTTP {exc.code}: {err_body}") from exc


def linked_image_field_overrides(url: str, alt: str) -> dict:
    return {
        "img": {
            "src": url,
            "alt": alt,
            "width": 1200,
            "height": 675,
        }
    }


def resolve_adobe_stock(query: str, placement: str) -> dict:
    """Search Adobe Stock and download bytes via adobe_stock_client."""
    import sys

    adobe_dir = str(ADOBE_STOCK_DIR)
    if adobe_dir not in sys.path:
        sys.path.insert(0, adobe_dir)
    from adobe_stock_client import search_and_download  # noqa: WPS433

    downloaded = search_and_download(query, placement=placement)
    content = downloaded.pop("content")
    ext = downloaded.get("extension") or "jpg"
    filename = f"hvac-pm-2026-{placement}-adobe-{downloaded.get('adobe_stock_id')}.{ext}"
    return {
        "source": "adobe_stock",
        "filename": filename,
        "file_bytes": content,
        "alt": (downloaded.get("title") or query)[:125],
        **downloaded,
    }


def cmd_adobe_import(args: argparse.Namespace) -> None:
    load_dotenv()
    query = args.query or build_search_query(args.prompt or "HVAC retail portfolio", args.placement)
    adobe = resolve_adobe_stock(query, args.placement)
    folder = args.folder or "/campaign-images/hvac-pm-2026"
    alt = args.alt or adobe.get("alt") or query[:125]

    uploaded = upload_to_hubspot(adobe["file_bytes"], adobe["filename"], folder_path=folder)
    final_url = uploaded.get("url") or uploaded.get("defaultHostingUrl")

    output = {
        "placement": args.placement,
        "search_query": query,
        "adobe_stock_id": adobe.get("adobe_stock_id"),
        "quality": adobe.get("quality"),
        "license_note": adobe.get("license_note"),
        "hubspot_file_id": uploaded.get("id"),
        "hubspot_url": final_url,
        "alt": alt,
        "folder": folder,
    }
    if args.content_id and args.module_id:
        output["manage_landing_page"] = {
            "action": "SET_MODULE_FIELDS",
            "contentId": int(args.content_id),
            "moduleId": args.module_id,
            "fieldOverridesJson": json.dumps(linked_image_field_overrides(final_url, alt)),
        }
    print(json.dumps(output, indent=2))


def cmd_adobe_import_set(args: argparse.Namespace) -> None:
    load_dotenv()
    placements = ["hero", "section_roi", "section_scale", "section_technician", "email_header"]
    results = []
    for placement in placements:
        query = build_search_query("HVAC preventative maintenance retail portfolio", placement)
        try:
            adobe = resolve_adobe_stock(query, placement)
            folder = args.folder or "/campaign-images/hvac-pm-2026"
            alt = adobe.get("alt") or query[:125]
            uploaded = upload_to_hubspot(adobe["file_bytes"], adobe["filename"], folder_path=folder)
            results.append(
                {
                    "placement": placement,
                    "search_query": query,
                    "adobe_stock_id": adobe.get("adobe_stock_id"),
                    "quality": adobe.get("quality"),
                    "license_note": adobe.get("license_note"),
                    "hubspot_file_id": uploaded.get("id"),
                    "hubspot_url": uploaded.get("url") or uploaded.get("defaultHostingUrl"),
                    "alt": alt,
                }
            )
        except SystemExit as exc:
            results.append({"placement": placement, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            results.append({"placement": placement, "error": str(exc)})
    print(json.dumps({"imports": results}, indent=2))


def resolve_image(prompt: str, placement: str, prefer: str = "auto") -> dict:
    query = build_search_query(prompt, placement)
    result: dict = {
        "placement": placement,
        "prompt": prompt,
        "search_query": query,
        "breeze_ai_note": (
            "HubSpot Breeze AI image generation has no public API. "
            "Replace placeholder in HubSpot UI: image module > Generate with AI, "
            f'prompt: "{query}"'
        ),
    }

    if prefer in ("auto", "adobe_stock", "adobe"):
        try:
            adobe = resolve_adobe_stock(query, placement)
            return {
                **result,
                "source": "adobe_stock",
                "url": "pending_upload",
                "alt": adobe.get("alt"),
                "adobe_stock_id": adobe.get("adobe_stock_id"),
                "quality": adobe.get("quality"),
                "license_note": adobe.get("license_note"),
                "filename": adobe.get("filename"),
                "file_bytes": adobe.get("file_bytes"),
                "hubspot_upload_recommended": True,
            }
        except SystemExit:
            if prefer == "adobe_stock" or prefer == "adobe":
                raise
        except Exception:
            if prefer in ("adobe_stock", "adobe"):
                raise

    if prefer in ("auto", "shutterstock"):
        ss = resolve_shutterstock_preview(query)
        if ss:
            result.update(
                {
                    "source": "shutterstock_preview",
                    "url": ss["preview_url"],
                    "alt": ss["description"][:125],
                    "shutterstock_image_id": ss.get("image_id"),
                    "license_note": ss.get("license_note"),
                    "hubspot_upload_recommended": True,
                }
            )
            return result

    result.update(
        {
            "source": "hubspot_native_placeholder",
            "url": HUBSPOT_PLACEHOLDER,
            "alt": f"[REPLACE WITH BREEZE AI] {prompt[:80]}",
            "replace_via": "HubSpot editor > Generate with AI or Stock Images tab",
        }
    )
    return result


def cmd_resolve(args: argparse.Namespace) -> None:
    load_dotenv()
    out = resolve_image(args.prompt, args.placement, prefer=args.prefer)
    file_bytes = out.pop("file_bytes", None)
    if file_bytes is not None:
        out["has_file_bytes"] = True
        out["file_bytes_size"] = len(file_bytes)
    print(json.dumps(out, indent=2))


def cmd_upload(args: argparse.Namespace) -> None:
    load_dotenv()
    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")
    data = path.read_bytes()
    filename = args.filename or path.name
    uploaded = upload_to_hubspot(data, filename, folder_path=args.folder)
    print(
        json.dumps(
            {
                "file_id": uploaded.get("id"),
                "url": uploaded.get("url") or uploaded.get("defaultHostingUrl"),
                "name": uploaded.get("name"),
                "folder": args.folder,
            },
            indent=2,
        )
    )


def cmd_upload_url(args: argparse.Namespace) -> None:
    load_dotenv()
    content, ext = download_bytes(args.url)
    filename = args.filename or f"campaign-{args.placement}.{ext}"
    uploaded = upload_to_hubspot(content, filename, folder_path=args.folder)
    print(
        json.dumps(
            {
                "source_url": args.url,
                "file_id": uploaded.get("id"),
                "url": uploaded.get("url") or uploaded.get("defaultHostingUrl"),
                "alt": args.alt,
                "placement": args.placement,
            },
            indent=2,
        )
    )


def cmd_insert_spec(args: argparse.Namespace) -> None:
    overrides = linked_image_field_overrides(args.url, args.alt)
    spec = {
        "hubspot_upstream_call": {
            "name": "manage_landing_page",
            "arguments": {
                "action": "SET_MODULE_FIELDS",
                "contentId": args.content_id,
                "moduleId": args.module_id,
                "fieldOverridesJson": json.dumps(overrides),
            },
        },
        "field_overrides": overrides,
        "placement": args.placement,
        "image_url": args.url,
        "alt": args.alt,
    }
    print(json.dumps(spec, indent=2))


def cmd_pipeline(args: argparse.Namespace) -> None:
    load_dotenv()
    resolved = resolve_image(args.prompt, args.placement, prefer=args.prefer)
    file_bytes = resolved.pop("file_bytes", None)
    filename_override = resolved.pop("filename", None)
    final_url = resolved["url"]
    alt = args.alt or resolved.get("alt") or args.prompt[:125]

    upload_result = None
    if args.upload and resolved.get("hubspot_upload_recommended") and _resolve_hubspot_auth_token():
        if file_bytes is not None:
            content = file_bytes
            ext = Path(filename_override or "").suffix.lstrip(".") or "jpg"
            filename = filename_override or f"hvac-pm-2026-{args.placement}.{ext}"
        else:
            content, ext = download_bytes(final_url)
            filename = f"hvac-pm-2026-{args.placement}.{ext}"
        folder = args.folder or "/campaign-images/hvac-pm-2026"
        upload_result = upload_to_hubspot(content, filename, folder_path=folder)
        final_url = upload_result.get("url") or upload_result.get("defaultHostingUrl") or final_url

    output = {
        "resolved": resolved,
        "upload": upload_result,
        "final_url": final_url,
        "alt": alt,
    }
    if args.content_id and args.module_id:
        output["manage_landing_page"] = {
            "action": "SET_MODULE_FIELDS",
            "contentId": int(args.content_id),
            "moduleId": args.module_id,
            "fieldOverridesJson": json.dumps(linked_image_field_overrides(final_url, alt)),
        }
    print(json.dumps(output, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="HubSpot campaign image pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="Resolve image URL for placement")
    p_resolve.add_argument("--prompt", required=True)
    p_resolve.add_argument("--placement", required=True)
    p_resolve.add_argument("--prefer", default="auto", choices=["auto", "adobe_stock", "adobe", "shutterstock", "placeholder"])
    p_resolve.set_defaults(func=cmd_resolve)

    p_upload = sub.add_parser("upload", help="Upload local file to HubSpot File Manager")
    p_upload.add_argument("--file", required=True)
    p_upload.add_argument("--folder", default="/campaign-images/hvac-pm-2026")
    p_upload.add_argument("--filename")
    p_upload.set_defaults(func=cmd_upload)

    p_upload_url = sub.add_parser("upload-url", help="Download URL and upload to HubSpot")
    p_upload_url.add_argument("--url", required=True)
    p_upload_url.add_argument("--placement", required=True)
    p_upload_url.add_argument("--alt", required=True)
    p_upload_url.add_argument("--folder", default="/campaign-images/hvac-pm-2026")
    p_upload_url.add_argument("--filename")
    p_upload_url.set_defaults(func=cmd_upload_url)

    p_spec = sub.add_parser("insert-spec", help="Emit manage_landing_page SET_MODULE_FIELDS spec")
    p_spec.add_argument("--url", required=True)
    p_spec.add_argument("--alt", required=True)
    p_spec.add_argument("--module-id", required=True)
    p_spec.add_argument("--content-id", type=int, required=True)
    p_spec.add_argument("--placement", default="hero")
    p_spec.set_defaults(func=cmd_insert_spec)

    p_pipe = sub.add_parser("pipeline", help="Resolve, optional upload, optional insert spec")
    p_pipe.add_argument("--prompt", required=True)
    p_pipe.add_argument("--placement", required=True)
    p_pipe.add_argument("--prefer", default="auto")
    p_pipe.add_argument("--upload", action="store_true")
    p_pipe.add_argument("--folder", default="/campaign-images/hvac-pm-2026")
    p_pipe.add_argument("--alt")
    p_pipe.add_argument("--content-id", type=int)
    p_pipe.add_argument("--module-id")
    p_pipe.set_defaults(func=cmd_pipeline)

    p_adobe = sub.add_parser("adobe-import", help="Adobe Stock search+download+HubSpot upload")
    p_adobe.add_argument("--placement", required=True)
    p_adobe.add_argument("--query")
    p_adobe.add_argument("--prompt")
    p_adobe.add_argument("--alt")
    p_adobe.add_argument("--folder", default="/campaign-images/hvac-pm-2026")
    p_adobe.add_argument("--content-id", type=int)
    p_adobe.add_argument("--module-id")
    p_adobe.set_defaults(func=cmd_adobe_import)

    p_adobe_set = sub.add_parser("adobe-import-set", help="Import all 5 campaign placements")
    p_adobe_set.add_argument("--folder", default="/campaign-images/hvac-pm-2026")
    p_adobe_set.set_defaults(func=cmd_adobe_import_set)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
