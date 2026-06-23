#!/usr/bin/env python3
"""HubSpot content staging: blog drafts, marketing email drafts, social copy files.

Draft-only — no publish, send, or schedule endpoints are exposed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HUBSPOT_API = "https://api.hubapi.com"
BLOG_API = f"{HUBSPOT_API}/cms/blogs/2026-03/posts"
EMAIL_API = f"{HUBSPOT_API}/marketing/emails/2026-03"

SKILL_DIR = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "hubspot-content"

# Vixxo Brand Guidelines 2026 — imagery style (Breeze prompt suffix)
BREEZE_IMAGERY_STYLE = (
    "Editorial photo-journalistic style, authentic and caught in the moment, not staged. "
    "Bright inviting natural lighting. Clear optimistic focal point. "
    "Simple composition leaving room for headline overlay. "
    "Modern straightforward journalistic tone for business audience. "
    "Commercial facilities management context, not residential."
)

BREEZE_UI_STEPS = [
    "Open the staged asset in HubSpot editor (blog post, marketing email, or File Manager).",
    "Click the image module or Select image.",
    "Choose Generate with AI (HubSpot Breeze).",
    "Paste the breezePrompt from the agent output.",
    "Generate, review, then Save to files.",
    "Confirm the image is inserted (featured image, email header, or social attachment).",
]

CHANNEL_SPECS = {
    "blog_featured": {
        "label": "Blog featured image",
        "aspect": "Wide horizontal hero, 16:9, space for headline above or below subject",
        "hubspotSurface": "Blog post editor > Featured image",
    },
    "email_header": {
        "label": "Email header banner",
        "aspect": "Wide email banner, approximately 600px wide composition",
        "hubspotSurface": "Marketing email editor > Header image module",
    },
    "social": {
        "label": "Social post image",
        "aspect": "Square or 1.91:1 social feed composition, strong single focal point",
        "hubspotSurface": "Marketing > Social > Create post > Add image > Generate with AI",
    },
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


def hubspot_token() -> str:
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "HUBSPOT_ACCESS_TOKEN is required. Add a Private App token with "
            "content scope (optional files) to .env."
        )
    return token


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


LIST_CHILD_KEYS = frozenset({"memoryPaths", "defaultPlatforms", "avoid"})


def load_yaml_simple(path: Path) -> dict:
    """Minimal YAML reader for config files (no PyYAML dependency)."""
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
            parent.append(line[2:].strip().strip("'\""))
            continue

        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if not value:
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

        if value in ("null", "~"):
            parsed: Any = None
        elif value.startswith('"') and value.endswith('"'):
            parsed = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            parsed = value[1:-1]
        else:
            parsed = value

        if isinstance(parent, dict):
            parent[key] = parsed
    return result


def load_config() -> dict:
    for name in ("config.yaml", "config.yml"):
        path = SKILL_DIR / name
        if path.is_file():
            return load_yaml_simple(path)
    example = SKILL_DIR / "config.example.yaml"
    if example.is_file():
        cfg = load_yaml_simple(example)
        cfg["_source"] = "config.example.yaml (copy to config.yaml and fill in IDs)"
        return cfg
    return {}


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80] or "content"


_UI_DOMAIN_CACHE: str | None = None


def hubspot_app_base_url(cfg: dict | None = None) -> str:
    """Resolve HubSpot app host (e.g. app-na2.hubspot.com) from config or account info."""
    global _UI_DOMAIN_CACHE
    cfg = cfg or {}
    app_base = str(cfg.get("appBaseUrl") or "").strip().rstrip("/")
    if app_base:
        return app_base if app_base.startswith("http") else f"https://{app_base}"

    region = str(cfg.get("hubspotRegion") or "").strip().lower()
    if region:
        region = region.removeprefix("https://").removeprefix("app-").removesuffix(".hubspot.com")
        return f"https://app-{region}.hubspot.com"

    if _UI_DOMAIN_CACHE:
        return f"https://{_UI_DOMAIN_CACHE}"

    try:
        load_dotenv()
        details = hubspot_request("GET", f"{HUBSPOT_API}/account-info/v3/details")
        domain = str(details.get("uiDomain") or "app.hubspot.com")
        _UI_DOMAIN_CACHE = domain
        return f"https://{domain}"
    except Exception:
        return "https://app.hubspot.com"


def blog_post_body_widget(html: str) -> dict[str, Any]:
    """Rich-text widget required by the HubSpot blog editor to render draft content."""
    return {
        "id": "post_body",
        "label": "Blog Content",
        "name": "post_body",
        "type": "rich_text",
        "body": {"html": html},
    }


def sync_blog_post_widgets(post_id: str, html: str) -> dict[str, Any]:
    """Ensure postBody and the post_body widget stay in sync for the blog editor UI."""
    draft = hubspot_request("GET", f"{BLOG_API}/{post_id}/draft")
    widgets = dict(draft.get("widgets") or {})
    widgets["post_body"] = blog_post_body_widget(html)
    return hubspot_request(
        "PATCH",
        f"{BLOG_API}/{post_id}",
        {"postBody": html, "widgets": widgets, "state": "DRAFT"},
    )


def blog_editor_url(portal_id: str, post_id: str, cfg: dict | None = None) -> str:
    """Direct blog post editor. Use /editor/{postId}, not /editor/post/{postId}."""
    base = hubspot_app_base_url(cfg)
    if portal_id:
        return f"{base}/blog/{portal_id}/editor/{post_id}"
    return f"{base}/blog/editor/{post_id}"


def blog_editor_fallback_url(portal_id: str, post_id: str, cfg: dict | None = None) -> str:
    """Drafts list when the direct editor link fails (open post by title)."""
    return blog_drafts_list_url(portal_id, cfg)


def email_editor_url(portal_id: str, email_id: str, cfg: dict | None = None) -> str:
    base = hubspot_app_base_url(cfg)
    if portal_id:
        return f"{base}/email/{portal_id}/edit/{email_id}"
    return f"{base}/email/edit/{email_id}"


def blog_drafts_list_url(portal_id: str, cfg: dict | None = None) -> str:
    base = hubspot_app_base_url(cfg)
    return f"{base}/blog/{portal_id}/manage/posts/drafts"


def social_ui_url(portal_id: str, cfg: dict | None = None) -> str:
    base = hubspot_app_base_url(cfg)
    if portal_id:
        return f"{base}/social/{portal_id}/"
    return f"{base}/social/"


def render_review_doc(
    *,
    title: str,
    campaign_slug: str,
    blog_editor_url_value: str,
    email_editor_url_value: str,
    social_copy_path: str,
    social_image_url: str,
    social_ui_url_value: str,
) -> str:
    template_path = SKILL_DIR / "templates" / "REVIEW.template.md"
    template = template_path.read_text(encoding="utf-8")
    return template.format(
        title=title,
        campaign_slug=campaign_slug,
        blog_editor_url=blog_editor_url_value,
        email_editor_url=email_editor_url_value,
        social_copy_path=social_copy_path,
        social_image_url=social_image_url,
        social_ui_url=social_ui_url_value,
    )


DEFAULT_BLOG_HERO_IMAGE = (
    "https://7718689.fs1.hubspotusercontent-na2.net/hubfs/7718689/"
    "IMAGES/HVAC/Vixxo-Facilities-Management-HVAC-1173822860-600.jpg"
)


def blog_hero_html(image_url: str, alt: str = "") -> str:
    alt_attr = alt.replace('"', "&quot;")
    return (
        f'<figure style="margin:0 0 24px 0;">'
        f'<img src="{image_url}" alt="{alt_attr}" '
        f'style="width:100%;max-width:100%;height:auto;display:block;" />'
        f"</figure>"
    )


def prepend_blog_hero_image(body: str, image_url: str, *, alt: str = "") -> str:
    body = body.strip()
    if body.startswith("<figure"):
        end = body.find("</figure>")
        if end != -1:
            body = body[end + len("</figure>") :].lstrip()
    return blog_hero_html(image_url, alt) + body


def plain_html_to_email_module_html(html_body: str, preheader: str = "") -> str:
    """Convert simple HTML to HubSpot drag-and-drop email module HTML."""
    return (
        '<p style="margin-bottom:10px;">Hi,</p>'
        + html_body.replace("<h1>", '<p style="margin-bottom:10px;"><strong>').replace(
            "</h1>", "</strong></p>"
        ).replace("<p>", '<p style="margin-bottom:10px;">')
    )


def patch_drag_drop_email_draft(
    email_id: str,
    *,
    subject: str,
    name: str,
    html_body: str,
    preheader: str = "",
) -> dict:
    """Update HubSpot drag-and-drop email draft widgets with campaign HTML."""
    draft = hubspot_request("GET", f"{EMAIL_API}/{email_id}/draft")
    content = draft.get("content") or {}
    widgets = content.get("widgets") or {}
    module_key = next(
        (k for k, v in widgets.items() if isinstance(v, dict) and v.get("body", {}).get("html") is not None),
        "module-0-0-0",
    )
    if module_key in widgets:
        widgets[module_key]["body"]["html"] = plain_html_to_email_module_html(html_body, preheader)
    if "preview_text" in widgets and preheader:
        widgets["preview_text"]["body"]["value"] = preheader
    content["widgets"] = widgets
    return hubspot_request(
        "PATCH",
        f"{EMAIL_API}/{email_id}/draft",
        {"subject": subject, "name": name, "content": content},
    )


def staging_dir(config: dict) -> Path:
    rel = (config.get("staging") or {}).get("directory") or "_content/staging"
    if isinstance(config.get("staging"), str):
        rel = config["staging"]
    return repo_root() / rel


def social_ready_dir(config: dict) -> Path:
    rel = (config.get("social") or {}).get("directory") or "_content/social-ready"
    if not isinstance(config.get("social"), dict):
        rel = "_content/social-ready"
    return repo_root() / rel


def render_social_txt(post: dict) -> str:
    lines = [post.get("copy", "").strip()]
    hashtags = post.get("hashtags")
    if hashtags:
        if isinstance(hashtags, list):
            lines.append("")
            lines.append(" ".join(f"#{t.lstrip('#')}" for t in hashtags))
        else:
            lines.append("")
            lines.append(str(hashtags).strip())
    link = post.get("link")
    if link:
        lines.append(str(link).strip())
    return "\n".join(line for line in lines if line is not None).strip() + "\n"


def build_breeze_prompt(topic: str, channel: str, audience: str = "") -> dict:
    spec = CHANNEL_SPECS.get(channel)
    if not spec:
        raise SystemExit(f"Unknown channel: {channel}. Use blog_featured, email_header, or social.")

    audience_clause = f" Audience: {audience}." if audience else ""
    prompt = (
        f"{topic}.{audience_clause} "
        f"{spec['aspect']}. {BREEZE_IMAGERY_STYLE}"
    ).strip()

    return {
        "channel": channel,
        "label": spec["label"],
        "topic": topic,
        "audience": audience or None,
        "breezePrompt": prompt,
        "altTextSuggestion": topic[:125],
        "hubspotSurface": spec["hubspotSurface"],
        "breezeUiSteps": BREEZE_UI_STEPS,
        "apiNote": (
            "HubSpot Breeze AI image generation has no public API. "
            "Complete image insertion manually in HubSpot UI using the prompt above."
        ),
        "requiredPerAsset": True,
    }


def cmd_breeze_prompt(args: argparse.Namespace) -> None:
    result = build_breeze_prompt(args.topic, args.channel, audience=args.audience or "")
    print(json.dumps(result, indent=2))


def parse_iso_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except ValueError:
        return value[:10] if len(value) >= 10 else value


def cmd_get_config(_args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    missing = []
    if not cfg.get("contentGroupId"):
        missing.append("contentGroupId")
    if not cfg.get("blogAuthorId"):
        missing.append("blogAuthorId")
    out = {
        "config": cfg,
        "configPath": str(SKILL_DIR / "config.yaml"),
        "setupRequired": bool(missing),
        "missingFields": missing,
        "setupInstructions": (
            "Copy .agents/skills/hubspot-content/config.example.yaml to config.yaml "
            "and fill portalId, contentGroupId, blogAuthorId."
            if missing
            else None
        ),
    }
    print(json.dumps(out, indent=2))


def cmd_create_blog_draft(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    content_group = args.content_group_id or cfg.get("contentGroupId")
    author_id = args.blog_author_id or cfg.get("blogAuthorId")
    if not content_group or not author_id:
        raise SystemExit("contentGroupId and blogAuthorId required (config.yaml or CLI flags)")

    body = args.body
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    if not body:
        raise SystemExit("--body or --body-file required")

    hero_url = args.featured_image or DEFAULT_BLOG_HERO_IMAGE
    body = prepend_blog_hero_image(body, hero_url, alt=args.title)

    payload: dict[str, Any] = {
        "name": args.title,
        "htmlTitle": args.title,
        "slug": args.slug or slugify(args.title),
        "contentGroupId": str(content_group),
        "blogAuthorId": str(author_id),
        "metaDescription": args.meta_description,
        "postBody": body,
        "widgets": {"post_body": blog_post_body_widget(body)},
        "featuredImage": hero_url,
        "useFeaturedImage": True,
        "state": "DRAFT",
    }
    if args.publish_date:
        payload["publishDate"] = args.publish_date

    result = hubspot_request("POST", BLOG_API, payload)
    post_id = str(result.get("id", ""))
    if post_id and not ((result.get("widgets") or {}).get("post_body")):
        sync_blog_post_widgets(post_id, body)
    portal_id = str(cfg.get("portalId") or "")
    print(
        json.dumps(
            {
                "postId": post_id,
                "state": result.get("state", "DRAFT"),
                "editorUrl": blog_editor_url(portal_id, post_id, cfg),
                "blogListUrl": blog_drafts_list_url(portal_id, cfg) if portal_id else None,
                "slug": result.get("slug"),
                "draftOnly": True,
            },
            indent=2,
        )
    )


def cmd_update_blog_draft(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    payload: dict[str, Any] = {}
    title = args.title
    if title:
        payload["name"] = title
        payload["htmlTitle"] = title
    if args.meta_description:
        payload["metaDescription"] = args.meta_description
    hero_url = args.featured_image or DEFAULT_BLOG_HERO_IMAGE
    if args.body:
        alt = title or "Blog hero image"
        payload["postBody"] = prepend_blog_hero_image(args.body, hero_url, alt=alt)
        payload["featuredImage"] = hero_url
        payload["useFeaturedImage"] = True
    elif args.featured_image:
        draft = hubspot_request("GET", f"{BLOG_API}/{args.post_id}/draft")
        existing_body = draft.get("postBody") or ""
        alt = title or draft.get("name") or "Blog hero image"
        payload["postBody"] = prepend_blog_hero_image(existing_body, hero_url, alt=alt)
        payload["featuredImage"] = hero_url
        payload["useFeaturedImage"] = True
    if not payload:
        raise SystemExit("At least one of --title, --meta-description, --body, --featured-image required")
    payload["state"] = "DRAFT"
    if "postBody" in payload:
        draft = hubspot_request("GET", f"{BLOG_API}/{args.post_id}/draft")
        widgets = dict(draft.get("widgets") or {})
        widgets["post_body"] = blog_post_body_widget(payload["postBody"])
        payload["widgets"] = widgets

    result = hubspot_request("PATCH", f"{BLOG_API}/{args.post_id}", payload)
    portal_id = str(cfg.get("portalId") or "")
    print(
        json.dumps(
            {
                "postId": str(result.get("id", args.post_id)),
                "state": result.get("state", "DRAFT"),
                "editorUrl": blog_editor_url(portal_id, str(result.get("id", args.post_id)), cfg),
                "draftOnly": True,
            },
            indent=2,
        )
    )


def cmd_create_email_draft(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    email_cfg = cfg.get("email") or {}
    if not isinstance(email_cfg, dict):
        email_cfg = {}

    html_body = args.html_body
    if args.html_body_file:
        html_body = Path(args.html_body_file).read_text(encoding="utf-8")

    payload: dict[str, Any] = {
        "name": args.name,
        "subject": args.subject,
        "preheader": args.preheader or "",
    }
    if html_body:
        payload["html"] = html_body
    folder_id = args.folder_id or email_cfg.get("folderId")
    if folder_id:
        payload["folderId"] = int(folder_id)
    active_domain = args.active_domain or email_cfg.get("activeDomain")
    if active_domain:
        payload["activeDomain"] = active_domain

    result = hubspot_request("POST", EMAIL_API, payload)
    email_id = str(result.get("id", ""))
    portal_id = str(cfg.get("portalId") or "")

    if html_body:
        patch_drag_drop_email_draft(
            email_id,
            subject=args.subject,
            name=args.name,
            html_body=html_body,
            preheader=args.preheader or "",
        )

    print(
        json.dumps(
            {
                "emailId": email_id,
                "name": result.get("name"),
                "editorUrl": email_editor_url(portal_id, email_id, cfg),
                "draftOnly": True,
            },
            indent=2,
        )
    )


def cmd_update_email_draft(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    payload: dict[str, Any] = {}
    if args.subject:
        payload["subject"] = args.subject
    if args.preheader is not None:
        payload["preheader"] = args.preheader
    if args.html_body:
        payload["html"] = args.html_body
    if args.name:
        payload["name"] = args.name
    if not payload:
        raise SystemExit("At least one of --name, --subject, --preheader, --html-body required")

    result = hubspot_request("PATCH", f"{EMAIL_API}/{args.email_id}/draft", payload)
    portal_id = str(cfg.get("portalId") or "")
    print(
        json.dumps(
            {
                "emailId": str(result.get("id", args.email_id)),
                "editorUrl": email_editor_url(portal_id, str(result.get("id", args.email_id)), cfg),
                "draftOnly": True,
            },
            indent=2,
        )
    )


def render_social_markdown(pack: dict) -> str:
    lines = [
        f"# Social staging pack — {pack.get('campaign', 'campaign')}",
        "",
        f"**Target date:** {pack.get('targetDate', 'TBD')}",
        "",
    ]
    if pack.get("relatedBlogId"):
        lines.append(f"**Related blog ID:** {pack['relatedBlogId']}")
    if pack.get("relatedEmailId"):
        lines.append(f"**Related email ID:** {pack['relatedEmailId']}")
    lines.append("")
    lines.append("## Manual scheduling")
    lines.append("HubSpot → Marketing → Social → Create post → paste copy below.")
    lines.append("")
    for post in pack.get("posts") or []:
        platform = (post.get("platform") or "unknown").upper()
        lines.extend(
            [
                f"---",
                f"## {platform}",
                "",
                post.get("copy", ""),
                "",
            ]
        )
        if post.get("hashtags"):
            tags = post["hashtags"]
            if isinstance(tags, list):
                lines.append(" ".join(f"#{t.lstrip('#')}" for t in tags))
                lines.append("")
        if post.get("link"):
            lines.append(f"**Link:** {post['link']}")
            lines.append("")
        breeze = post.get("breezeImage") or {}
        image_prompt = post.get("imagePrompt") or breeze.get("breezePrompt")
        if image_prompt:
            lines.append("**Breeze AI image prompt:**")
            lines.append("")
            lines.append("```")
            lines.append(image_prompt)
            lines.append("```")
            lines.append("")
            lines.append("**Generate in HubSpot:** Marketing > Social > Create post > Add image > **Generate with AI**")
            lines.append("")
    return "\n".join(lines)


def cmd_stage_social_pack(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    if args.posts_file:
        posts = json.loads(Path(args.posts_file).read_text(encoding="utf-8"))
    else:
        posts = json.loads(args.posts_json) if args.posts_json else []
    pack = {
        "campaign": args.campaign,
        "targetDate": args.target_date,
        "posts": posts,
        "relatedBlogId": args.related_blog_id,
        "relatedEmailId": args.related_email_id,
        "stagedAt": datetime.now(timezone.utc).isoformat(),
    }
    date_part = parse_iso_date(args.target_date) or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    campaign_slug = slugify(args.campaign)
    out_dir = staging_dir(cfg) / campaign_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{date_part}-social.json"
    md_path = out_dir / f"{date_part}-social.md"
    json_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    md_path.write_text(render_social_markdown(pack), encoding="utf-8")

    social_dir = social_ready_dir(cfg) / campaign_slug
    social_dir.mkdir(parents=True, exist_ok=True)
    txt_paths: list[str] = []
    for post in posts:
        platform = slugify(post.get("platform") or "post")
        txt_path = social_dir / f"{platform}-post.txt"
        txt_path.write_text(render_social_txt(post), encoding="utf-8")
        txt_paths.append(str(txt_path.relative_to(repo_root())))

    print(
        json.dumps(
            {
                "jsonPath": str(json_path.relative_to(repo_root())),
                "markdownPath": str(md_path.relative_to(repo_root())),
                "socialCopyPaths": txt_paths,
                "postCount": len(posts),
                "manualSchedulingRequired": True,
            },
            indent=2,
        )
    )


def cmd_get_staged_summary(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    portal_id = str(cfg.get("portalId") or "")
    summary: dict[str, Any] = {"assets": [], "draftOnly": True}

    if portal_id:
        summary["blogListUrl"] = blog_drafts_list_url(portal_id, cfg)
    if args.blog_id:
        summary["assets"].append(
            {
                "type": "blog",
                "id": args.blog_id,
                "editorUrl": blog_editor_url(portal_id, args.blog_id, cfg),
                "editorFallbackUrl": blog_editor_fallback_url(portal_id, args.blog_id, cfg),
            }
        )
    if args.email_id:
        summary["assets"].append(
            {
                "type": "email",
                "id": args.email_id,
                "editorUrl": email_editor_url(portal_id, args.email_id, cfg),
            }
        )
    if args.staging_path:
        summary["socialStagingPath"] = args.staging_path
    if args.social_copy_path:
        summary["socialCopyPath"] = args.social_copy_path

    summary["reviewChecklist"] = [
        "Verify copy and links in HubSpot editors",
        "Confirm one Breeze AI image per asset (blog featured, email header, each social post)",
        "For social: schedule manually in HubSpot Social UI",
        "Explicit approval required before publish/send/schedule",
    ]
    summary["breezeImageRequired"] = True
    print(json.dumps(summary, indent=2))


def cmd_write_review_doc(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    portal_id = str(cfg.get("portalId") or "")
    campaign_slug = slugify(args.campaign)

    social_dir = social_ready_dir(cfg) / campaign_slug
    social_dir.mkdir(parents=True, exist_ok=True)

    social_copy = args.social_copy_path
    if not social_copy:
        default_txt = social_dir / "linkedin-post.txt"
        social_copy = str(default_txt.resolve())

    review_path = social_dir / "REVIEW.md"
    title = args.title or args.campaign.replace("-", " ").title()

    body = render_review_doc(
        title=title,
        campaign_slug=campaign_slug,
        blog_editor_url_value=blog_editor_url(portal_id, args.blog_id, cfg),
        email_editor_url_value=email_editor_url(portal_id, args.email_id, cfg),
        social_copy_path=social_copy,
        social_image_url=args.social_image_url,
        social_ui_url_value=social_ui_url(portal_id, cfg),
    )
    review_path.write_text(body, encoding="utf-8")

    print(
        json.dumps(
            {
                "reviewPath": str(review_path.relative_to(repo_root())),
                "reviewAbsolutePath": str(review_path.resolve()),
                "campaign": campaign_slug,
                "blogEditorUrl": blog_editor_url(portal_id, args.blog_id, cfg),
                "emailEditorUrl": email_editor_url(portal_id, args.email_id, cfg),
                "socialCopyPath": social_copy,
                "socialImageUrl": args.social_image_url,
                "socialUiUrl": social_ui_url(portal_id, cfg),
                "draftOnly": True,
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="HubSpot content staging (draft-only)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_cfg = sub.add_parser("get-config")
    p_cfg.set_defaults(func=cmd_get_config)

    p_blog = sub.add_parser("create-blog-draft")
    p_blog.add_argument("--title", required=True)
    p_blog.add_argument("--meta-description", required=True)
    p_blog.add_argument("--body", help="HTML post body")
    p_blog.add_argument("--body-file", help="Path to HTML file for post body")
    p_blog.add_argument("--slug")
    p_blog.add_argument("--featured-image")
    p_blog.add_argument("--publish-date")
    p_blog.add_argument("--content-group-id")
    p_blog.add_argument("--blog-author-id")
    p_blog.set_defaults(func=cmd_create_blog_draft)

    p_blog_up = sub.add_parser("update-blog-draft")
    p_blog_up.add_argument("--post-id", required=True)
    p_blog_up.add_argument("--title")
    p_blog_up.add_argument("--meta-description")
    p_blog_up.add_argument("--body")
    p_blog_up.add_argument("--featured-image")
    p_blog_up.set_defaults(func=cmd_update_blog_draft)

    p_email = sub.add_parser("create-email-draft")
    p_email.add_argument("--name", required=True)
    p_email.add_argument("--subject", required=True)
    p_email.add_argument("--preheader", default="")
    p_email.add_argument("--html-body")
    p_email.add_argument("--html-body-file", help="Path to HTML file for email body")
    p_email.add_argument("--folder-id")
    p_email.add_argument("--active-domain")
    p_email.set_defaults(func=cmd_create_email_draft)

    p_email_up = sub.add_parser("update-email-draft")
    p_email_up.add_argument("--email-id", required=True)
    p_email_up.add_argument("--name")
    p_email_up.add_argument("--subject")
    p_email_up.add_argument("--preheader")
    p_email_up.add_argument("--html-body")
    p_email_up.set_defaults(func=cmd_update_email_draft)

    p_social = sub.add_parser("stage-social-pack")
    p_social.add_argument("--campaign", required=True)
    p_social.add_argument("--target-date")
    p_social.add_argument("--posts-json", help="JSON array of post objects")
    p_social.add_argument("--posts-file", help="Path to JSON file with post array")
    p_social.add_argument("--related-blog-id")
    p_social.add_argument("--related-email-id")
    p_social.set_defaults(func=cmd_stage_social_pack)

    p_sum = sub.add_parser("get-staged-summary")
    p_sum.add_argument("--blog-id")
    p_sum.add_argument("--email-id")
    p_sum.add_argument("--staging-path")
    p_sum.add_argument("--social-copy-path")
    p_sum.set_defaults(func=cmd_get_staged_summary)

    p_review = sub.add_parser("write-review-doc")
    p_review.add_argument("--campaign", required=True)
    p_review.add_argument("--blog-id", required=True)
    p_review.add_argument("--email-id", required=True)
    p_review.add_argument("--social-image-url", required=True)
    p_review.add_argument("--title")
    p_review.add_argument("--social-copy-path")
    p_review.set_defaults(func=cmd_write_review_doc)

    p_breeze = sub.add_parser("breeze-prompt", help="Build HubSpot Breeze AI image prompt for a channel")
    p_breeze.add_argument("--topic", required=True)
    p_breeze.add_argument(
        "--channel",
        required=True,
        choices=["blog_featured", "email_header", "social"],
    )
    p_breeze.add_argument("--audience")
    p_breeze.set_defaults(func=cmd_breeze_prompt)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
