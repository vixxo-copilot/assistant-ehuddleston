"""Compose AEO/SEO HubSpot site pages from topic packages + CLEAN-6-1 module blueprints."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Callable

SKILL_DIR = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "hubspot-page-content"
CONTENT_BIN = Path(__file__).resolve().parent.parent / "hubspot-content"

PAGE_PACKAGE_SCHEMA: dict[str, Any] = {
    "topic": "Required user topic prompt",
    "pageName": "Internal HubSpot page name",
    "slug": "URL slug with section prefix, e.g. solutions/hvac-preventive-maintenance",
    "htmlTitle": "≤60 characters, primary keyword near front",
    "metaDescription": "≤155 characters, answer-first summary",
    "pageKind": "standard | case-study | contact (auto-inferred when omitted)",
    "hero": {
        "headline": "H1 — concise topic title",
        "subheadline": "Optional — case study kicker, e.g. A FACILITY MANAGEMENT CASE STUDY",
    },
    "answerFirst": "40–60 words directly answering the topic (AEO lead paragraph)",
    "intro": "Supporting intro paragraph(s) — HTML or plain text",
    "sections": [
        {
            "heading": "H2 phrased as a natural-language question where possible",
            "bodyHtml": "Section body HTML with <p> tags and optional internal <a href> links",
            "placement": "section1 | section2 | case-profile | case-challenge | case-solution",
        }
    ],
    "faqs": [{"question": "PAA-style question", "answer": "Direct concise answer"}],
    "internalLinks": [{"label": "Anchor text", "slug": "solutions/sign-and-lighting"}],
    "trade": "Optional — hvac | plumbing | electrical (auto-inferred from topic)",
    "visualTopic": "Optional editorial image brief (auto-generated when omitted)",
}

TEMPLATE_KEYS = {
    "standard": "targetTemplatePath",
    "case-study": "caseStudyTemplatePath",
    "contact": "contactTemplatePath",
}

DEFAULT_TEMPLATES = {
    "standard": "CLEAN-6-1-theme child X Vixxo Facility Solutions/templates/clean-pro-home-opt-1.html",
    "case-study": "CLEAN-6-1-theme child X Vixxo Facility Solutions/templates/clean-pro-case-study.html",
    "contact": "CLEAN-6-1-theme child X Vixxo Facility Solutions/templates/clean-pro-contact-us.html",
}

CASE_STUDY_KEYWORDS = ("case study", "customer story", "success story", "client story", "pilot program")
CONTACT_KEYWORDS = ("contact", "sales", "get in touch", "talk to", "request a demo", "schedule a call")
INDUSTRY_KEYWORDS = {
    "retail": ("retail", "store", "chain", "multi-site"),
    "grocery": ("grocery", "supermarket", "food retail"),
    "convenience": ("convenience", "c-store", "gas station"),
    "restaurant": ("restaurant", "food service", "qsr", "dining"),
    "healthcare": ("healthcare", "hospital", "clinic", "medical"),
    "hospitality": ("hospitality", "hotel", "lodging"),
}


def _import_hubspot_content_helpers() -> tuple[Any, ...]:
    import sys

    if str(CONTENT_BIN) not in sys.path:
        sys.path.insert(0, str(CONTENT_BIN))
    from hubspot_content import (  # noqa: E402
        build_visual_topic_from_topic,
        infer_trade_from_topic,
        package_brief_for_topic,
        slugify,
    )

    return slugify, infer_trade_from_topic, build_visual_topic_from_topic, package_brief_for_topic


def infer_page_kind(topic: str, package: dict[str, Any] | None = None) -> str:
    if package and package.get("pageKind"):
        kind = str(package["pageKind"]).strip().lower().replace("_", "-")
        if kind in TEMPLATE_KEYS:
            return kind
    text = (topic or "").lower()
    if any(kw in text for kw in CASE_STUDY_KEYWORDS):
        return "case-study"
    if any(kw in text for kw in CONTACT_KEYWORDS):
        return "contact"
    return "standard"


def infer_slug_prefix(topic: str, page_kind: str) -> str:
    if page_kind == "case-study":
        return "resources"
    if page_kind == "contact":
        return "about-us"
    text = (topic or "").lower()
    if any(kw in text for kw in ("industry", "industries", "sector", "vertical")):
        return "industries"
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return f"industries/{industry}"
    return "solutions"


def infer_slug(topic: str, page_kind: str, slugify: Callable[[str], str]) -> str:
    prefix = infer_slug_prefix(topic, page_kind)
    base = slugify(topic)
    if page_kind == "case-study" and not base.startswith("case-study"):
        base = f"case-study-{base}"
    if page_kind == "contact" and "contact" not in base:
        base = "contact-sales" if "sales" in topic.lower() else "contact-us"
    if "/" in prefix:
        return f"{prefix}/{base}"
    return f"{prefix}/{base}"


def template_path_for_kind(page_kind: str, cfg: dict[str, Any]) -> str:
    key = TEMPLATE_KEYS.get(page_kind, "targetTemplatePath")
    return str(cfg.get(key) or DEFAULT_TEMPLATES.get(page_kind) or cfg.get("targetTemplatePath") or "")


def load_blueprint(page_kind: str) -> dict[str, Any]:
    path = SKILL_DIR / "reference" / f"blueprint-{page_kind}.json"
    if not path.is_file() and page_kind != "standard":
        path = SKILL_DIR / "reference" / "blueprint-standard.json"
    if not path.is_file():
        raise SystemExit(f"Module blueprint missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def html_paragraph(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    if "<p" in text or "<h" in text or "<ul" in text:
        return text
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "".join(f"<p>{p}</p>" for p in parts)


def build_faq_html(faqs: list[dict[str, Any]]) -> str:
    if not faqs:
        return ""
    blocks = ['<h2>Frequently Asked Questions</h2>']
    for item in faqs:
        q = str(item.get("question") or "").strip()
        a = str(item.get("answer") or "").strip()
        if not q or not a:
            continue
        blocks.append(f"<h3>{q}</h3>")
        blocks.append(html_paragraph(a))
    return "\n".join(blocks)


def build_internal_links_html(links: list[dict[str, Any]]) -> str:
    if not links:
        return ""
    items = []
    for link in links:
        label = str(link.get("label") or "").strip()
        slug = str(link.get("slug") or "").strip().lstrip("/")
        if not label or not slug:
            continue
        href = f"/{slug}" if not slug.startswith("http") else slug
        items.append(f'<li><a href="{href}">{label}</a></li>')
    if not items:
        return ""
    return "<h3>Related Vixxo Resources</h3><ul>" + "".join(items) + "</ul>"


def _container_widgets(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    containers = blueprint.get("widgetContainers") or {}
    if not containers:
        return []
    first = next(iter(containers.values()))
    return list(first.get("widgets") or [])


def _widget_by_order(widgets: list[dict[str, Any]], order: int) -> dict[str, Any] | None:
    for widget in widgets:
        if widget.get("order") == order:
            return widget
    return None


def _widget_by_label(widgets: list[dict[str, Any]], label_substring: str) -> dict[str, Any] | None:
    needle = label_substring.lower()
    for widget in widgets:
        label = str(widget.get("label") or widget.get("body", {}).get("label") or "").lower()
        if needle in label:
            return widget
    return None


def set_image_fields(image_obj: dict[str, Any], url: str, alt: str) -> None:
    image_obj["src"] = url
    image_obj["alt"] = alt
    if "width" not in image_obj:
        image_obj["width"] = 1400
    if "height" not in image_obj:
        image_obj["height"] = 788


def apply_standard_package(
    blueprint: dict[str, Any],
    package: dict[str, Any],
    images: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    result = copy.deepcopy(blueprint)
    widgets = _container_widgets(result)

    hero = _widget_by_order(widgets, 0) or _widget_by_label(widgets, "hero")
    if hero:
        body = hero.setdefault("body", {})
        h1 = str(package.get("hero", {}).get("headline") or package.get("pageName") or "")
        body.setdefault("col_1", {})["content"] = f"<h1>{h1}</h1>"
        hero_img = images.get("hero") or {}
        if hero_img.get("url"):
            row_settings = body.setdefault("row_settings", {})
            bg = row_settings.setdefault("bg_image", {})
            set_image_fields(bg, hero_img["url"], hero_img.get("alt") or h1)

    intro = _widget_by_order(widgets, 1)
    if intro:
        answer = str(package.get("answerFirst") or "").strip()
        intro_html = html_paragraph(str(package.get("intro") or ""))
        centered = f'<div style="text-align: center;">{html_paragraph(answer)}</div>' if answer else ""
        intro.setdefault("body", {}).setdefault("col_1", {})["content"] = centered + intro_html

    section1 = _widget_by_label(widgets, "image and text")
    section1_data = next(
        (s for s in package.get("sections") or [] if s.get("placement") in (None, "section1")),
        (package.get("sections") or [{}])[0] if package.get("sections") else None,
    )
    if section1 and section1_data:
        body = section1.setdefault("body", {})
        heading = str(section1_data.get("heading") or "")
        body_html = str(section1_data.get("bodyHtml") or "")
        content = body.setdefault("content", {})
        content["text"] = f"<h2>{heading}</h2>\n{body_html}" if heading else body_html
        sec_img = images.get("section1") or {}
        if sec_img.get("url"):
            img = content.setdefault("image", {})
            set_image_fields(img, sec_img["url"], sec_img.get("alt") or heading)
            img["width"] = 600
            img["height"] = 337

    section2 = _widget_by_order(widgets, 4)
    section2_data = next(
        (s for s in package.get("sections") or [] if s.get("placement") == "section2"),
        (package.get("sections") or [None, None])[1] if len(package.get("sections") or []) > 1 else None,
    )
    faq_html = build_faq_html(package.get("faqs") or [])
    links_html = build_internal_links_html(package.get("internalLinks") or [])
    if section2:
        body_parts = []
        if section2_data:
            heading = str(section2_data.get("heading") or "")
            body_html = str(section2_data.get("bodyHtml") or "")
            if heading:
                body_parts.append(f"<h2>{heading}</h2>")
            body_parts.append(body_html)
        if faq_html:
            body_parts.append(faq_html)
        if links_html:
            body_parts.append(links_html)
        combined = "\n".join(body_parts)
        section2.setdefault("body", {}).setdefault("col_1", {})["content"] = combined
        if section2.get("body", {}).get("col_2"):
            section2["body"]["col_2"]["content"] = ""

    return result


def apply_case_study_package(
    blueprint: dict[str, Any],
    package: dict[str, Any],
    images: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    result = copy.deepcopy(blueprint)
    widgets = _container_widgets(result)

    hero = _widget_by_order(widgets, 0) or _widget_by_label(widgets, "hero")
    if hero:
        body = hero.setdefault("body", {})
        h1 = str(package.get("hero", {}).get("headline") or package.get("pageName") or "")
        sub = str(package.get("hero", {}).get("subheadline") or "A FACILITY MANAGEMENT CASE STUDY")
        body.setdefault("col_1", {})["content"] = f"<h1>{h1}</h1>\n<h3>{sub}</h3>"
        hero_img = images.get("hero") or {}
        if hero_img.get("url"):
            row_settings = body.setdefault("row_settings", {})
            bg = row_settings.setdefault("bg_image", {})
            set_image_fields(bg, hero_img["url"], hero_img.get("alt") or h1)

    placements = {
        "case-profile": 1,
        "case-challenge": 2,
        "case-solution": 3,
    }
    for section in package.get("sections") or []:
        placement = str(section.get("placement") or "case-profile")
        order = placements.get(placement, 1)
        widget = _widget_by_order(widgets, order)
        if not widget:
            continue
        heading = str(section.get("heading") or "")
        body_html = str(section.get("bodyHtml") or "")
        widget.setdefault("body", {}).setdefault("col_1", {})["content"] = (
            f"<h2>{heading}</h2>\n{body_html}" if heading else body_html
        )

    faq_widget = _widget_by_order(widgets, 4) or _widget_by_label(widgets, "multi-column")
    faq_html = build_faq_html(package.get("faqs") or [])
    links_html = build_internal_links_html(package.get("internalLinks") or [])
    if faq_widget and (faq_html or links_html):
        faq_widget.setdefault("body", {}).setdefault("col_1", {})["content"] = faq_html + links_html

    return result


def apply_package_to_blueprint(
    page_kind: str,
    package: dict[str, Any],
    images: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    blueprint = load_blueprint(page_kind if page_kind in {"standard", "case-study"} else "standard")
    if page_kind == "case-study":
        return apply_case_study_package(blueprint, package, images)
    return apply_standard_package(blueprint, package, images)


def score_page_relevance(topic: str, page: dict[str, Any]) -> int:
    text = f"{topic} {page.get('name') or ''} {page.get('slug') or ''}".lower()
    tokens = [t for t in re.split(r"[^a-z0-9]+", topic.lower()) if len(t) > 3]
    return sum(1 for token in tokens if token in text)


def discover_internal_links(
    topic: str,
    list_pages_fn: Callable[[], list[dict[str, Any]]],
    existing: list[dict[str, Any]] | None = None,
    limit: int = 4,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = list(existing or [])
    seen = {str(x.get("slug") or "").lstrip("/") for x in merged}
    candidates = sorted(list_pages_fn(), key=lambda p: score_page_relevance(topic, p), reverse=True)
    for page in candidates:
        slug = str(page.get("slug") or "").strip().lstrip("/")
        state = str(page.get("state") or "").upper()
        if not slug or slug in seen:
            continue
        if slug in {"old", "home", "index"} or len(slug) < 4:
            continue
        if state not in {"PUBLISHED_OR_SCHEDULED", "PUBLISHED", "DRAFT"}:
            continue
        if score_page_relevance(topic, page) < 1:
            continue
        merged.append({"label": str(page.get("name") or slug), "slug": slug})
        seen.add(slug)
        if len(merged) >= limit:
            break
    return merged


def resolve_page_images(package: dict[str, Any], campaign_slug: str) -> dict[str, dict[str, Any]]:
    slugify, infer_trade_from_topic, build_visual_topic_from_topic, _ = _import_hubspot_content_helpers()
    topic = str(package.get("topic") or "")
    trade = str(package.get("trade") or infer_trade_from_topic(topic))
    visual_topic = str(package.get("visualTopic") or build_visual_topic_from_topic(topic, trade))

    import sys

    if str(CONTENT_BIN) not in sys.path:
        sys.path.insert(0, str(CONTENT_BIN))
    from hubspot_content import resolve_topic_hero_image  # noqa: E402

    images: dict[str, dict[str, Any]] = {}
    placements = (
        ("hero", "hero"),
        ("section1", "section_roi"),
        ("section2", "section_scale"),
    )
    for key, placement in placements:
        visual = f"{visual_topic} {placement.replace('_', ' ')}"
        try:
            resolved = resolve_topic_hero_image(
                visual,
                trade,
                f"{campaign_slug}-{key}",
                topic=topic,
            )
            images[key] = {
                "url": resolved.get("url"),
                "alt": f"Vixxo {package.get('hero', {}).get('headline') or topic} — {key}",
                "source": resolved.get("source"),
            }
        except Exception as exc:
            images[key] = {"url": None, "alt": "", "source": "error", "error": str(exc)}
    return images


def page_brief_for_topic(topic: str, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    slugify, infer_trade_from_topic, build_visual_topic_from_topic, package_brief_for_topic = (
        _import_hubspot_content_helpers()
    )
    content_brief = package_brief_for_topic(topic)
    page_kind = infer_page_kind(topic)
    suggested_slug = infer_slug(topic, page_kind, slugify)
    trade = infer_trade_from_topic(topic)
    return {
        "topic": topic,
        "pageKind": page_kind,
        "suggestedSlug": suggested_slug,
        "suggestedTemplatePath": template_path_for_kind(page_kind, cfg or {}),
        "suggestedTrade": trade,
        "suggestedVisualTopic": build_visual_topic_from_topic(topic, trade),
        "brandVoice": content_brief.get("brandVoice"),
        "aeoRules": [
            "Lead with a 40–60 word answer-first paragraph directly addressing the topic.",
            "Write 3–5 FAQ pairs in natural-language question form (People Also Ask style).",
            "Phrase section H2s as questions where it fits the topic.",
            "Include entity-rich copy: Vixxo, facilities management, multi-site, licensed technicians.",
            "Add internal links only to slugs verified to exist in HubSpot.",
            "htmlTitle ≤60 chars; metaDescription ≤155 chars with primary keyword.",
        ],
        "seoRules": content_brief.get("compositionRules", [])[:4],
        "imageRules": [
            "Resolve hero + two section images from topic (Adobe Stock → Shutterstock → Pexels → Wikimedia → trade fallback).",
            "Upload all images to HubSpot File Manager under /page-images/{slug}/.",
        ],
        "draftOnlyRules": [
            "Always create pages with state DRAFT.",
            "Never publish unless the user explicitly says publish / approved / go live.",
        ],
        "requiredSchema": PAGE_PACKAGE_SCHEMA,
        "workflow": [
            "1. User provides a topic.",
            "2. Cursor calls hubspot_pages_get_page_brief (optional — schema is in the skill).",
            "3. Cursor composes the full page package per requiredSchema (VP+ FM voice, full AEO).",
            "4. Cursor calls hubspot_pages_stage_page with the package — stages immediately as DRAFT.",
            "5. Return editor URL, slug, template, image sources, and internal links.",
        ],
        "moduleBlueprint": {
            "standard": "reference/blueprint-standard.json",
            "case-study": "reference/blueprint-case-study.json",
        },
        "templateInference": {
            "standard": "solution/industry FM topics",
            "case-study": "case study / customer story / pilot program",
            "contact": "contact / sales / demo requests",
        },
    }


def normalize_package(package: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    slugify, infer_trade_from_topic, build_visual_topic_from_topic, _ = _import_hubspot_content_helpers()
    topic = str(package.get("topic") or "").strip()
    if not topic:
        raise SystemExit("package.topic is required")

    normalized = copy.deepcopy(package)
    normalized["topic"] = topic
    page_kind = infer_page_kind(topic, normalized)
    normalized["pageKind"] = page_kind
    normalized.setdefault("trade", infer_trade_from_topic(topic))
    normalized.setdefault("visualTopic", build_visual_topic_from_topic(topic, normalized["trade"]))
    normalized.setdefault("slug", infer_slug(topic, page_kind, slugify))
    normalized.setdefault("pageName", topic.title())
    normalized.setdefault("htmlTitle", f"{topic.title()[:50]} | Vixxo")
    normalized.setdefault(
        "metaDescription",
        str(normalized.get("answerFirst") or "")[:155],
    )
    normalized.setdefault("hero", {})
    normalized["hero"].setdefault("headline", topic.title())
    if page_kind == "case-study":
        normalized["hero"].setdefault("subheadline", "A FACILITY MANAGEMENT CASE STUDY")
    normalized.setdefault("faqs", [])
    normalized.setdefault("sections", [])
    normalized.setdefault("internalLinks", [])
    normalized["templatePath"] = template_path_for_kind(page_kind, cfg)
    return normalized


def build_create_payload(
    package: dict[str, Any],
    blueprint_applied: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": package["pageName"],
        "slug": package["slug"],
        "htmlTitle": package["htmlTitle"],
        "metaDescription": package["metaDescription"],
        "templatePath": package["templatePath"],
        "state": "DRAFT",
        "widgetContainers": blueprint_applied.get("widgetContainers") or {},
        "widgets": blueprint_applied.get("widgets") or {},
    }
    domain = cfg.get("defaultDomain")
    if domain:
        payload["domain"] = domain
    hero_url = (package.get("_images") or {}).get("hero", {}).get("url")
    if hero_url:
        payload["featuredImage"] = hero_url
        payload["featuredImageAltText"] = (package.get("_images") or {}).get("hero", {}).get("alt") or package["pageName"]
        payload["useFeaturedImage"] = True
    return payload


def write_review_md(
    package: dict[str, Any],
    result: dict[str, Any],
    staging_root: Path,
) -> Path:
    slugify, _, _, _ = _import_hubspot_content_helpers()
    slug_key = slugify(str(package.get("slug") or package.get("topic") or "page"))
    out_dir = staging_root / slug_key
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# HubSpot Page — {package.get('pageName')}",
        "",
        f"**Topic:** {package.get('topic')}",
        f"**Slug:** {package.get('slug')}",
        f"**Template:** {package.get('templatePath')}",
        f"**State:** DRAFT",
        "",
        "## Editor",
        "",
        f"- [Open in HubSpot]({result.get('editorUrl')})",
        "",
        "## SEO",
        "",
        f"- **Title:** {package.get('htmlTitle')}",
        f"- **Meta:** {package.get('metaDescription')}",
        "",
        "## Images",
        "",
    ]
    for key, meta in (package.get("_images") or {}).items():
        lines.append(f"- **{key}:** {meta.get('source')} — {meta.get('url')}")
    lines.extend(["", "## Internal links", ""])
    for link in package.get("internalLinks") or []:
        lines.append(f"- [{link.get('label')}](/{str(link.get('slug')).lstrip('/')})")
    lines.extend(["", "## FAQ count", "", str(len(package.get("faqs") or []))])
    path = out_dir / "REVIEW.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
