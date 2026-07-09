#!/usr/bin/env python3
"""HubSpot CMS site/landing page staging and template migration.

Draft-first — no publish endpoints unless explicitly requested via publish command.
Reuses OAuth from hubspot-content for per-user attribution.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HUBSPOT_API = "https://api.hubapi.com"
SITE_PAGES_API = f"{HUBSPOT_API}/cms/pages/2026-03/site-pages"
LANDING_PAGES_API = f"{HUBSPOT_API}/cms/pages/2026-03/landing-pages"
TEMPLATES_API = f"{HUBSPOT_API}/content/api/v2/templates"

SKILL_DIR = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "hubspot-pages"
CONTENT_BIN = Path(__file__).resolve().parent.parent / "hubspot-content"
sys.path.insert(0, str(CONTENT_BIN))

from hubspot_oauth import auth_status, get_access_token, login, logout, require_oauth_session  # noqa: E402

from page_content import (  # noqa: E402
    apply_package_to_blueprint,
    build_create_payload,
    discover_internal_links,
    normalize_package,
    page_brief_for_topic,
    resolve_page_images,
    write_review_md,
)


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


def hubspot_token() -> str:
    token = get_access_token(auto_refresh=True)
    if token:
        return str(token)
    pat = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()
    allow_pat = os.environ.get("HUBSPOT_PAGES_ALLOW_PRIVATE_APP_TOKEN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    cfg = load_config()
    if not allow_pat and cfg.get("allowPrivateAppToken"):
        allow_pat = True
    if pat and allow_pat:
        return pat
    if pat:
        raise SystemExit(
            "HUBSPOT_ACCESS_TOKEN is set but OAuth is not connected. "
            "Run login, or set HUBSPOT_PAGES_ALLOW_PRIVATE_APP_TOKEN=true "
            "(or allowPrivateAppToken: true in config.yaml) for private-app writes."
        )
    return str(require_oauth_session()["access_token"])


def http_json(
    method: str,
    url: str,
    headers: dict | None = None,
    data: bytes | None = None,
) -> dict | list:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=90) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {url}: {err_body}") from exc


def hubspot_request(method: str, path: str, payload: dict | None = None) -> dict | list:
    url = path if path.startswith("http") else f"{HUBSPOT_API}{path}"
    headers = {
        "Authorization": f"Bearer {hubspot_token()}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    return http_json(method, url, headers=headers, data=data)


LIST_CHILD_KEYS = frozenset({"domains", "excludeSlugs"})


def load_yaml_simple(path: Path) -> dict:
    if not path.is_file():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    result: dict[str, Any] = {}
    stack: list[tuple[int, dict | list]] = [(0, result)]

    for idx, raw_line in enumerate(lines):
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        if line.startswith("- "):
            if not isinstance(parent, list):
                continue
            item_text = line[2:].strip()
            if ":" in item_text:
                key, _, val = item_text.partition(":")
                item: dict[str, Any] = {key.strip(): _parse_scalar(val.strip())}
                parent.append(item)
                stack.append((indent, item))
            else:
                parent.append(_parse_scalar(item_text))
            continue

        if ":" not in line:
            continue
        key, _, raw_val = line.partition(":")
        key = key.strip()
        val = raw_val.strip()
        if not val:
            next_is_list = key in LIST_CHILD_KEYS
            if not next_is_list:
                for future in lines[idx + 1 :]:
                    if not future.strip() or future.strip().startswith("#"):
                        continue
                    future_indent = len(future) - len(future.lstrip())
                    if future_indent <= indent:
                        break
                    next_is_list = future.lstrip().startswith("- ")
                    break
            if next_is_list:
                child_list: list = []
                if isinstance(parent, dict):
                    parent[key] = child_list
                    stack.append((indent, child_list))
            else:
                child_dict: dict[str, Any] = {}
                if isinstance(parent, dict):
                    parent[key] = child_dict
                    stack.append((indent, child_dict))
            continue

        if isinstance(parent, dict):
            parent[key] = _parse_scalar(val)

    return result


def _parse_scalar(value: str) -> Any:
    if "#" in value:
        value = value.split("#", 1)[0].rstrip()
    value = value.strip()
    if not value or value.lower() in {"null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def load_inventory(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Inventory file not found: {path}")
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return load_yaml_simple(path)


def config_path() -> Path:
    for name in ("config.yaml", "config.yml"):
        path = SKILL_DIR / name
        if path.is_file():
            return path
    return SKILL_DIR / "config.yaml"


def load_config() -> dict[str, Any]:
    cfg = load_yaml_simple(config_path())
    example = load_yaml_simple(SKILL_DIR / "config.example.yaml")
    merged = {**example, **cfg}
    page_content_cfg_path = (
        Path(__file__).resolve().parents[3]
        / ".agents"
        / "skills"
        / "hubspot-page-content"
        / "config.yaml"
    )
    if page_content_cfg_path.is_file():
        merged = {**merged, **load_yaml_simple(page_content_cfg_path)}
    else:
        page_content_example = (
            Path(__file__).resolve().parents[3]
            / ".agents"
            / "skills"
            / "hubspot-page-content"
            / "config.example.yaml"
        )
        if page_content_example.is_file():
            merged = {**merged, **load_yaml_simple(page_content_example)}
    portal_id = str(merged.get("portalId") or "").strip()
    target_template = normalize_template_path(str(merged.get("targetTemplatePath") or ""))
    return {
        **merged,
        "portalId": portal_id,
        "targetTemplatePath": target_template,
        "configPath": str(config_path()),
        "configExists": config_path().is_file(),
    }


def normalize_template_path(path: str) -> str:
    path = (path or "").strip()
    while path.startswith("/"):
        path = path[1:]
    return path


def pages_api(page_type: str) -> str:
    if page_type == "landing-page":
        return LANDING_PAGES_API
    if page_type == "site-page":
        return SITE_PAGES_API
    raise SystemExit(f"Unknown pageType: {page_type}. Use site-page or landing-page.")


def app_base_url(portal_id: str, cfg: dict[str, Any]) -> str:
    override = str(cfg.get("appBaseUrl") or "").strip()
    if override:
        return override.rstrip("/")
    region = str(cfg.get("hubspotRegion") or "na1").strip()
    if region.startswith("na2"):
        return f"https://app-na2.hubspot.com"
    return "https://app.hubspot.com"


def editor_url(page_id: str, page_type: str, cfg: dict[str, Any] | None = None) -> str:
    config = cfg or load_config()
    portal_id = str(config.get("portalId") or require_oauth_session().get("hubId") or "").strip()
    if not portal_id:
        raise SystemExit("portalId missing in config.yaml and OAuth hubId unavailable.")
    base = app_base_url(portal_id, config)
    content_path = "landing-pages" if page_type == "landing-page" else "website-pages"
    return f"{base}/website/{portal_id}/pages/{content_path}/{page_id}/edit"


def cmd_get_config(_args: argparse.Namespace) -> None:
    cfg = load_config()
    auth = auth_status()
    print(
        json.dumps(
            {
                "config": cfg,
                "auth": auth,
                "readyToWork": bool(
                    (auth.get("readyToStage") or cfg.get("allowPrivateAppToken"))
                    and cfg.get("targetTemplatePath")
                ),
                "setupChecklist": _setup_checklist(cfg, auth),
            },
            indent=2,
        )
    )


def _setup_checklist(cfg: dict[str, Any], auth: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if not auth.get("oauthConnected"):
        items.append("Run hubspot_pages login (OAuth) on this machine.")
    if not cfg.get("configExists"):
        items.append("Copy config.example.yaml to config.yaml in .agents/skills/hubspot-pages/.")
    if not cfg.get("portalId"):
        items.append("Set portalId in config.yaml (Hub ID, e.g. 7718689).")
    if not cfg.get("targetTemplatePath"):
        items.append("Set targetTemplatePath — copy from Design Manager (no leading slash).")
    return items


def cmd_auth_status(_args: argparse.Namespace) -> None:
    print(json.dumps(auth_status(), indent=2))


def cmd_login(args: argparse.Namespace) -> None:
    load_dotenv()
    result = login(open_browser=not args.no_browser)
    print(json.dumps(result, indent=2))


def cmd_logout(_args: argparse.Namespace) -> None:
    print(json.dumps(logout(), indent=2))


def cmd_list_templates(args: argparse.Namespace) -> None:
    params: dict[str, str] = {"limit": str(args.limit)}
    if args.search:
        params["path"] = args.search
    query = urllib.parse.urlencode(params)
    data = hubspot_request("GET", f"{TEMPLATES_API}?{query}")
    results = data.get("objects", data.get("results", data)) if isinstance(data, dict) else data
    templates = []
    for item in results or []:
        if not isinstance(item, dict):
            continue
        path = normalize_template_path(str(item.get("path") or ""))
        if args.search and args.search.lower() not in path.lower():
            label = str(item.get("label") or item.get("title") or "")
            if args.search.lower() not in label.lower():
                continue
        templates.append(
            {
                "id": item.get("id"),
                "path": path,
                "label": item.get("label") or item.get("title"),
                "category": item.get("category"),
                "isAvailableForNewContent": item.get("is_available_for_new_content")
                if "is_available_for_new_content" in item
                else item.get("isAvailableForNewContent"),
            }
        )
    print(json.dumps({"total": len(templates), "templates": templates}, indent=2))


def cmd_list_pages(args: argparse.Namespace) -> None:
    params: dict[str, str] = {"limit": str(args.limit)}
    if args.state:
        params["state__in"] = args.state
    if args.name_contains:
        params["name__contains"] = args.name_contains
    if args.slug:
        params["slug__eq"] = args.slug
    query = urllib.parse.urlencode(params)
    api = pages_api(args.page_type)
    data = hubspot_request("GET", f"{api}?{query}")
    rows = []
    for item in data.get("results", []) if isinstance(data, dict) else []:
        rows.append(_page_summary(item, args.page_type))
    print(json.dumps({"total": data.get("total", len(rows)), "pages": rows}, indent=2))


def _page_summary(item: dict[str, Any], page_type: str) -> dict[str, Any]:
    cfg = load_config()
    page_id = str(item.get("id") or "")
    return {
        "id": page_id,
        "name": item.get("name"),
        "slug": item.get("slug"),
        "url": item.get("url"),
        "state": item.get("state") or item.get("currentState"),
        "templatePath": normalize_template_path(str(item.get("templatePath") or "")),
        "htmlTitle": item.get("htmlTitle"),
        "updatedAt": item.get("updatedAt") or item.get("updated"),
        "editorUrl": editor_url(page_id, page_type, cfg) if page_id else None,
    }


def cmd_get_page(args: argparse.Namespace) -> None:
    api = pages_api(args.page_type)
    item = hubspot_request("GET", f"{api}/{args.page_id}")
    cfg = load_config()
    backup_dir = repo_root() / "_pages" / "staging" / args.page_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"page-backup-{stamp}.json"
    backup_path.write_text(json.dumps(item, indent=2), encoding="utf-8")
    summary = _page_summary(item if isinstance(item, dict) else {}, args.page_type)
    summary["backupPath"] = str(backup_path)
    print(json.dumps(summary, indent=2))


def _find_page_by_slug(slug: str, page_type: str) -> dict[str, Any] | None:
    api = pages_api(page_type)
    query = urllib.parse.urlencode({"slug__eq": slug, "limit": "5"})
    data = hubspot_request("GET", f"{api}?{query}")
    results = data.get("results", []) if isinstance(data, dict) else []
    return results[0] if results else None


def cmd_migrate_template(args: argparse.Namespace) -> None:
    cfg = load_config()
    template_path = normalize_template_path(args.template_path or cfg.get("targetTemplatePath") or "")
    if not template_path:
        raise SystemExit("templatePath required (flag or config targetTemplatePath).")

    page_id = args.page_id
    page_type = args.page_type
    if not page_id:
        if not args.slug:
            raise SystemExit("Provide --page-id or --slug.")
        found = _find_page_by_slug(args.slug, page_type)
        if not found:
            raise SystemExit(f"No {page_type} found with slug '{args.slug}'.")
        page_id = str(found.get("id"))

    api = pages_api(page_type)
    current = hubspot_request("GET", f"{api}/{page_id}")
    if not isinstance(current, dict):
        raise SystemExit(f"Unexpected response fetching page {page_id}")

    backup_dir = repo_root() / "_pages" / "staging" / page_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"pre-migrate-{stamp}.json"
    backup_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    current_template = normalize_template_path(str(current.get("templatePath") or ""))
    if current_template == template_path:
        print(
            json.dumps(
                {
                    "status": "unchanged",
                    "pageId": page_id,
                    "templatePath": template_path,
                    "message": "Page already uses target template.",
                    "editorUrl": editor_url(page_id, page_type, cfg),
                },
                indent=2,
            )
        )
        return

    payload = {"templatePath": template_path}
    state = str(current.get("state") or current.get("currentState") or "").upper()
    if state in {"PUBLISHED", "PUBLISHED_OR_SCHEDULED", "SCHEDULED"}:
        updated = hubspot_request("PATCH", f"{api}/{page_id}/draft", payload)
        endpoint = "draft"
    else:
        updated = hubspot_request("PATCH", f"{api}/{page_id}", payload)
        endpoint = "page"

    print(
        json.dumps(
            {
                "status": "migrated",
                "pageId": page_id,
                "pageType": page_type,
                "previousTemplatePath": current_template,
                "templatePath": template_path,
                "endpointUsed": endpoint,
                "backupPath": str(backup_path),
                "editorUrl": editor_url(page_id, page_type, cfg),
                "nextSteps": [
                    "Open the editor URL and rebuild module content for the new template.",
                    "Review SEO fields (htmlTitle, metaDescription) after template change.",
                    "Publish only after explicit human approval.",
                ],
                "page": _page_summary(updated if isinstance(updated, dict) else current, page_type),
            },
            indent=2,
        )
    )


def cmd_create_page(args: argparse.Namespace) -> None:
    cfg = load_config()
    template_path = normalize_template_path(args.template_path or cfg.get("targetTemplatePath") or "")
    if not template_path:
        raise SystemExit("templatePath required (flag or config targetTemplatePath).")
    if not args.name:
        raise SystemExit("--name is required.")

    payload: dict[str, Any] = {
        "name": args.name,
        "templatePath": template_path,
        "state": "DRAFT",
    }
    if args.slug:
        payload["slug"] = args.slug
    if args.html_title:
        payload["htmlTitle"] = args.html_title
    if args.meta_description:
        payload["metaDescription"] = args.meta_description
    if args.domain:
        payload["domain"] = args.domain
    elif cfg.get("defaultDomain"):
        payload["domain"] = cfg.get("defaultDomain")

    if args.layout_file:
        layout = json.loads(Path(args.layout_file).read_text(encoding="utf-8"))
        payload["layoutSections"] = layout
    elif args.layout_json:
        payload["layoutSections"] = json.loads(args.layout_json)

    api = pages_api(args.page_type)
    created = hubspot_request("POST", api, payload)
    page_id = str(created.get("id") if isinstance(created, dict) else "")
    print(
        json.dumps(
            {
                "status": "created",
                "pageType": args.page_type,
                "page": _page_summary(created if isinstance(created, dict) else {}, args.page_type),
                "editorUrl": editor_url(page_id, args.page_type, cfg) if page_id else None,
            },
            indent=2,
        )
    )


def cmd_update_page(args: argparse.Namespace) -> None:
    cfg = load_config()
    api = pages_api(args.page_type)
    payload: dict[str, Any] = {}
    for field, arg_name, key in (
        ("name", "name", "name"),
        ("slug", "slug", "slug"),
        ("html_title", "html_title", "htmlTitle"),
        ("meta_description", "meta_description", "metaDescription"),
        ("template_path", "template_path", "templatePath"),
    ):
        value = getattr(args, arg_name, None)
        if value:
            payload[key] = normalize_template_path(value) if key == "templatePath" else value

    if not payload:
        raise SystemExit("Provide at least one field to update.")

    current = hubspot_request("GET", f"{api}/{args.page_id}")
    state = str(current.get("state") or current.get("currentState") or "").upper() if isinstance(current, dict) else ""
    if state in {"PUBLISHED", "PUBLISHED_OR_SCHEDULED", "SCHEDULED"}:
        updated = hubspot_request("PATCH", f"{api}/{args.page_id}/draft", payload)
        endpoint = "draft"
    else:
        updated = hubspot_request("PATCH", f"{api}/{args.page_id}", payload)
        endpoint = "page"

    print(
        json.dumps(
            {
                "status": "updated",
                "endpointUsed": endpoint,
                "page": _page_summary(updated if isinstance(updated, dict) else {}, args.page_type),
                "editorUrl": editor_url(args.page_id, args.page_type, cfg),
            },
            indent=2,
        )
    )


def cmd_publish_page(args: argparse.Namespace) -> None:
    if not args.confirm:
        raise SystemExit(
            "Publishing requires --confirm. Only call after the user explicitly approves publish."
        )
    api = pages_api(args.page_type)
    result = hubspot_request("POST", f"{api}/{args.page_id}/publish")
    cfg = load_config()
    print(
        json.dumps(
            {
                "status": "published",
                "pageId": args.page_id,
                "editorUrl": editor_url(args.page_id, args.page_type, cfg),
                "result": result,
            },
            indent=2,
        )
    )


def inventory_path(custom: str | None = None) -> Path:
    if custom:
        return Path(custom).expanduser()
    default = repo_root() / "_pages" / "inventory" / "pages.inventory.json"
    if not default.is_file():
        yaml_default = repo_root() / "_pages" / "inventory" / "pages.inventory.yaml"
        if yaml_default.is_file():
            return yaml_default
    return default


def cmd_get_page_brief(args: argparse.Namespace) -> None:
    topic = (args.topic or "").strip()
    if not topic:
        raise SystemExit("--topic is required.")
    cfg = load_config()
    brief = page_brief_for_topic(topic, cfg)
    brief["suggestedCampaign"] = slugify(topic)
    print(json.dumps(brief, indent=2))


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80] or "page"


def _list_pages_for_linking(page_type: str = "site-page", limit: int = 100) -> list[dict[str, Any]]:
    api = pages_api(page_type)
    query = urllib.parse.urlencode({"limit": str(limit)})
    data = hubspot_request("GET", f"{api}?{query}")
    rows = []
    for item in data.get("results", []) if isinstance(data, dict) else []:
        rows.append(_page_summary(item, page_type))
    return rows


def cmd_stage_page(args: argparse.Namespace) -> None:
    cfg = load_config()
    if args.package_file:
        package = json.loads(Path(args.package_file).read_text(encoding="utf-8"))
    elif args.package_json:
        package = json.loads(args.package_json)
    else:
        raise SystemExit("--package-json or --package-file required")

    package = normalize_package(package, cfg)
    package["internalLinks"] = discover_internal_links(
        package["topic"],
        lambda: _list_pages_for_linking(),
        existing=package.get("internalLinks"),
    )

    if args.dry_run:
        images = {
            "hero": {"url": None, "source": "skipped-dry-run"},
            "section1": {"url": None, "source": "skipped-dry-run"},
            "section2": {"url": None, "source": "skipped-dry-run"},
        }
    else:
        from page_content import _import_hubspot_content_helpers

        campaign_slug = _import_hubspot_content_helpers()[0](str(package.get("slug") or package["topic"]))
        images = resolve_page_images(package, campaign_slug)
    package["_images"] = images

    blueprint_applied = apply_package_to_blueprint(
        str(package.get("pageKind") or "standard"),
        package,
        images,
    )
    payload = build_create_payload(package, blueprint_applied, cfg)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry-run",
                    "pageKind": package.get("pageKind"),
                    "slug": package.get("slug"),
                    "templatePath": package.get("templatePath"),
                    "htmlTitle": package.get("htmlTitle"),
                    "metaDescription": package.get("metaDescription"),
                    "internalLinks": package.get("internalLinks"),
                    "images": images,
                    "widgetCount": len(
                        (payload.get("widgetContainers") or {})
                        .get(next(iter(payload.get("widgetContainers") or {"x": {}}), "x"), {})
                        .get("widgets", [])
                    ),
                    "faqCount": len(package.get("faqs") or []),
                },
                indent=2,
            )
        )
        return

    api = pages_api("site-page")
    created = hubspot_request("POST", api, payload)
    page_id = str(created.get("id") if isinstance(created, dict) else "")
    editor = editor_url(page_id, "site-page", cfg) if page_id else None
    result = {
        "status": "staged",
        "pageType": "site-page",
        "page": _page_summary(created if isinstance(created, dict) else {}, "site-page"),
        "editorUrl": editor,
        "images": images,
        "internalLinks": package.get("internalLinks"),
    }
    review_path = write_review_md(package, result, repo_root() / "_pages" / "staging")
    result["reviewPath"] = str(review_path)
    print(json.dumps(result, indent=2))


def cmd_run_inventory(args: argparse.Namespace) -> None:
    path = inventory_path(args.inventory_file)
    if not path.is_file():
        raise SystemExit(
            f"Inventory file not found: {path}. Copy pages.inventory.example.yaml and fill it in."
        )
    inv = load_inventory(path)
    cfg = load_config()
    target_template = normalize_template_path(
        str(inv.get("targetTemplatePath") or cfg.get("targetTemplatePath") or "")
    )
    page_type = str(inv.get("pageType") or cfg.get("defaultPageType") or "site-page")
    dry_run = bool(args.dry_run)

    results: dict[str, Any] = {
        "inventoryPath": str(path),
        "targetTemplatePath": target_template,
        "pageType": page_type,
        "dryRun": dry_run,
        "migrate": [],
        "create": [],
        "skipped": [],
    }

    for item in inv.get("migrate") or []:
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug") or "").strip()
        page_id = str(item.get("pageId") or "").strip()
        entry = {"slug": slug, "pageId": page_id, "notes": item.get("notes")}
        if dry_run:
            entry["action"] = "migrate-template"
            entry["templatePath"] = normalize_template_path(
                str(item.get("templatePath") or target_template)
            )
            results["migrate"].append(entry)
            continue
        migrate_args = argparse.Namespace(
            page_id=page_id or None,
            slug=slug or None,
            page_type=page_type,
            template_path=normalize_template_path(str(item.get("templatePath") or target_template)),
        )
        try:
            if not migrate_args.page_id and not migrate_args.slug:
                results["skipped"].append({**entry, "reason": "missing slug and pageId"})
                continue
            api = pages_api(page_type)
            if not migrate_args.page_id:
                found = _find_page_by_slug(migrate_args.slug or "", page_type)
                if not found:
                    results["skipped"].append({**entry, "reason": "slug not found"})
                    continue
                migrate_args.page_id = str(found.get("id"))
            current = hubspot_request("GET", f"{api}/{migrate_args.page_id}")
            payload = {"templatePath": migrate_args.template_path}
            state = str(current.get("state") or current.get("currentState") or "").upper()
            if state in {"PUBLISHED", "PUBLISHED_OR_SCHEDULED", "SCHEDULED"}:
                hubspot_request("PATCH", f"{api}/{migrate_args.page_id}/draft", payload)
            else:
                hubspot_request("PATCH", f"{api}/{migrate_args.page_id}", payload)
            entry["status"] = "migrated"
            entry["editorUrl"] = editor_url(migrate_args.page_id, page_type, cfg)
            results["migrate"].append(entry)
        except SystemExit as exc:
            entry["status"] = "error"
            entry["error"] = str(exc)
            results["migrate"].append(entry)

    for item in inv.get("create") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        entry = {"name": name, "slug": item.get("slug"), "notes": item.get("notes")}
        if dry_run:
            entry["action"] = "create-draft"
            entry["templatePath"] = normalize_template_path(
                str(item.get("templatePath") or target_template)
            )
            results["create"].append(entry)
            continue
        if not name:
            results["skipped"].append({**entry, "reason": "missing name"})
            continue
        create_args = argparse.Namespace(
            name=name,
            slug=str(item.get("slug") or "").strip() or None,
            html_title=item.get("htmlTitle"),
            meta_description=item.get("metaDescription"),
            domain=item.get("domain") or cfg.get("defaultDomain"),
            template_path=normalize_template_path(str(item.get("templatePath") or target_template)),
            page_type=page_type,
            layout_file=None,
            layout_json=None,
        )
        try:
            api = pages_api(page_type)
            payload: dict[str, Any] = {
                "name": create_args.name,
                "templatePath": create_args.template_path,
                "state": "DRAFT",
            }
            if create_args.slug:
                payload["slug"] = create_args.slug
            if create_args.html_title:
                payload["htmlTitle"] = create_args.html_title
            if create_args.meta_description:
                payload["metaDescription"] = create_args.meta_description
            if create_args.domain:
                payload["domain"] = create_args.domain
            created = hubspot_request("POST", api, payload)
            page_id = str(created.get("id") if isinstance(created, dict) else "")
            entry["status"] = "created"
            entry["pageId"] = page_id
            entry["editorUrl"] = editor_url(page_id, page_type, cfg) if page_id else None
            results["create"].append(entry)
        except SystemExit as exc:
            entry["status"] = "error"
            entry["error"] = str(exc)
            results["create"].append(entry)

    summary_path = repo_root() / "_pages" / "staging" / "inventory-run-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    results["summaryPath"] = str(summary_path)
    print(json.dumps(results, indent=2))


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="HubSpot CMS pages — draft-first tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("get-config", help="Read portal config + auth readiness").set_defaults(
        func=cmd_get_config
    )
    sub.add_parser("auth-status", help="OAuth connection status").set_defaults(func=cmd_auth_status)
    p_login = sub.add_parser("login", help="Connect HubSpot OAuth")
    p_login.add_argument("--no-browser", action="store_true")
    p_login.set_defaults(func=cmd_login)
    sub.add_parser("logout", help="Remove OAuth token").set_defaults(func=cmd_logout)

    p_templates = sub.add_parser("list-templates", help="List CMS templates")
    p_templates.add_argument("--search", help="Filter template path contains")
    p_templates.add_argument("--limit", type=int, default=100)
    p_templates.set_defaults(func=cmd_list_templates)

    p_list = sub.add_parser("list-pages", help="List site or landing pages")
    p_list.add_argument("--page-type", default="site-page", choices=["site-page", "landing-page"])
    p_list.add_argument("--state", help="e.g. DRAFT, PUBLISHED_OR_SCHEDULED")
    p_list.add_argument("--name-contains")
    p_list.add_argument("--slug")
    p_list.add_argument("--limit", type=int, default=50)
    p_list.set_defaults(func=cmd_list_pages)

    p_get = sub.add_parser("get-page", help="Fetch page + write JSON backup")
    p_get.add_argument("--page-id", required=True)
    p_get.add_argument("--page-type", default="site-page", choices=["site-page", "landing-page"])
    p_get.set_defaults(func=cmd_get_page)

    p_migrate = sub.add_parser("migrate-template", help="Change page templatePath")
    p_migrate.add_argument("--page-id")
    p_migrate.add_argument("--slug")
    p_migrate.add_argument("--template-path")
    p_migrate.add_argument("--page-type", default="site-page", choices=["site-page", "landing-page"])
    p_migrate.set_defaults(func=cmd_migrate_template)

    p_create = sub.add_parser("create-page", help="Create DRAFT page")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--slug")
    p_create.add_argument("--html-title")
    p_create.add_argument("--meta-description")
    p_create.add_argument("--domain")
    p_create.add_argument("--template-path")
    p_create.add_argument("--layout-json")
    p_create.add_argument("--layout-file")
    p_create.add_argument("--page-type", default="site-page", choices=["site-page", "landing-page"])
    p_create.set_defaults(func=cmd_create_page)

    p_update = sub.add_parser("update-page", help="Update page metadata (draft endpoint when live)")
    p_update.add_argument("--page-id", required=True)
    p_update.add_argument("--name")
    p_update.add_argument("--slug")
    p_update.add_argument("--html-title")
    p_update.add_argument("--meta-description")
    p_update.add_argument("--template-path")
    p_update.add_argument("--page-type", default="site-page", choices=["site-page", "landing-page"])
    p_update.set_defaults(func=cmd_update_page)

    p_publish = sub.add_parser("publish-page", help="Publish page — requires explicit --confirm")
    p_publish.add_argument("--page-id", required=True)
    p_publish.add_argument("--page-type", default="site-page", choices=["site-page", "landing-page"])
    p_publish.add_argument("--confirm", action="store_true")
    p_publish.set_defaults(func=cmd_publish_page)

    p_inv = sub.add_parser("run-inventory", help="Process pages.inventory.yaml migrate + create lists")
    p_inv.add_argument("--inventory-file")
    p_inv.add_argument("--dry-run", action="store_true")
    p_inv.set_defaults(func=cmd_run_inventory)

    p_page_brief = sub.add_parser(
        "get-page-brief",
        help="Return AEO page composition schema + template/slug suggestions for a topic",
    )
    p_page_brief.add_argument("--topic", required=True)
    p_page_brief.set_defaults(func=cmd_get_page_brief)

    p_stage_page = sub.add_parser(
        "stage-page",
        help="Stage a DRAFT site page from a composed AEO page package JSON",
    )
    p_stage_page.add_argument("--package-json")
    p_stage_page.add_argument("--package-file")
    p_stage_page.add_argument("--dry-run", action="store_true")
    p_stage_page.set_defaults(func=cmd_stage_page)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
