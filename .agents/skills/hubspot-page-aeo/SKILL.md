---
name: hubspot-page-aeo
description: >-
  Weekly AEO + SEO revamp workflow for existing Vixxo HubSpot site pages.
  Clones live pages to draft, applies answer-engine and on-page SEO passes,
  updates the SharePoint tracker. Draft-only — never publish without approval.
---

# HubSpot AEO + SEO Page Revamp

Revamp **existing published site pages** for **answer-engine optimization (AEO)**
and **on-page SEO** without touching live URLs. Work happens on **clone drafts**
tracked in the Marketing919 Excel workbook.

## When to use

- User asks to revamp, optimize, or audit an existing Vixxo website page
- User references the AEO tracker, weekly page audit, or Profound findings
- User wants AEO + SEO work on a specific slug or tracker row
- User references `hubspot-page-aeo`, `hubspot-page-aeo-seo`, or the revamp tracker

**Start with `vixxo-profound-aeo`** when Profound MCP is available — it pulls
visibility/citation/prompt data and routes to marketingskills before this
workflow executes page edits.

**Not for:** net-new pages from a topic (`hubspot-page-content`), bulk template
migration (`hubspot-pages`), or blog/email bundles (`hubspot-content`).

## Tracker

| Item | Location |
| --- | --- |
| Local workbook | `_pages/aeo/Vixxo-AEO-Website-Revamp-Status.xlsx` |
| SharePoint config | `_pages/aeo/sharepoint-tracker.config.yaml` |
| Table | `AEOPageStatus` on sheet `AEO Page Status` |

Key columns (side-by-side for comparison):

| Col | Header | Purpose |
| --- | --- | --- |
| C | **Before URL** | Published live page — Excel hyperlink |
| D | **After URL** | AEO/SEO clone draft — Excel hyperlink when clone exists |
| G–L | AEO/SEO Status & Scores | Before/after audit scores |
| M–N | Meta Title/Description (After) | Staged SEO meta on clone (not URL columns) |
| X | **Assignment** | Round-robin: Erica Huddleston, Neetu Rao, Mia Li |

## MCP / CLI

`hubspot-pages` (local) — same OAuth as `hubspot-content`.

| Tool / command | Purpose |
| --- | --- |
| **Profound MCP** (`profound`) | Visibility, citations, sentiment, prompt answers, bot/referral reports |
| `hubspot_pages_get_config` | Validate portal + OAuth |
| `hubspot_pages_get_page` | Fetch live page SEO + module content |
| `hubspot_pages_update_page` | Stage AEO/SEO changes on **clone draft only** |
| `hubspot_pages_clone_page` / `clone-page` | Clone live page → draft for revamp |
| `hubspot_pages_list_pages` | Verify internal link targets |

```powershell
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py clone-page --slug solutions/hvac
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py get-page --page-id <clone-id>
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py update-page --page-id <clone-id> --html-title "..." --meta-description "..."
```

## Unified workflow (per tracker row)

### 1 — Read tracker row

Open the workbook (local or SharePoint). Pick the next **CLEAN-6-1** row where
**AEO Status** or **SEO Status** is `Not Started` or `In Progress`, scoped to the
current **Assignment** owner when running as automation.

### 2 — Clone live page

```powershell
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py clone-page --slug <url-slug>
```

- Write **After URL** (column D) and clone **HubSpot Editor URL** to the tracker.
  Apply Excel hyperlinks via `fix_url_hyperlinks.py` after populating URLs.
- **Before URL** (column C) and the published page remain unchanged.

### 3 — Fetch live baseline

`hubspot_pages_get_page` on the **live** page ID/slug. Capture:

- `htmlTitle`, `metaDescription`
- H1/H2 structure, FAQ presence, internal links
- Module content for AEO gap analysis

Record **AEO Score (Before)** and **SEO Score (Before)** in the tracker
(use your audit rubric; leave blank if not yet scored).

### 3b — Pull Profound AEO signals (required when MCP connected)

Use the **Profound MCP** server (`profound` in `.cursor/mcp.json`) before
writing clone content. If the server is missing or unauthenticated, stop and ask
{{employee_name}} to connect it in Cursor (**Settings → Tools & MCPs → profound →
Connect**). Do not guess visibility or citation data.

Discovery sequence:

1. `whoami` — confirm org access
2. `list_categories` — resolve Vixxo category ID
3. `list_domains` — confirm `www.vixxo.com` hostname
4. For the page slug/topic, call as needed:
   - `get_citations_report` — cited URLs/paths on vixxo.com (gap vs competitors)
   - `get_visibility_report` — visibility score / share of voice by topic, model
   - `get_sentiment_report` — themes to reinforce or counter in copy
   - `get_prompt_answers` — actual AI answers behind weak visibility
   - `get_bots_report` / `get_referrals_report` — crawl/referral context for `www.vixxo.com`

Translate Profound output into concrete page edits:

- Question-phrased H2/H3 aligned to high-value prompts
- Answer-first intro that matches how AI engines summarize the topic
- FAQ Q&As drawn from prompt-answer gaps
- Internal links to pages Profound shows as cited or under-cited
- **Profound Items Addressed** — list specific prompts, themes, or citation gaps fixed

Fallback only when MCP is unavailable: Mia's weekly exports or
`Vixxo_AEO_Heading_Analysis.xlsx` on SharePoint.

### 4 — AEO pass (clone draft)

Apply per [hubspot-page-content/reference/aeo-guidelines.md](../hubspot-page-content/reference/aeo-guidelines.md):

- Answer-first intro (40–60 words)
- Question-phrased H2s where natural
- FAQ block (≥3 Q&As, schema-friendly)
- Entity-rich FM copy (Vixxo, multi-site, licensed technicians)
- LLM retrieval test queries → **LLM Test Queries** column

### 5 — SEO pass (clone draft)

Apply per [reference/seo-guidelines.md](reference/seo-guidelines.md) and
`hubspot-content` conventions:

- `htmlTitle` ≤60 chars, primary keyword near front
- `metaDescription` ≤155 chars, compelling + keyword
- Single H1 in hero; logical H2/H3 hierarchy
- 2–4 verified internal links to live vixxo.com slugs
- Schema where applicable (FAQ, Organization via modules)
- **Primary Keyword** → tracker column
- Staged values → **Meta Title (After)**, **Meta Description (After)**

Update clone via `hubspot_pages_update_page` (draft endpoint for live-source clones).

### 6 — Update tracker

| Field | Value |
| --- | --- |
| AEO Status / SEO Status | `Draft Ready` when clone is staged for review |
| AEO Score (After) / SEO Score (After) | Post-revamp scores |
| Meta Title (After) / Meta Description (After) | Staged clone values |
| Primary Keyword | Target query |
| SEO Notes | On-page changes applied |
| Profound Items Addressed | Items resolved this pass |
| Accomplishments / Notes | Summary for assignee |
| Last Updated / Updated By | Timestamp + agent/user |
| Report File | Path to `_pages/aeo/reports/{slug}.md` |

### 7 — Write report

Save `_pages/aeo/reports/{slug}.md` with before/after SEO, AEO checklist,
editor URL, and open items. Link path in **Report File** column.

### 8 — Return summary

Always return: live URL, clone URL, editor URL, AEO/SEO status, scores,
meta fields, primary keyword, report path, assignee.

**Never publish.** Do not call `hubspot_pages_publish_page` unless the user
explicitly says publish / approved / go live.

## Guardrails

- **Clone-only edits** — never PATCH the live published page for revamp work.
- **Draft-first** — all revamp output stays in draft until human approval.
- **Assignment round-robin** — do not reassign rows; respect existing **Assignment**.
- **CLEAN-6-1 scope** — skip or defer **Legacy** template rows unless asked.
- **One page per run** — unless user requests a batch.

## Config

| File | Purpose |
| --- | --- |
| `_pages/aeo/sharepoint-tracker.config.yaml` | SharePoint drive/item IDs + column map |
| `.cursor/bin/hubspot-pages/fix_url_hyperlinks.py` | Apply Before/After URL hyperlinks after clone |
| `.cursor/bin/hubspot-pages/url_hyperlink.py` | Shared hyperlink helper for tracker scripts |
| `.agents/skills/hubspot-pages/config.yaml` | portalId, templates, OAuth |
| `reference/seo-guidelines.md` | On-page SEO checklist for revamps |

## Related

- Profound + marketing skills: `.agents/skills/vixxo-profound-aeo/SKILL.md`
- New page from topic: `.agents/skills/hubspot-page-content/SKILL.md`
- Template migration: `.agents/skills/hubspot-pages/SKILL.md`
- Voice + meta limits: `.agents/skills/hubspot-content/SKILL.md`
- Automation: `.cursor/automations/hubspot-page-aeo-seo.md`
