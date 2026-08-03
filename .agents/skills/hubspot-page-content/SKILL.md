---
name: hubspot-page-content
description: >-
  Creates and stages AEO/SEO-optimized draft website pages in HubSpot from a
  user topic. Maps copy and images into CLEAN-6-1-theme modules. Draft-only —
  never publish without approval.
---

# HubSpot AEO Site Page Staging

Stage a **full draft site page** on www.vixxo.com from a **topic prompt**.
Content is composed for **full AEO** (answer-first intro, FAQ, PAA-style
sections, entity-rich FM copy) and mapped into **CLEAN-6-1-theme child X**
template modules via the HubSpot API.

## When to use

- User gives a **topic** and wants a new website page staged in HubSpot
- User asks for AEO/SEO-optimized site page content on the Vixxo CLEAN-6-1 theme
- User references `hubspot-page-content` or "create a HubSpot page for topic …"

**Not for:** blog/email/social bundles (`hubspot-content`), or bulk template
migration (`hubspot-pages` inventory workflow).

## MCP server

`hubspot-pages` (local) — reuses CMS Pages API + image pipeline from `hubspot-content`.

| Tool | Purpose |
| --- | --- |
| `hubspot_pages_get_config` | Validate portalId, templates, auth |
| `hubspot_pages_get_page_brief` | Composition schema + AEO rules for a topic |
| `hubspot_pages_list_pages` | Discover internal link targets |
| `hubspot_pages_stage_page` | Stage full DRAFT page (copy + images + modules) |

## Topic → staged page (primary workflow)

When a user provides a **topic**, compose and stage in **one turn** (no
pre-approval in chat — user reviews in HubSpot editor).

### Step 1 — Setup check

`hubspot_pages_get_config` — confirm `readyToWork` and `targetTemplatePath`.

### Step 2 — Get brief (optional if skill loaded)

`hubspot_pages_get_page_brief` with `{ "topic": "..." }`

Returns `requiredSchema`, `aeoRules`, `brandVoice`, `suggestedSlug`,
`suggestedTemplatePath`, and module blueprint paths.

### Step 3 — Compose page package

Write the full `package` object per
[reference/page-package.schema.json](reference/page-package.schema.json).

**Mandatory AEO (priority over SEO):**

- `answerFirst` — 40–60 words, direct answer to the topic
- `faqs` — 3–5 natural-language Q&A pairs (schema-ready in FAQ module)
- Section `heading` values — phrase as questions where natural
- Entity-rich copy — Vixxo, facilities management, multi-site, licensed technicians
- `htmlTitle` ≤60 chars; `metaDescription` ≤155 chars

**Voice:** Match `hubspot-content` — VP+ multi-site FM, operational credibility.

**Slug:** Infer section prefix (`solutions/`, `industries/`, `resources/` for case studies).

**Template inference:**

| Topic signal | Template |
| --- | --- |
| Solution / industry FM topic | `clean-pro-home-opt-1.html` (standard inner page) |
| Case study / customer story | `clean-pro-case-study.html` |
| Contact / sales | `clean-pro-contact-us.html` |

**Internal links:** Call `hubspot_pages_list_pages` when helpful. Only link
slugs that exist. MCP staging also verifies links against live pages.

**Images:** Package staging resolves hero + two section images (topic-matched
stock pipeline). Do not skip image fields — full visual pass is required.

### Step 4 — Stage immediately

`hubspot_pages_stage_page` with `{ "package": { ... } }`

Creates a **DRAFT** `site-page` with:

- SEO metadata
- Hero H1 + hero background image
- Intro + answer-first paragraph
- Two content sections + FAQ block
- Section images
- Preserved CTA form + footer modules from blueprint

### Step 5 — Return summary

Always return:

| Field | Source |
| --- | --- |
| Editor URL | `editorUrl` |
| Page ID / slug | `page` object |
| Template used | `page.templatePath` |
| Image sources | `images` object |
| Internal links | `internalLinks` |
| Review file | `reviewPath` under `_pages/staging/` |

## Example user prompts

```
Use hubspot-page-content — create a HubSpot page for topic: LED lighting retrofit programs for multi-site retail.
```

```
Use hubspot-page-content — stage a draft page about emergency plumbing response for grocery chains.
```

## Guardrails

**Draft-only.** Never call `hubspot_pages_publish_page` unless the user
explicitly says publish / approved / go live.

**One topic → one page.** Do not create page clusters without explicit request.

**Stage immediately.** Do not wait for chat approval before calling
`hubspot_pages_stage_page`.

**Never publish** migrated or new pages without explicit approval.

**Template:** CLEAN-6-1-theme child X Vixxo Facility Solutions only.

## Config

| File | Purpose |
| --- | --- |
| `.agents/skills/hubspot-pages/config.yaml` | portalId, `targetTemplatePath`, `defaultDomain` |
| `.agents/skills/hubspot-page-content/config.yaml` | Optional case-study/contact template overrides |
| `reference/blueprint-standard.json` | Module shell for solution pages |
| `reference/blueprint-case-study.json` | Module shell for case studies |

## Related

- Template migration: `.agents/skills/hubspot-pages/SKILL.md`
- Blog/email/social: `.agents/skills/hubspot-content/SKILL.md`
- Automation: `.cursor/automations/hubspot-page-content.md`
