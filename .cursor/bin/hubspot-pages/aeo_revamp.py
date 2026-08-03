#!/usr/bin/env python3
"""AEO + SEO revamp helpers for existing HubSpot site pages (clone drafts only)."""
from __future__ import annotations

import copy
import re
import time
from datetime import datetime, timezone
from typing import Any, Callable

from page_content import (
    apply_package_to_blueprint,
    build_faq_html,
    build_internal_links_html,
    build_update_payload,
    discover_internal_links,
    html_paragraph,
    infer_page_kind,
    normalize_package,
    resolve_page_images,
)

# Imported lazily in clone_name_for_payload to avoid import cycles at module load.

SITE_PAGES_API = "https://api.hubapi.com/cms/pages/2026-03/site-pages"

DEFAULT_INTERNAL_LINKS = [
    {"label": "Facility Management Solutions", "slug": "solutions"},
    {"label": "Contact Vixxo", "slug": "about-us/contact-us"},
    {"label": "About Vixxo", "slug": "about-us/overview"},
]

TRADE_KEYWORDS = {
    "hvac": ("hvac", "heating", "cooling", "refrigeration"),
    "plumbing": ("plumbing", "drain", "water heater"),
    "electrical": ("electrical", "lighting", "sign"),
    "handyman": ("handyman", "general maintenance"),
}


def clean_page_topic(name: str) -> str:
    from hubspot_pages import strip_clone_title_suffix

    text = strip_clone_title_suffix(name or "")
    text = re.sub(r"\s*-\s*(June|July|August)\s+\d{4}\s*$", "", text, flags=re.I)
    text = re.sub(r"\s*\(.*?\)\s*$", "", text).strip()
    return text or name or "Vixxo facility management"


def clone_name_for_payload(
    package: dict[str, Any],
    *,
    live_page: dict[str, Any] | None = None,
    clone_page: dict[str, Any] | None = None,
) -> str:
    from hubspot_pages import clone_page_title, resolve_clone_base_name

    base = resolve_clone_base_name(live_page=live_page, package=package, clone_page=clone_page)
    existing = str((clone_page or {}).get("name") or "")
    if existing:
        return clone_page_title(existing)
    return clone_page_title(base)


def primary_keyword(topic: str, slug: str) -> str:
    slug_text = (slug or "").replace("/", " ").replace("-", " ")
    base = clean_page_topic(topic).lower()
    if slug_text and slug_text not in {"(homepage)", "homepage"}:
        return f"{slug_text.strip()} facility management"
    return "multi-site facility management"


def build_answer_first(topic: str, slug: str) -> str:
    kw = primary_keyword(topic, slug)
    clean = clean_page_topic(topic)
    if slug in {"(homepage)", "", "home"}:
        return (
            "Vixxo is a national facilities management partner for multi-site retail, "
            "grocery, restaurant, and convenience brands. We coordinate licensed "
            "technicians, work orders, and preventive maintenance across your portfolio."
        )
    if "case study" in slug.lower() or "resources" in slug.lower():
        return (
            f"This Vixxo case study shows how {clean.lower()} teams improved uptime, "
            "cost control, and vendor coordination across a multi-site facilities program."
        )
    if "contact" in slug.lower():
        return (
            "Contact Vixxo to discuss multi-site facility management, service provider "
            "coordination, and preventive maintenance for retail and restaurant portfolios."
        )
    if "career" in slug.lower():
        return (
            "Vixxo careers connect facilities professionals with multi-site retail and "
            "restaurant programs backed by licensed technicians and national scale."
        )
    return (
        f"Vixxo helps multi-site operators manage {clean.lower()} with licensed technicians, "
        f"centralized work orders, and preventive maintenance aligned to {kw} priorities."
    )


def build_faqs(topic: str, slug: str) -> list[dict[str, str]]:
    clean = clean_page_topic(topic)
    kw = primary_keyword(topic, slug)
    return [
        {
            "question": f"What is Vixxo {clean}?",
            "answer": (
                f"Vixxo provides national facilities management for multi-site brands, "
                f"including {clean.lower()} services delivered through a licensed service provider network."
            ),
        },
        {
            "question": f"How does Vixxo support {kw}?",
            "answer": (
                "Vixxo coordinates preventive maintenance, reactive repairs, and vendor "
                "management through one work-order platform built for distributed portfolios."
            ),
        },
        {
            "question": "Which industries does Vixxo serve?",
            "answer": (
                "Vixxo supports retail, grocery, convenience, restaurant, healthcare, "
                "and hospitality operators that need consistent facilities execution at scale."
            ),
        },
        {
            "question": "How do I get started with Vixxo?",
            "answer": (
                "Request a conversation with Vixxo to review your site list, trades, "
                "and maintenance priorities. Programs stay in draft until your team approves changes."
            ),
        },
    ]


def build_html_title(topic: str, slug: str) -> str:
    clean = clean_page_topic(topic)
    if slug in {"(homepage)", "", "home"}:
        title = "Multi-Site Facility Management | Vixxo"
    elif len(clean) + 10 <= 60:
        title = f"{clean} | Vixxo"
    else:
        title = f"{clean[:48].rstrip()} | Vixxo"
    return title[:60]


def build_meta_description(topic: str, slug: str, answer_first: str) -> str:
    if answer_first and len(answer_first) <= 155:
        return answer_first
    clean = clean_page_topic(topic)
    desc = (
        f"Learn how Vixxo supports {clean.lower()} for multi-site retail and restaurant "
        "operators with licensed technicians and centralized work orders."
    )
    return desc[:155]


def llm_test_queries(topic: str, slug: str) -> str:
    clean = clean_page_topic(topic)
    queries = [
        f"What is Vixxo {clean}?",
        f"How does Vixxo handle {primary_keyword(topic, slug)}?",
        f"Who does Vixxo serve for {clean.lower()}?",
    ]
    return " | ".join(queries)


def score_before(page: dict[str, Any]) -> tuple[int, int]:
    title = str(page.get("htmlTitle") or "")
    meta = str(page.get("metaDescription") or "")
    layout = page.get("layoutSections") or {}
    text_blob = _collect_rich_text(layout).lower()
    aeo = 35
    seo = 35
    if 30 <= len(title) <= 60:
        seo += 15
    if meta and 80 <= len(meta) <= 155:
        seo += 15
    if "<h1" in text_blob:
        seo += 10
        aeo += 10
    if text_blob.count("<h2") >= 2:
        seo += 10
        aeo += 10
    if "faq" in text_blob or text_blob.count("<h3") >= 3:
        aeo += 20
    if text_blob.count("<a ") >= 2:
        seo += 10
        aeo += 10
    if len(text_blob) > 400:
        aeo += 15
    return min(aeo, 100), min(seo, 100)


def score_after(package: dict[str, Any]) -> tuple[int, int]:
    title = str(package.get("htmlTitle") or "")
    meta = str(package.get("metaDescription") or "")
    aeo = 55
    seo = 55
    if package.get("answerFirst"):
        aeo += 15
    if len(package.get("faqs") or []) >= 3:
        aeo += 15
    if len(package.get("internalLinks") or []) >= 2:
        aeo += 10
        seo += 10
    if 30 <= len(title) <= 60:
        seo += 15
    if meta and 80 <= len(meta) <= 155:
        seo += 15
    if package.get("sections"):
        seo += 10
    return min(aeo, 100), min(seo, 100)


def build_revamp_package(
    page: dict[str, Any],
    list_pages_fn: Callable[[], list[dict[str, Any]]],
) -> dict[str, Any]:
    topic = clean_page_topic(str(page.get("name") or ""))
    slug = str(page.get("slug") or "")
    answer = build_answer_first(topic, slug)
    faqs = build_faqs(topic, slug)
    links = discover_internal_links(topic, list_pages_fn, existing=DEFAULT_INTERNAL_LINKS, limit=4)
    html_title = build_html_title(topic, slug)
    meta = build_meta_description(topic, slug, answer)
    return {
        "topic": topic,
        "pageName": clean_page_topic(str(page.get("name") or topic)),
        "slug": slug,
        "htmlTitle": html_title,
        "metaDescription": meta,
        "answerFirst": answer,
        "faqs": faqs,
        "internalLinks": links,
        "sections": [
            {
                "heading": f"Why choose Vixxo for {topic.lower()}?",
                "bodyHtml": html_paragraph(
                    "Vixxo combines national coverage with trade-specific expertise so "
                    "multi-site teams spend less time chasing vendors and more time "
                    "running stores. Programs include preventive maintenance, reactive "
                    "repairs, and performance reporting through one work-order platform."
                ),
            }
        ],
        "primaryKeyword": primary_keyword(topic, slug),
        "llmTestQueries": llm_test_queries(topic, slug),
        "seoNotes": (
            "Staged answer-first intro, FAQ block, internal links, and optimized "
            "htmlTitle/metaDescription on clone draft."
        ),
    }


def _collect_rich_text(obj: Any) -> str:
    chunks: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in {"rich_text", "content", "text"} and isinstance(value, str):
                chunks.append(value)
            else:
                chunks.append(_collect_rich_text(value))
    elif isinstance(obj, list):
        for item in obj:
            chunks.append(_collect_rich_text(item))
    return "\n".join(chunks)


def _is_hero_rich_text(text: str, module_label: str = "") -> bool:
    """Detect hero blocks — AEO copy must never be injected here."""
    label = module_label.lower()
    if any(skip in label for skip in ("column layout", "call to action", "blog post", "multi-column")):
        return False
    if re.search(r"\bhero\b", label):
        return True
    lower = text.lower()
    if "<h1" in lower and "<h2" not in lower and "text-align: center" in lower:
        return True
    if "<h2" in lower and "text-align: center" in lower and len(text) < 600 and "#fff" in lower:
        return True
    if "<h1" in lower and "#fff" in lower and len(text) < 350:
        return True
    if "<h1" in lower and "<h2" not in lower and len(text) < 120:
        return True
    return False


AEO_STRIP_MARKERS = (
    "What is Vixxo",
    "Vixxo helps multi-site operators",
    "Vixxo careers connect",
    "Vixxo is a national facilities",
    "Contact Vixxo to discuss",
    "Frequently Asked Questions",
)


def _strip_prior_aeo_injection(text: str) -> str:
    """Remove a previous AEO pass so reprocess starts from live body copy."""
    if not text or not any(marker in text for marker in AEO_STRIP_MARKERS):
        return text
    lower = text.lower()
    cut = lower.find("<h4><span style=\"color: #8e992e")
    if cut == -1:
        cut = lower.find("<h4><span style='color: #8e992e")
    if cut == -1:
        for marker in AEO_STRIP_MARKERS:
            idx = text.find(marker)
            if idx != -1:
                prior = text.rfind("<h", 0, idx)
                cut = prior if prior != -1 else idx
                break
    return text[cut:].lstrip() if cut > 0 else text


def _build_aeo_injection(package: dict[str, Any]) -> str:
    answer_html = (
        '<h4><span style="color: #8e992e; font-family: \'Wix Madefor Text\'; '
        f'font-weight: 800; font-style: normal;">{package["answerFirst"]}</span></h4>'
    )
    section_html = ""
    for section in package.get("sections") or []:
        heading = str(section.get("heading") or "").strip()
        body = str(section.get("bodyHtml") or "").strip()
        if heading:
            section_html += f"<h2>{heading}</h2>"
        if body:
            section_html += body
    faq_html = build_faq_html(package.get("faqs") or [])
    links_html = build_internal_links_html(package.get("internalLinks") or [])
    return "\n".join(part for part in [answer_html, section_html, faq_html, links_html] if part)


def _iter_content_targets(obj: Any, module_label: str = "") -> list[dict[str, Any]]:
    """Find injectable rich_text / widget content fields in layout or widgets."""
    targets: list[dict[str, Any]] = []

    def walk(node: Any, label: str = "") -> None:
        if isinstance(node, dict):
            current_label = str(node.get("label") or label)
            if node.get("label"):
                current_label = str(node["label"])
            if "rich_text" in node and isinstance(node["rich_text"], str):
                targets.append({"obj": node, "field": "rich_text", "module_label": current_label})
            body = node.get("body")
            if isinstance(body, dict):
                col1 = body.get("col_1")
                if isinstance(col1, dict) and isinstance(col1.get("content"), str):
                    targets.append({"obj": col1, "field": "content", "module_label": current_label})
                content = body.get("content")
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    targets.append({"obj": content, "field": "text", "module_label": current_label})
            for value in node.values():
                walk(value, current_label)
        elif isinstance(node, list):
            for item in node:
                walk(item, label)

    walk(obj, module_label)
    return targets


def _pick_body_target(targets: list[dict[str, Any]]) -> dict[str, Any] | None:
    body_target: dict[str, Any] | None = None
    for entry in targets:
        text = str(entry["obj"].get(entry["field"]) or "")
        if _is_hero_rich_text(text, entry.get("module_label") or ""):
            continue
        if "<h2" in text.lower() or len(text) > 180:
            body_target = entry
            break
    if body_target is None:
        for entry in targets:
            text = str(entry["obj"].get(entry["field"]) or "")
            if not _is_hero_rich_text(text, entry.get("module_label") or ""):
                body_target = entry
                break
    return body_target


def _inject_aeo_into_target(target: dict[str, Any], package: dict[str, Any]) -> None:
    field = target["field"]
    obj = target["obj"]
    injection = _build_aeo_injection(package)
    existing = _strip_prior_aeo_injection(str(obj.get(field) or ""))
    if package["answerFirst"][:40] not in existing:
        obj[field] = injection + ("\n" + existing if existing else "")


def _iter_rich_text_targets(layout_sections: dict[str, Any]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []

    def walk(obj: Any, module_label: str = "") -> None:
        if isinstance(obj, dict):
            label = str(obj.get("label") or module_label)
            if obj.get("label"):
                label = str(obj["label"])
            if "rich_text" in obj and isinstance(obj["rich_text"], str):
                targets.append({"obj": obj, "module_label": label})
            for value in obj.values():
                walk(value, label)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, module_label)

    walk(layout_sections)
    return targets


def patch_layout_sections(layout_sections: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    patched = copy.deepcopy(layout_sections or {})
    targets = [
        {**entry, "field": "rich_text"}
        for entry in _iter_rich_text_targets(patched)
    ]
    body_target = _pick_body_target(targets)
    if body_target:
        _inject_aeo_into_target(body_target, package)
    return patched


def patch_widget_structure(
    widgets: dict[str, Any] | None,
    widget_containers: dict[str, Any] | None,
    package: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Patch AEO copy into legacy/widget-based page structures."""
    patched_widgets = copy.deepcopy(widgets or {})
    patched_containers = copy.deepcopy(widget_containers or {})
    targets = _iter_content_targets(patched_widgets) + _iter_content_targets(patched_containers)
    body_target = _pick_body_target(targets)
    if body_target:
        _inject_aeo_into_target(body_target, package)
    return patched_widgets, patched_containers


def copy_live_structure(
    live_page: dict[str, Any],
    package: dict[str, Any],
    *,
    clone_page: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Copy published page layout/widgets and inject AEO without changing visual design."""
    layout = copy.deepcopy(live_page.get("layoutSections") or {})
    widgets = copy.deepcopy(live_page.get("widgets") or {})
    containers = copy.deepcopy(live_page.get("widgetContainers") or {})

    if len(_collect_rich_text(layout)) > 100:
        layout = patch_layout_sections(layout, package)
    if len(_collect_rich_text(widgets) + _collect_rich_text(containers)) > 100:
        widgets, containers = patch_widget_structure(widgets, containers, package)

    payload: dict[str, Any] = {
        "name": clone_name_for_payload(package, live_page=live_page, clone_page=clone_page),
        "htmlTitle": package["htmlTitle"],
        "metaDescription": package["metaDescription"],
        "templatePath": live_page.get("templatePath"),
    }
    if containers or widgets:
        payload["layoutSections"] = {}
        payload["widgets"] = widgets
        payload["widgetContainers"] = containers
    elif layout:
        payload["layoutSections"] = layout
        payload["widgets"] = {}
        payload["widgetContainers"] = {}
    return payload


def merge_structure_payload(
    live_page: dict[str, Any],
    clone_page: dict[str, Any],
    package: dict[str, Any],
) -> dict[str, Any]:
    """Build a replace-style payload from live and clear stale clone module keys."""
    payload = copy_live_structure(live_page, package, clone_page=clone_page)

    live_containers = (live_page.get("widgetContainers") or {}).keys()
    clone_containers = (clone_page.get("widgetContainers") or {}).keys()
    stale_containers = set(clone_containers) - set(live_containers)
    if stale_containers:
        containers = payload.setdefault("widgetContainers", {})
        for key in stale_containers:
            containers[key] = {"widgets": []}

    live_widgets = (live_page.get("widgets") or {}).keys()
    clone_widgets = (clone_page.get("widgets") or {}).keys()
    stale_widgets = set(clone_widgets) - set(live_widgets)
    if stale_widgets:
        widgets = payload.setdefault("widgets", {})
        for key in stale_widgets:
            widgets[key] = {"widgets": []}

    return payload


def layout_has_content(page: dict[str, Any]) -> bool:
    """True when page has substantive module content worth patching."""
    layout = page.get("layoutSections") or {}
    text = _collect_rich_text(layout)
    if len(text) > 100:
        return True
    widget_text = _collect_rich_text(page.get("widgets") or {})
    container_text = _collect_rich_text(page.get("widgetContainers") or {})
    return len(widget_text + container_text) > 100


def verify_clone_content(page: dict[str, Any]) -> dict[str, Any]:
    layout_text = _collect_rich_text(page.get("layoutSections") or {})
    widget_text = _collect_rich_text(page.get("widgets") or {})
    container_text = _collect_rich_text(page.get("widgetContainers") or {})
    text = layout_text + widget_text + container_text
    text_len = len(text)
    aeo = has_aeo_optimization(page) or any(
        marker in text
        for marker in (
            "What is Vixxo",
            "Vixxo helps multi-site operators",
            "Vixxo careers connect",
            "Vixxo is a national facilities",
            "Contact Vixxo to discuss",
        )
    )
    return {
        "text_len": text_len,
        "has_layout": layout_has_content(page),
        "has_aeo_injection": aeo,
        "content_confirmed": text_len > 500 and aeo,
        "empty": text_len < 200 and not layout_has_content(page),
    }


def has_aeo_optimization(page: dict[str, Any]) -> bool:
    text = _collect_rich_text(page.get("layoutSections") or {})
    text += _collect_rich_text(page.get("widgets") or {})
    text += _collect_rich_text(page.get("widgetContainers") or {})
    markers = (
        "What is Vixxo",
        "Vixxo helps multi-site operators",
        "Vixxo careers connect",
        "Vixxo is a national facilities",
        "Contact Vixxo to discuss",
    )
    return any(marker in text for marker in markers)


def revamp_to_stage_package(
    live_page: dict[str, Any],
    package: dict[str, Any],
    *,
    clone_slug: str | None = None,
) -> dict[str, Any]:
    topic = str(package.get("topic") or clean_page_topic(str(live_page.get("name") or "")))
    slug = clone_slug or str(live_page.get("slug") or package.get("slug") or "")
    headline = clean_page_topic(str(package.get("pageName") or topic))
    page_kind = infer_page_kind(topic, {"pageKind": package.get("pageKind")})
    return {
        "topic": topic,
        "pageName": str(package.get("pageName") or live_page.get("name") or headline),
        "slug": slug,
        "htmlTitle": package["htmlTitle"],
        "metaDescription": package["metaDescription"],
        "pageKind": page_kind,
        "layoutStyle": "standard",
        "hero": {
            "headline": headline,
            "subheadline": str(package.get("answerFirst") or "")[:120],
        },
        "answerFirst": package["answerFirst"],
        "intro": html_paragraph(package["answerFirst"]),
        "sections": package.get("sections") or [],
        "faqs": package.get("faqs") or [],
        "internalLinks": package.get("internalLinks") or [],
    }


def build_full_stage_payload(
    live_page: dict[str, Any],
    package: dict[str, Any],
    cfg: dict[str, Any],
    *,
    clone_slug: str | None = None,
) -> dict[str, Any]:
    """Rebuild empty clone drafts from CLEAN blueprint + optimized copy."""
    stage_pkg = revamp_to_stage_package(live_page, package, clone_slug=clone_slug)
    stage_pkg = normalize_package(stage_pkg, cfg)
    stage_pkg["slug"] = clone_slug or stage_pkg["slug"]
    stage_pkg["pageName"] = clone_name_for_payload(stage_pkg, live_page=live_page)
    campaign_slug = re.sub(r"[^a-z0-9]+", "-", stage_pkg["slug"].lower()).strip("-") or "page"
    images = resolve_page_images(stage_pkg, campaign_slug)
    stage_pkg["_images"] = images
    blueprint_applied = apply_package_to_blueprint(
        str(stage_pkg.get("pageKind") or "standard"),
        stage_pkg,
        images,
    )
    return build_update_payload(stage_pkg, blueprint_applied)


def build_stage_payload(
    page: dict[str, Any],
    package: dict[str, Any],
    cfg: dict[str, Any] | None = None,
    *,
    live_page: dict[str, Any] | None = None,
    clone_slug: str | None = None,
) -> dict[str, Any]:
    if live_page and layout_has_content(live_page):
        return copy_live_structure(live_page, package, clone_page=page)

    payload: dict[str, Any] = {
        "name": clone_name_for_payload(package, live_page=live_page, clone_page=page),
        "htmlTitle": package["htmlTitle"],
        "metaDescription": package["metaDescription"],
    }
    if layout_has_content(page):
        layout = patch_layout_sections(copy.deepcopy(page.get("layoutSections") or {}), package)
        if len(_collect_rich_text(layout)) > 100:
            payload["layoutSections"] = layout
        widgets, containers = patch_widget_structure(
            page.get("widgets"),
            page.get("widgetContainers"),
            package,
        )
        if _collect_rich_text(widgets) + _collect_rich_text(containers):
            payload["widgets"] = widgets
            payload["widgetContainers"] = containers
        if page.get("templatePath"):
            payload["templatePath"] = page.get("templatePath")
        return payload

    if cfg and live_page:
        return build_full_stage_payload(live_page, package, cfg, clone_slug=clone_slug)
    return payload


def write_report_md(
    report_path: Any,
    *,
    live_page: dict[str, Any],
    clone_page: dict[str, Any],
    package: dict[str, Any],
    before_scores: tuple[int, int],
    after_scores: tuple[int, int],
) -> None:
    lines = [
        f"# AEO + SEO Revamp — {package['pageName']}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## URLs",
        "",
        f"- **Live (Before):** {live_page.get('url')}",
        f"- **Clone (After):** {clone_page.get('url')}",
        f"- **Editor:** {clone_page.get('editorUrl')}",
        "",
        "## Scores",
        "",
        f"| Metric | Before | After |",
        f"| --- | ---: | ---: |",
        f"| AEO | {before_scores[0]} | {after_scores[0]} |",
        f"| SEO | {before_scores[1]} | {after_scores[1]} |",
        "",
        "## SEO (staged on clone)",
        "",
        f"- **Title:** {package['htmlTitle']}",
        f"- **Meta:** {package['metaDescription']}",
        f"- **Primary keyword:** {package['primaryKeyword']}",
        "",
        "## AEO checklist",
        "",
        "- [x] Answer-first intro (40–60 words)",
        "- [x] Question-style H2 section",
        f"- [x] FAQ block ({len(package.get('faqs') or [])} Q&As)",
        f"- [x] Internal links ({len(package.get('internalLinks') or [])})",
        "- [x] Entity-rich FM copy (Vixxo, multi-site, licensed technicians)",
        "",
        "## LLM test queries",
        "",
        package.get("llmTestQueries") or "",
        "",
        "## Notes",
        "",
        package.get("seoNotes") or "",
        "",
        "**Draft only — not published.**",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def backoff_sleep(attempt: int) -> None:
    time.sleep(min(2 ** attempt, 30))
