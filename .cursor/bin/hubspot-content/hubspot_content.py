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
import sys
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
CAMPAIGN_IMAGES_DIR = Path(__file__).resolve().parent.parent / "hubspot-campaign-images"
DEFAULT_BREEZE_AUDIENCE = "VP+ multi-site retail facilities management"

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


def sync_blog_post_widgets(
    post_id: str, html: str, featured_image: str | None = None
) -> dict[str, Any]:
    """Ensure postBody and the post_body widget stay in sync for the blog editor UI."""
    draft = hubspot_request("GET", f"{BLOG_API}/{post_id}/draft")
    widgets = dict(draft.get("widgets") or {})
    widgets["post_body"] = blog_post_body_widget(html)
    payload: dict[str, Any] = {"postBody": html, "widgets": widgets, "state": "DRAFT"}
    if featured_image:
        payload["featuredImage"] = featured_image
        payload["useFeaturedImage"] = True
    return hubspot_request("PATCH", f"{BLOG_API}/{post_id}", payload)


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
    breeze_prompts: dict[str, str] | None = None,
    email_banner_url: str = "",
    blog_featured_image_url: str = "",
) -> str:
    template_path = SKILL_DIR / "templates" / "REVIEW.template.md"
    template = template_path.read_text(encoding="utf-8")
    prompts = breeze_prompts or {}
    return template.format(
        title=title,
        campaign_slug=campaign_slug,
        blog_editor_url=blog_editor_url_value,
        email_editor_url=email_editor_url_value,
        social_copy_path=social_copy_path,
        social_image_url=social_image_url,
        social_ui_url=social_ui_url_value,
        email_banner_url=email_banner_url or "_Not staged_",
        blog_featured_image_url=blog_featured_image_url or "_Not staged_",
        blog_breeze_prompt=prompts.get("blog_featured", "_Generate via hubspot_content_breeze_image_prompt_"),
        email_breeze_prompt=prompts.get("email_header", "_Generate via hubspot_content_breeze_image_prompt_"),
        social_breeze_prompt=prompts.get("social", "_Optional — branded 300×300 image already uploaded above._"),
    )


def write_campaign_links_file(
    out_dir: Path,
    *,
    campaign_slug: str,
    portal_id: str,
    cfg: dict,
    blog_id: str,
    email_id: str,
    hero_url: str,
    banner_url: str,
    social_image_url: str,
    social_copy: str,
    review_path: Path,
    image_dpi: int = 150,
) -> Path:
    links_path = out_dir / "campaign-links.json"
    links_path.write_text(
        json.dumps(
            {
                "campaign": campaign_slug,
                "blogId": blog_id,
                "emailId": email_id,
                "blogDraft": blog_editor_url(portal_id, blog_id, cfg),
                "emailDraft": email_editor_url(portal_id, email_id, cfg),
                "blogFeaturedImage": hero_url,
                "emailBanner": banner_url,
                "socialImage": social_image_url,
                "socialCopyPath": social_copy,
                "socialUi": social_ui_url(portal_id, cfg),
                "reviewPath": str(review_path.resolve()),
                "reviewRelativePath": str(review_path.relative_to(repo_root())),
                "imageDpi": image_dpi,
                "draftOnly": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return links_path


def read_campaign_links(campaign_slug: str, cfg: dict | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    portal_id = str(cfg.get("portalId") or "")
    out_dir = staging_dir(cfg) / slugify(campaign_slug)
    links_path = out_dir / "campaign-links.json"
    if links_path.is_file():
        return json.loads(links_path.read_text(encoding="utf-8"))

    manifest_path = out_dir / "staging-manifest.json"
    image_path = out_dir / "image-resolution.json"
    if not manifest_path.is_file():
        raise SystemExit(f"No campaign data found for {campaign_slug} (missing staging-manifest.json)")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    blog_id = str(manifest.get("blogId") or "")
    email_id = str(manifest.get("emailId") or "")
    hero_url = ""
    if image_path.is_file():
        hero_url = str(json.loads(image_path.read_text(encoding="utf-8")).get("url") or "")

    social_dir = social_ready_dir(cfg) / slugify(campaign_slug)
    social_copy = str((social_dir / "linkedin-post.txt").resolve())
    review_path = social_dir / "REVIEW.md"

    banner_url = ""
    social_image_url = ""
    if review_path.is_file():
        review_text = review_path.read_text(encoding="utf-8")
        for line in review_text.splitlines():
            line = line.strip()
            if line.startswith("https://") and "email-header" in line:
                banner_url = line
            if line.startswith("https://") and "linkedin" in line and line.endswith(".png"):
                social_image_url = line

    return {
        "campaign": slugify(campaign_slug),
        "blogId": blog_id,
        "emailId": email_id,
        "blogDraft": blog_editor_url(portal_id, blog_id, cfg) if blog_id else "",
        "emailDraft": email_editor_url(portal_id, email_id, cfg) if email_id else "",
        "blogFeaturedImage": hero_url,
        "emailBanner": banner_url,
        "socialImage": social_image_url,
        "socialCopyPath": social_copy,
        "socialUi": social_ui_url(portal_id, cfg),
        "reviewPath": str(review_path.resolve()) if review_path.is_file() else "",
        "imageDpi": 150,
        "draftOnly": True,
        "assembledFromManifest": True,
    }


def breeze_prompts_for_topic(topic: str, audience: str = "") -> dict[str, str]:
    audience = audience or DEFAULT_BREEZE_AUDIENCE
    return {
        channel: build_breeze_prompt(topic, channel, audience=audience)["breezePrompt"]
        for channel in ("blog_featured", "email_header", "social")
    }


def import_upload_to_hubspot():
    sys.path.insert(0, str(CAMPAIGN_IMAGES_DIR))
    from hubspot_campaign_images import upload_to_hubspot  # noqa: E402

    return upload_to_hubspot


def import_render_photo_at_dpi():
    scripts_dir = SKILL_DIR / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from brand_image import (  # noqa: E402
        BLOG_DISPLAY_HEIGHT,
        BLOG_DISPLAY_WIDTH,
        TARGET_DPI,
        blog_hero_pixel_size,
        render_photo_at_dpi,
    )

    return render_photo_at_dpi, blog_hero_pixel_size, TARGET_DPI, BLOG_DISPLAY_WIDTH, BLOG_DISPLAY_HEIGHT


def import_render_social_card():
    scripts_dir = SKILL_DIR / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from generate_social_image import render_card  # noqa: E402

    return render_card


DEFAULT_BLOG_HERO_IMAGE = (
    "https://7718689.fs1.hubspotusercontent-na2.net/hubfs/7718689/"
    "IMAGES/HVAC/Vixxo-Facilities-Management-HVAC-1173822860-600.jpg"
)

PLUMBING_HERO_IMAGE = (
    "https://www.vixxo.com/hubfs/IMAGES/Plumbing/"
    "Vixxo-Facilities-Management-Plumbing-1129117534-1400.jpg"
)

TRADE_HERO_IMAGES: dict[str, str] = {
    "hvac": DEFAULT_BLOG_HERO_IMAGE,
    "plumbing": PLUMBING_HERO_IMAGE,
    # No verified Vixxo electrical CDN asset — use on-brand HVAC hero instead of unrelated stock IDs
    "electrical": DEFAULT_BLOG_HERO_IMAGE,
}

# Only verified Vixxo CDN URLs — never hardcoded third-party photo IDs (IDs drift to wrong subjects)
TOPIC_IMAGE_KEYWORDS: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (
        ("frozen", "freeze", "burst", "pipe", "plumb", "plumbing", "plumber", "drain", "sewer", "backflow", "leak"),
        PLUMBING_HERO_IMAGE,
        "plumbing_vixxo",
    ),
    (
        ("refriger", "refrigeration", "grocery", "cooler", "cold chain", "walk-in", "compressor", "hvac", "rooftop"),
        DEFAULT_BLOG_HERO_IMAGE,
        "hvac_vixxo",
    ),
)

TRADE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "plumbing": (
        "plumb", "plumbing", "plumber", "pipe", "pipes", "frozen", "freeze", "burst", "drain", "sewer",
        "water", "backflow", "restroom", "fixture", "leak",
    ),
    "hvac": (
        "hvac", "heating", "cooling", "refriger", "refrigeration", "rooftop", "air condition",
        "furnace", "boiler", "ventilation", "compressor",
    ),
    "electrical": (
        "electrical", "electric", "lighting", "panel", "power", "generator",
        "wiring", "breaker", "switchgear",
    ),
}


def topic_keyword_in_text(text: str, keyword: str) -> bool:
    """Whole-word match so 'led' does not match inside 'licensed', etc."""
    return re.search(rf"\b{re.escape(keyword.lower())}\b", text.lower()) is not None


def infer_trade_from_topic(topic: str) -> str:
    """Pick the closest Vixxo trade hero family for a user topic."""
    text = topic.lower()
    scores = {
        trade: sum(1 for kw in keywords if topic_keyword_in_text(text, kw))
        for trade, keywords in TRADE_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "hvac"


def build_visual_topic_from_topic(topic: str, trade: str | None = None) -> str:
    """Editorial FM visual brief for Breeze AI and stock search — derived from user topic."""
    trade = trade or infer_trade_from_topic(topic)
    return (
        f"{topic.strip()}. Commercial facilities management, multi-site retail, "
        f"licensed {trade} tradesperson at work, editorial photo-journalistic, not residential."
    )


def topic_stock_search_query(visual_topic: str) -> str:
    return f"{visual_topic} commercial facilities management editorial photo-journalistic"


def simplify_stock_search_query(topic: str, visual_topic: str, trade: str) -> str:
    """Primary short phrase for stock/Wikimedia search."""
    return stock_search_queries(topic, visual_topic, trade)[0]


def stock_search_queries(topic: str, visual_topic: str, trade: str) -> list[str]:
    """Ordered stock/Wikimedia queries — user topic first, then keyword bundles, then trade default."""
    text = f"{topic} {visual_topic}".lower()
    queries: list[str] = []
    seed = re.sub(r"\s+", " ", (topic or visual_topic.split(".")[0] or "").strip())
    if seed:
        queries.append(f"{seed} commercial {trade}")
    bundles: tuple[tuple[tuple[str, ...], str], ...] = (
        (("led", "lighting", "retrofit", "fixture", "lamp"), "LED lighting commercial building"),
        (("electric", "electrical", "electrician", "panel", "wiring", "breaker"), "commercial electrician light fixture installation"),
        (("frozen", "freeze", "pipe", "plumb", "plumbing", "plumber", "burst", "drain", "sewer"), "commercial plumber pipe repair retail"),
        (("refriger", "refrigeration", "cooler", "walk-in", "cold chain", "grocery"), "commercial refrigeration grocery store"),
        (("seasonal", "readiness", "pre-season", "preseason", "peak summer", "summer"), "commercial HVAC pre-season rooftop inspection retail"),
        (("hvac", "rooftop", "compressor", "air condition", "ventilation"), "commercial HVAC technician rooftop retail"),
    )
    for keywords, query in bundles:
        if any(topic_keyword_in_text(text, kw) for kw in keywords):
            queries.append(query)
    trade_defaults = {
        "electrical": "commercial electrical lighting building interior",
        "plumbing": "commercial plumber pipe repair retail",
        "hvac": "commercial HVAC technician rooftop unit retail",
    }
    queries.append(trade_defaults.get(trade, "commercial facilities management retail"))
    seen: set[str] = set()
    ordered: list[str] = []
    for query in queries:
        q = query.strip()
        if q and q not in seen:
            seen.add(q)
            ordered.append(q)
    return ordered


def pick_topic_keyword_fallback(visual_topic: str, topic: str, trade: str) -> tuple[str, str, str]:
    """Score topic keywords and return the best verified Vixxo fallback URL for the prompt."""
    text = f"{topic} {visual_topic}".lower()
    best_url = TRADE_HERO_IMAGES.get(trade) or DEFAULT_BLOG_HERO_IMAGE
    best_score = 0
    best_label = "trade_fallback"
    best_rule = "none"
    for keywords, url, rule_name in TOPIC_IMAGE_KEYWORDS:
        score = sum(1 for kw in keywords if topic_keyword_in_text(text, kw))
        if score > best_score:
            best_score = score
            best_url = url
            best_label = "vixxo_topic_keyword"
            best_rule = rule_name
    return best_url, best_label if best_score > 0 else "vixxo_trade_fallback", best_rule


def _try_preview_bytes(get_preview, query: str) -> tuple[bytes, str, dict[str, Any]] | None:
    from hubspot_campaign_images import download_bytes  # noqa: E402

    preview = get_preview(query)
    if not preview or not preview.get("preview_url"):
        return None
    content, _ext = download_bytes(preview["preview_url"])
    meta = {
        "previewId": preview.get("image_id"),
        "licenseNote": preview.get("license_note"),
        "searchQueryUsed": query,
    }
    return content, str(preview.get("source") or "stock_preview"), meta


def _try_preview_bytes_for_queries(
    get_preview, queries: list[str]
) -> tuple[bytes, str, dict[str, Any]] | None:
    for query in queries:
        matched = _try_preview_bytes(get_preview, query)
        if matched:
            return matched
    return None


def resolve_topic_hero_image(
    visual_topic: str,
    trade: str,
    campaign_slug: str,
    *,
    topic: str = "",
) -> dict[str, Any]:
    """Resolve a topic-matched hero background at 150 DPI; upload to HubSpot File Manager."""
    load_dotenv()
    breeze_query = topic_stock_search_query(visual_topic)
    search_queries = stock_search_queries(topic, visual_topic, trade)
    query = search_queries[0]
    folder = f"/campaign-images/{campaign_slug}"
    keyword_url, keyword_label, keyword_rule = pick_topic_keyword_fallback(visual_topic, topic, trade)
    fallback = keyword_url
    render_photo_at_dpi, blog_hero_pixel_size, target_dpi, blog_display_w, blog_display_h = (
        import_render_photo_at_dpi()
    )
    pixel_w, pixel_h = blog_hero_pixel_size()

    raw_source: str | bytes = fallback
    source = keyword_label
    stock_meta: dict[str, Any] = {"matchedRule": keyword_rule}
    provider_errors: dict[str, str] = {}

    if str(CAMPAIGN_IMAGES_DIR) not in sys.path:
        sys.path.insert(0, str(CAMPAIGN_IMAGES_DIR))

    if os.environ.get("ADOBE_STOCK_API_KEY", "").strip():
        try:
            from hubspot_campaign_images import resolve_adobe_stock  # noqa: E402

            adobe = resolve_adobe_stock(query, "email_header")
            raw_source = adobe["file_bytes"]
            source = "adobe_stock"
            stock_meta = {"adobeStockId": adobe.get("adobe_stock_id"), "matchedRule": "adobe_stock"}
        except (Exception, SystemExit) as exc:
            provider_errors["adobe"] = type(exc).__name__ + ": " + str(exc)[:120]

    if not source.startswith(("adobe_", "shutterstock", "pexels", "openverse")):
        from hubspot_campaign_images import (  # noqa: E402
            resolve_openverse_preview,
            resolve_pexels_preview,
            resolve_shutterstock_preview,
            resolve_wikimedia_preview,
        )

        for provider_name, resolver in (
            ("shutterstock_preview", resolve_shutterstock_preview),
            ("pexels", resolve_pexels_preview),
            ("wikimedia", resolve_wikimedia_preview),
            ("openverse", resolve_openverse_preview),
        ):
            if provider_name == "shutterstock_preview" and not os.environ.get("SHUTTERSTOCK_API_TOKEN", "").strip():
                continue
            if provider_name == "pexels" and not os.environ.get("PEXELS_API_KEY", "").strip():
                continue
            try:
                matched = _try_preview_bytes_for_queries(resolver, search_queries)
                if matched:
                    raw_source, source, stock_meta = matched[0], matched[1], {**matched[2], "matchedRule": provider_name}
                    break
            except (Exception, SystemExit) as exc:
                provider_errors[provider_name] = type(exc).__name__ + ": " + str(exc)[:120]

    upload_to_hubspot = import_upload_to_hubspot()
    hero_bytes = render_photo_at_dpi(raw_source)
    filename = f"{campaign_slug}-topic-hero-150dpi.jpg"
    uploaded = upload_to_hubspot(hero_bytes, filename, folder_path=folder)
    url = str(uploaded.get("url") or uploaded.get("defaultHostingUrl") or fallback)

    topic_matched = source in {"adobe_stock", "shutterstock_preview", "pexels", "openverse", "wikimedia"}
    result: dict[str, Any] = {
        "visualTopic": visual_topic,
        "searchQuery": query,
        "breezeSearchQuery": breeze_query,
        "source": source,
        "url": url,
        "dpi": target_dpi,
        "displaySize": [blog_display_w, blog_display_h],
        "pixelSize": [pixel_w, pixel_h],
        "fileId": uploaded.get("id"),
        "breezePrompts": breeze_prompts_for_topic(visual_topic),
        "topicMatchedPhoto": topic_matched,
        "breezeRequiredForTopicPhoto": not topic_matched,
        "providerErrors": provider_errors,
        **stock_meta,
    }
    return result


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

    breeze_prompts = None
    if args.visual_topic:
        audience = args.breeze_audience or DEFAULT_BREEZE_AUDIENCE
        breeze_prompts = breeze_prompts_for_topic(args.visual_topic, audience=audience)
    elif args.breeze_prompts_json:
        breeze_prompts = json.loads(args.breeze_prompts_json)

    body = render_review_doc(
        title=title,
        campaign_slug=campaign_slug,
        blog_editor_url_value=blog_editor_url(portal_id, args.blog_id, cfg),
        email_editor_url_value=email_editor_url(portal_id, args.email_id, cfg),
        social_copy_path=social_copy,
        social_image_url=args.social_image_url,
        social_ui_url_value=social_ui_url(portal_id, cfg),
        breeze_prompts=breeze_prompts,
        email_banner_url=args.email_banner_url or "",
        blog_featured_image_url=args.blog_featured_image_url or "",
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
                "breezePromptsIncluded": bool(breeze_prompts),
                "draftOnly": True,
            },
            indent=2,
        )
    )


PACKAGE_BRIEF_SCHEMA: dict[str, Any] = {
    "topic": "User topic prompt (required)",
    "campaign": "Optional slug; auto-generated from topic if omitted",
    "targetDate": "Optional ISO date for social scheduling notes",
    "trade": "Optional — auto-inferred from topic (hvac | plumbing | electrical)",
    "reviewTitle": "Human-readable title for REVIEW.md header",
    "visualTopic": "Optional — auto-generated from topic for Breeze/stock image matching",
    "blog": {
        "title": "Blog post title (sentence case)",
        "metaDescription": "≤155 characters",
        "bodyHtml": "HTML body (h2, p, ul, a — no featured image figure)",
        "slug": "Optional URL slug",
    },
    "email": {
        "name": "Internal HubSpot email name",
        "subject": "Subject line",
        "preheader": "Preview text",
        "htmlBody": "HTML body without Hi, (added automatically)",
        "bannerHeadline": "Short headline on 150 DPI email banner",
    },
    "social": {
        "headline": "Short headline on 300×300 social card",
        "posts": [
            {
                "platform": "linkedin",
                "copy": "Post copy",
                "hashtags": ["FacilitiesManagement"],
                "link": "https://www.vixxo.com/...",
            }
        ],
    },
}


def package_brief_for_topic(topic: str) -> dict[str, Any]:
    suggested_trade = infer_trade_from_topic(topic) if topic else "hvac"
    suggested_visual = build_visual_topic_from_topic(topic, suggested_trade) if topic else ""
    return {
        "topic": topic,
        "audience": DEFAULT_BREEZE_AUDIENCE,
        "suggestedTrade": suggested_trade,
        "suggestedVisualTopic": suggested_visual,
        "brandVoice": {
            "tone": "Professional, concise, evidence-backed. VP+ multi-site retail FM.",
            "avoid": ["residential framing", "hype", "unverified superlatives"],
            "cta": "Spend less. Stress less. One work order at a time.",
        },
        "compositionRules": [
            "Compose all copy before calling stage_content_package.",
            "Email htmlBody must NOT include Hi, — it is injected automatically.",
            "Blog bodyHtml must NOT include a featured-image figure — hero is added at staging.",
            "Social headline: short only, no subheading on the 300×300 card.",
            "trade and visualTopic are optional — auto-inferred from topic at staging if omitted.",
            "Images (blog hero, email banner bg, social card bg) are resolved from the topic.",
            "Preferred: Cursor generates ai-hero-bg.png from visualTopic, then refresh_campaign_images with --bg-file.",
            "Fallback chain: Adobe Stock -> Shutterstock -> Pexels -> Wikimedia -> verified Vixxo trade hero.",
            "Breeze prompts in REVIEW.md always match the topic visual brief.",
            "NEVER publish, send, or schedule HubSpot assets unless the user explicitly requests it.",
        ],
        "imageRules": [
            "Best match: generate hero in Cursor from visualTopic -> save _content/staging/{campaign}/ai-hero-bg.png -> refresh with --bg-file (source: cursor_ai).",
            "Automated stock: Adobe Stock (ADOBE_STOCK_API_KEY) -> Shutterstock -> Pexels -> Wikimedia Commons -> Vixxo trade hero.",
            "Never use hardcoded third-party photo IDs — they drift to wrong subjects.",
            "Cursor should set visualTopic only when a sharper art direction than auto-inference is needed.",
            "All Breeze prompts are generated from the topic visual brief automatically.",
        ],
        "draftOnlyRules": [
            "All HubSpot blog posts and marketing emails must remain DRAFT until explicit user approval.",
            "Use verify-campaign-draft-status to confirm nothing is live before and after staging work.",
            "This MCP exposes no publish, send, or schedule endpoints.",
        ],
        "requiredSchema": PACKAGE_BRIEF_SCHEMA,
        "workflow": [
            "1. User provides a topic.",
            "2. Cursor composes blog, email, and social copy per requiredSchema.",
            "3. Cursor calls hubspot_content_stage_content_package with the full package (topic required; trade/visualTopic optional).",
            "4. Cursor generates topic-matched hero image from visualTopic; saves ai-hero-bg.png; calls hubspot_content_refresh_campaign_images with bgFile.",
            "5. MCP returns REVIEW.md, campaign-links.json, and HubSpot editor URLs (imageSource: cursor_ai or stock provider).",
        ],
        "draftOnly": True,
    }


def cmd_get_package_brief(args: argparse.Namespace) -> None:
    topic = args.topic or ""
    brief = package_brief_for_topic(topic)
    if args.topic:
        brief["suggestedCampaign"] = slugify(args.topic)
    print(json.dumps(brief, indent=2))


def cmd_stage_content_package(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    portal_id = str(cfg.get("portalId") or "")

    if args.package_file:
        bundle = json.loads(Path(args.package_file).read_text(encoding="utf-8"))
    elif args.package_json:
        bundle = json.loads(args.package_json)
    else:
        raise SystemExit("--package-json or --package-file required")

    topic = (bundle.get("topic") or "").strip()
    if not topic:
        raise SystemExit("package.topic is required")

    campaign_slug = slugify(bundle.get("campaign") or topic)
    trade = (bundle.get("trade") or infer_trade_from_topic(topic)).strip().lower()
    if trade not in TRADE_HERO_IMAGES:
        raise SystemExit(f"package.trade must be one of: {', '.join(sorted(TRADE_HERO_IMAGES))}")

    blog = bundle.get("blog") or {}
    email = bundle.get("email") or {}
    social = bundle.get("social") or {}
    posts = social.get("posts") or []

    for section, name in ((blog, "blog"), (email, "email"), (social, "social")):
        if not section:
            raise SystemExit(f"package.{name} is required")

    required_blog = ("title", "metaDescription", "bodyHtml")
    required_email = ("name", "subject", "preheader", "htmlBody", "bannerHeadline")
    for key in required_blog:
        if not blog.get(key):
            raise SystemExit(f"package.blog.{key} is required")
    for key in required_email:
        if not email.get(key):
            raise SystemExit(f"package.email.{key} is required")
    if not posts:
        raise SystemExit("package.social.posts must include at least one post")
    social_headline = social.get("headline") or email.get("bannerHeadline") or blog["title"][:60]

    target_date = bundle.get("targetDate") or bundle.get("target_date")
    review_title = bundle.get("reviewTitle") or campaign_slug.replace("-", " ").title()

    visual_topic = bundle.get("visualTopic") or build_visual_topic_from_topic(topic, trade)
    hero = resolve_topic_hero_image(visual_topic, trade, campaign_slug, topic=topic)
    hero_url = str(hero["url"])
    breeze_prompts = hero.get("breezePrompts") or breeze_prompts_for_topic(
        visual_topic, audience=bundle.get("breezeAudience") or DEFAULT_BREEZE_AUDIENCE
    )

    out_dir = staging_dir(cfg) / campaign_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    blog_path = out_dir / "blog-body.html"
    email_path = out_dir / "email-body.html"
    social_path = out_dir / "social-posts.json"
    blog_path.write_text(blog["bodyHtml"].strip(), encoding="utf-8")
    email_path.write_text(email["htmlBody"].strip(), encoding="utf-8")
    social_path.write_text(json.dumps(posts, indent=2), encoding="utf-8")
    (out_dir / "package.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    # Blog draft
    blog_body = prepend_blog_hero_image(blog["bodyHtml"], hero_url, alt=blog["title"])
    content_group = cfg.get("contentGroupId")
    author_id = cfg.get("blogAuthorId")
    if not content_group or not author_id:
        raise SystemExit("contentGroupId and blogAuthorId required in config.yaml")
    blog_payload: dict[str, Any] = {
        "name": blog["title"],
        "htmlTitle": blog["title"],
        "slug": blog.get("slug") or slugify(blog["title"]),
        "contentGroupId": str(content_group),
        "blogAuthorId": str(author_id),
        "metaDescription": blog["metaDescription"],
        "postBody": blog_body,
        "widgets": {"post_body": blog_post_body_widget(blog_body)},
        "featuredImage": hero_url,
        "useFeaturedImage": True,
        "state": "DRAFT",
    }
    blog_result = hubspot_request("POST", BLOG_API, blog_payload)
    post_id = str(blog_result.get("id", ""))
    if post_id and not ((blog_result.get("widgets") or {}).get("post_body")):
        sync_blog_post_widgets(post_id, blog_body)

    # Email draft (shell — body + banner applied next)
    email_cfg = cfg.get("email") if isinstance(cfg.get("email"), dict) else {}
    email_payload: dict[str, Any] = {
        "name": email["name"],
        "subject": email["subject"],
        "preheader": email.get("preheader") or "",
    }
    if email_cfg.get("folderId"):
        email_payload["folderId"] = int(email_cfg["folderId"])
    if email_cfg.get("activeDomain"):
        email_payload["activeDomain"] = email_cfg["activeDomain"]
    email_result = hubspot_request("POST", EMAIL_API, email_payload)
    email_id = str(email_result.get("id", ""))

    # Email banner + body
    bin_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(bin_dir))
    from attach_email_banner import build_banner, patch_email  # noqa: E402

    upload_to_hubspot = import_upload_to_hubspot()
    banner_bytes = build_banner(hero_url, email["bannerHeadline"])
    banner_filename = f"{campaign_slug}-email-header-v2.jpg"
    banner_upload = upload_to_hubspot(
        banner_bytes,
        banner_filename,
        folder_path=f"/campaign-images/{campaign_slug}",
    )
    banner_url = str(banner_upload.get("url") or banner_upload.get("defaultHostingUrl") or "")
    patch_email(
        email_id,
        banner_url,
        email["bannerHeadline"],
        html_body=email["htmlBody"],
        subject=email["subject"],
        name=email["name"],
        preheader=email.get("preheader") or "",
    )

    # Social copy files
    pack = {
        "campaign": campaign_slug,
        "targetDate": target_date,
        "posts": posts,
        "relatedBlogId": post_id,
        "relatedEmailId": email_id,
        "stagedAt": datetime.now(timezone.utc).isoformat(),
    }
    date_part = parse_iso_date(target_date) or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    staging_campaign_dir = staging_dir(cfg) / campaign_slug
    staging_campaign_dir.mkdir(parents=True, exist_ok=True)
    (staging_campaign_dir / f"{date_part}-social.json").write_text(
        json.dumps(pack, indent=2), encoding="utf-8"
    )
    social_dir = social_ready_dir(cfg) / campaign_slug
    social_dir.mkdir(parents=True, exist_ok=True)
    social_copy_paths: list[str] = []
    for post in posts:
        platform = slugify(post.get("platform") or "post")
        txt_path = social_dir / f"{platform}-post.txt"
        txt_path.write_text(render_social_txt(post), encoding="utf-8")
        social_copy_paths.append(str(txt_path.resolve()))

    # Social image
    render_card = import_render_social_card()
    social_filename = f"{campaign_slug}-linkedin-300x300-v2.png"
    social_local = out_dir / social_filename
    render_card(
        social_headline,
        social_local,
        SKILL_DIR / "assets" / "fonts",
        bg_url=hero_url,
    )
    social_upload = upload_to_hubspot(
        social_local.read_bytes(),
        social_filename,
        folder_path=f"/campaign-images/{campaign_slug}",
    )
    social_image_url = str(social_upload.get("url") or social_upload.get("defaultHostingUrl") or "")

    # REVIEW.md
    social_copy = social_copy_paths[0] if social_copy_paths else str((social_dir / "linkedin-post.txt").resolve())
    review_path = social_dir / "REVIEW.md"
    review_path.write_text(
        render_review_doc(
            title=review_title,
            campaign_slug=campaign_slug,
            blog_editor_url_value=blog_editor_url(portal_id, post_id, cfg),
            email_editor_url_value=email_editor_url(portal_id, email_id, cfg),
            social_copy_path=social_copy,
            social_image_url=social_image_url,
            social_ui_url_value=social_ui_url(portal_id, cfg),
            breeze_prompts=breeze_prompts,
            email_banner_url=banner_url,
            blog_featured_image_url=hero_url,
        ),
        encoding="utf-8",
    )
    links_path = write_campaign_links_file(
        out_dir,
        campaign_slug=campaign_slug,
        portal_id=portal_id,
        cfg=cfg,
        blog_id=post_id,
        email_id=email_id,
        hero_url=hero_url,
        banner_url=banner_url,
        social_image_url=social_image_url,
        social_copy=social_copy,
        review_path=review_path,
        image_dpi=int(hero.get("dpi") or 150),
    )
    (out_dir / "image-resolution.json").write_text(json.dumps(hero, indent=2), encoding="utf-8")
    (out_dir / "staging-manifest.json").write_text(
        json.dumps(
            {
                "campaign": campaign_slug,
                "blogId": post_id,
                "emailId": email_id,
                "topic": topic,
                "trade": trade,
                "visualTopic": visual_topic,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "campaign": campaign_slug,
                "topic": topic,
                "trade": trade,
                "visualTopic": visual_topic,
                "imageSource": hero.get("source"),
                "imageSearchQuery": hero.get("searchQuery"),
                "imageDpi": hero.get("dpi"),
                "blogHeroPixelSize": hero.get("pixelSize"),
                "blogId": post_id,
                "blogEditorUrl": blog_editor_url(portal_id, post_id, cfg),
                "blogFeaturedImage": hero_url,
                "emailId": email_id,
                "emailEditorUrl": email_editor_url(portal_id, email_id, cfg),
                "emailBannerUrl": banner_url,
                "emailBannerDpi": 150,
                "socialImageUrl": social_image_url,
                "socialImageDpi": 150,
                "socialCopyPath": social_copy,
                "socialUiUrl": social_ui_url(portal_id, cfg),
                "breezePrompts": breeze_prompts,
                "reviewPath": str(review_path.relative_to(repo_root())),
                "reviewAbsolutePath": str(review_path.resolve()),
                "campaignLinksPath": str(links_path.relative_to(repo_root())),
                "stagingDirectory": str(out_dir.relative_to(repo_root())),
                "draftOnly": True,
            },
            indent=2,
        )
    )


def cmd_refresh_campaign_images(args: argparse.Namespace) -> None:
    """Re-render and upload all campaign images at 150 DPI for existing staged drafts."""
    load_dotenv()
    cfg = load_config()
    portal_id = str(cfg.get("portalId") or "")
    campaign_slug = slugify(args.campaign)

    manifest_path = staging_dir(cfg) / campaign_slug / "staging-manifest.json"
    package_path = staging_dir(cfg) / campaign_slug / "package.json"
    if not package_path.is_file():
        raise SystemExit(f"package.json not found: {package_path}")

    bundle = json.loads(package_path.read_text(encoding="utf-8"))
    post_id = args.blog_id
    email_id = args.email_id
    if manifest_path.is_file() and (not post_id or not email_id):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        post_id = post_id or manifest.get("blogId")
        email_id = email_id or manifest.get("emailId")
    if not post_id or not email_id:
        raise SystemExit("--blog-id and --email-id required (or staging-manifest.json with IDs)")

    topic = (bundle.get("topic") or "").strip()
    trade = (bundle.get("trade") or infer_trade_from_topic(topic)).strip().lower()
    email = bundle.get("email") or {}
    social = bundle.get("social") or {}
    blog = bundle.get("blog") or {}
    review_title = bundle.get("reviewTitle") or campaign_slug.replace("-", " ").title()
    visual_topic = bundle.get("visualTopic") or build_visual_topic_from_topic(topic, trade)
    social_headline = social.get("headline") or email.get("bannerHeadline") or blog.get("title", "")[:60]

    if getattr(args, "bg_file", None):
        bg_path = Path(args.bg_file)
        if not bg_path.is_file():
            raise SystemExit(f"Background file not found: {bg_path}")
        bg_bytes = bg_path.read_bytes()
        render_photo_at_dpi, blog_hero_pixel_size, target_dpi, blog_display_w, blog_display_h = (
            import_render_photo_at_dpi()
        )
        pixel_w, pixel_h = blog_hero_pixel_size()
        upload_to_hubspot_fn = import_upload_to_hubspot()
        hero_bytes = render_photo_at_dpi(bg_bytes)
        folder = f"/campaign-images/{campaign_slug}"
        filename = f"{campaign_slug}-topic-hero-150dpi.jpg"
        uploaded = upload_to_hubspot_fn(hero_bytes, filename, folder_path=folder)
        hero_url_local = str(uploaded.get("url") or uploaded.get("defaultHostingUrl") or "")
        hero = {
            "visualTopic": visual_topic,
            "searchQuery": "cursor_ai_generated",
            "source": "cursor_ai",
            "url": hero_url_local,
            "dpi": target_dpi,
            "displaySize": [blog_display_w, blog_display_h],
            "pixelSize": [pixel_w, pixel_h],
            "fileId": uploaded.get("id"),
            "breezePrompts": breeze_prompts_for_topic(visual_topic),
            "topicMatchedPhoto": True,
            "breezeRequiredForTopicPhoto": False,
            "matchedRule": "cursor_ai",
            "bgFile": str(bg_path.resolve()),
        }
    else:
        hero = resolve_topic_hero_image(visual_topic, trade, campaign_slug, topic=topic)
    hero_url = str(hero["url"])
    breeze_prompts = hero.get("breezePrompts") or breeze_prompts_for_topic(visual_topic)

    out_dir = staging_dir(cfg) / campaign_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "image-resolution.json").write_text(json.dumps(hero, indent=2), encoding="utf-8")

    blog_body_path = out_dir / "blog-body.html"
    blog_body_raw = blog_body_path.read_text(encoding="utf-8") if blog_body_path.is_file() else blog.get("bodyHtml", "")
    blog_body = prepend_blog_hero_image(blog_body_raw, hero_url, alt=blog.get("title", ""))
    sync_blog_post_widgets(post_id, blog_body, featured_image=hero_url)

    bin_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(bin_dir))
    from attach_email_banner import build_banner, patch_email  # noqa: E402

    upload_to_hubspot = import_upload_to_hubspot()
    banner_bytes = build_banner(hero_url, email["bannerHeadline"])
    banner_filename = f"{campaign_slug}-email-header-v2.jpg"
    banner_upload = upload_to_hubspot(
        banner_bytes,
        banner_filename,
        folder_path=f"/campaign-images/{campaign_slug}",
    )
    banner_url = str(banner_upload.get("url") or banner_upload.get("defaultHostingUrl") or "")

    email_body_path = out_dir / "email-body.html"
    html_body = email_body_path.read_text(encoding="utf-8") if email_body_path.is_file() else email.get("htmlBody", "")
    patch_email(
        email_id,
        banner_url,
        email["bannerHeadline"],
        html_body=html_body,
        subject=email.get("subject"),
        name=email.get("name"),
        preheader=email.get("preheader") or "",
    )

    render_card = import_render_social_card()
    social_filename = f"{campaign_slug}-linkedin-300x300-v2.png"
    social_local = out_dir / social_filename
    render_card(
        social_headline,
        social_local,
        SKILL_DIR / "assets" / "fonts",
        bg_url=hero_url,
    )
    social_upload = upload_to_hubspot(
        social_local.read_bytes(),
        social_filename,
        folder_path=f"/campaign-images/{campaign_slug}",
    )
    social_image_url = str(social_upload.get("url") or social_upload.get("defaultHostingUrl") or "")

    social_dir = social_ready_dir(cfg) / campaign_slug
    social_copy = str((social_dir / "linkedin-post.txt").resolve())
    review_path = social_dir / "REVIEW.md"
    review_path.write_text(
        render_review_doc(
            title=review_title,
            campaign_slug=campaign_slug,
            blog_editor_url_value=blog_editor_url(portal_id, post_id, cfg),
            email_editor_url_value=email_editor_url(portal_id, email_id, cfg),
            social_copy_path=social_copy,
            social_image_url=social_image_url,
            social_ui_url_value=social_ui_url(portal_id, cfg),
            breeze_prompts=breeze_prompts,
            email_banner_url=banner_url,
            blog_featured_image_url=hero_url,
        ),
        encoding="utf-8",
    )
    links_path = write_campaign_links_file(
        out_dir,
        campaign_slug=campaign_slug,
        portal_id=portal_id,
        cfg=cfg,
        blog_id=post_id,
        email_id=email_id,
        hero_url=hero_url,
        banner_url=banner_url,
        social_image_url=social_image_url,
        social_copy=social_copy,
        review_path=review_path,
        image_dpi=int(hero.get("dpi") or 150),
    )
    (out_dir / "staging-manifest.json").write_text(
        json.dumps(
            {
                "campaign": campaign_slug,
                "blogId": post_id,
                "emailId": email_id,
                "topic": topic,
                "trade": trade,
                "visualTopic": visual_topic,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "campaign": campaign_slug,
                "blogId": post_id,
                "blogFeaturedImage": hero_url,
                "blogHeroDpi": hero.get("dpi"),
                "blogHeroPixelSize": hero.get("pixelSize"),
                "emailBannerUrl": banner_url,
                "emailBannerDpi": 150,
                "socialImageUrl": social_image_url,
                "socialImageDpi": 150,
                "reviewPath": str(review_path.relative_to(repo_root())),
                "campaignLinksPath": str(links_path.relative_to(repo_root())),
                "draftOnly": True,
            },
            indent=2,
        )
    )


def cmd_get_campaign_links(args: argparse.Namespace) -> None:
    load_dotenv()
    cfg = load_config()
    links = read_campaign_links(args.campaign, cfg)
    print(json.dumps(links, indent=2))


def asset_draft_status(blog_id: str, email_id: str) -> dict[str, Any]:
    """Read-only HubSpot check — blog/email must stay DRAFT until user explicitly publishes."""
    blog_draft = hubspot_request("GET", f"{BLOG_API}/{blog_id}/draft")
    blog_live = hubspot_request("GET", f"{BLOG_API}/{blog_id}")
    email_draft = hubspot_request("GET", f"{EMAIL_API}/{email_id}/draft")
    email_live = hubspot_request("GET", f"{EMAIL_API}/{email_id}")

    blog_state = str(blog_live.get("state") or blog_draft.get("state") or "UNKNOWN")
    email_state = str(email_live.get("state") or email_draft.get("state") or "UNKNOWN")
    blog_published = bool(
        blog_live.get("currentlyPublished")
        or blog_draft.get("currentlyPublished")
        or blog_state.upper() in {"PUBLISHED", "SCHEDULED"}
    )
    email_published = bool(email_live.get("isPublished") or email_draft.get("isPublished"))

    return {
        "blogId": blog_id,
        "emailId": email_id,
        "blogState": blog_state,
        "emailState": email_state,
        "blogPublished": blog_published,
        "emailPublished": email_published,
        "allDraft": not blog_published and not email_published,
    }


def staged_campaign_manifests(cfg: dict) -> list[dict[str, Any]]:
    base = staging_dir(cfg)
    manifests: list[dict[str, Any]] = []
    if not base.is_dir():
        return manifests
    for child in sorted(base.iterdir()):
        manifest_path = child / "staging-manifest.json"
        if not manifest_path.is_file():
            continue
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data.setdefault("campaign", child.name)
        manifests.append(data)
    return manifests


def cmd_verify_campaign_draft_status(args: argparse.Namespace) -> None:
    """Verify staged HubSpot assets are draft-only. Read-only — never publishes or unpublishes."""
    load_dotenv()
    cfg = load_config()
    manifests = staged_campaign_manifests(cfg)
    if args.campaign:
        slug = slugify(args.campaign)
        manifests = [m for m in manifests if slugify(str(m.get("campaign") or "")) == slug]
        if not manifests:
            raise SystemExit(f"No staging-manifest.json found for campaign: {args.campaign}")

    results: list[dict[str, Any]] = []
    for manifest in manifests:
        blog_id = str(manifest.get("blogId") or "")
        email_id = str(manifest.get("emailId") or "")
        if not blog_id or not email_id:
            results.append(
                {
                    "campaign": manifest.get("campaign"),
                    "error": "missing blogId or emailId in staging-manifest.json",
                    "allDraft": None,
                }
            )
            continue
        status = asset_draft_status(blog_id, email_id)
        results.append({"campaign": manifest.get("campaign"), **status})

    checkable = [r for r in results if r.get("allDraft") is not None]
    all_draft = all(r.get("allDraft") for r in checkable) if checkable else False
    any_live = any(r.get("blogPublished") or r.get("emailPublished") for r in results)

    print(
        json.dumps(
            {
                "draftOnlyGuardrail": (
                    "This MCP never publishes, sends, or schedules. "
                    "Do not publish unless the user explicitly requests it."
                ),
                "allDraft": all_draft,
                "anyLive": any_live,
                "campaignCount": len(results),
                "campaigns": results,
            },
            indent=2,
        )
    )


def cmd_upload_social_image(args: argparse.Namespace) -> None:
    load_dotenv()
    campaign_slug = slugify(args.campaign)
    headline = args.headline
    filename = args.filename or f"{campaign_slug}-linkedin-300x300-v2.png"
    folder_path = args.folder_path or f"/campaign-images/{campaign_slug}"

    out_dir = staging_dir(load_config()) / campaign_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.output) if args.output else out_dir / filename

    render_card = import_render_social_card()
    font_dir = Path(args.font_dir) if args.font_dir else SKILL_DIR / "assets" / "fonts"
    bg_url = args.bg_url or TRADE_HERO_IMAGES.get(args.trade or "", "")
    render_card(headline, out_path, font_dir, bg_url=bg_url or None)

    upload_to_hubspot = import_upload_to_hubspot()
    uploaded = upload_to_hubspot(
        out_path.read_bytes(),
        filename,
        folder_path=folder_path,
    )
    url = uploaded.get("url") or uploaded.get("defaultHostingUrl") or ""

    print(
        json.dumps(
            {
                "campaign": campaign_slug,
                "localPath": str(out_path.relative_to(repo_root())),
                "localAbsolutePath": str(out_path.resolve()),
                "cdnUrl": url,
                "fileId": uploaded.get("id"),
                "headline": headline,
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
    p_review.add_argument(
        "--visual-topic",
        help="Visual brief used to auto-generate Breeze prompts in REVIEW.md",
    )
    p_review.add_argument("--breeze-audience", help="Audience clause for Breeze prompts")
    p_review.add_argument(
        "--breeze-prompts-json",
        help='JSON object with blog_featured, email_header, social prompt strings',
    )
    p_review.add_argument("--email-banner-url", help="HubSpot CDN URL for 150 DPI email header")
    p_review.add_argument("--blog-featured-image-url", help="HubSpot CDN URL for 150 DPI blog hero")
    p_review.set_defaults(func=cmd_write_review_doc)

    p_social_img = sub.add_parser(
        "upload-social-image",
        help="Generate branded 300x300 social image and upload to HubSpot File Manager",
    )
    p_social_img.add_argument("--campaign", required=True)
    p_social_img.add_argument("--headline", required=True)
    p_social_img.add_argument("--output", help="Local PNG path (default: _content/staging/{campaign}/...)")
    p_social_img.add_argument("--filename", help="Upload filename (default: {campaign}-linkedin-300x300.png)")
    p_social_img.add_argument(
        "--folder-path",
        help="HubSpot File Manager folder (default: /campaign-images/{campaign})",
    )
    p_social_img.add_argument("--font-dir", help="Override Wix Madefor font directory")
    p_social_img.add_argument("--bg-url", help="Background photo URL for the 300x300 card")
    p_social_img.add_argument(
        "--trade",
        choices=sorted(TRADE_HERO_IMAGES),
        help="Use trade-specific Vixxo hero image when --bg-url is omitted",
    )
    p_social_img.set_defaults(func=cmd_upload_social_image)

    p_breeze = sub.add_parser("breeze-prompt", help="Build HubSpot Breeze AI image prompt for a channel")
    p_breeze.add_argument("--topic", required=True)
    p_breeze.add_argument(
        "--channel",
        required=True,
        choices=["blog_featured", "email_header", "social"],
    )
    p_breeze.add_argument("--audience")
    p_breeze.set_defaults(func=cmd_breeze_prompt)

    p_brief = sub.add_parser(
        "get-package-brief",
        help="Return composition schema + rules for Cursor to build a content package from a topic",
    )
    p_brief.add_argument("--topic", help="User topic prompt")
    p_brief.set_defaults(func=cmd_get_package_brief)

    p_pkg = sub.add_parser(
        "stage-content-package",
        help="Stage full blog + email + social + images + REVIEW.md from a composed package JSON",
    )
    p_pkg.add_argument("--package-json", help="JSON content package object")
    p_pkg.add_argument("--package-file", help="Path to JSON content package file")
    p_pkg.set_defaults(func=cmd_stage_content_package)

    p_refresh = sub.add_parser(
        "refresh-campaign-images",
        help="Re-render all campaign images at 150 DPI for existing staged blog/email drafts",
    )
    p_refresh.add_argument("--campaign", required=True, help="Campaign slug")
    p_refresh.add_argument("--blog-id", help="HubSpot blog post ID (or read from staging-manifest.json)")
    p_refresh.add_argument("--email-id", help="HubSpot marketing email ID (or read from staging-manifest.json)")
    p_refresh.add_argument(
        "--bg-file",
        help="Local background photo (e.g. Cursor AI-generated) — skips stock search; renders at 150 DPI",
    )
    p_refresh.set_defaults(func=cmd_refresh_campaign_images)

    p_links = sub.add_parser(
        "get-campaign-links",
        help="Return consolidated link table for a staged campaign",
    )
    p_links.add_argument("--campaign", required=True, help="Campaign slug")
    p_links.set_defaults(func=cmd_get_campaign_links)

    p_verify = sub.add_parser(
        "verify-campaign-draft-status",
        help="Read-only check that staged blog/email assets are DRAFT (never publishes or unpublishes)",
    )
    p_verify.add_argument(
        "--campaign",
        help="Campaign slug (optional — checks all staged campaigns when omitted)",
    )
    p_verify.set_defaults(func=cmd_verify_campaign_draft_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
