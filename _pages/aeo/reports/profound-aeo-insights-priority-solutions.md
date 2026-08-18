# Profound AEO Insights — Priority Solution Pages

**Generated:** 2026-07-31  
**Mode:** Insights-only (Profound MCP offline in agent session — reconnect for live data)  
**Domain:** www.vixxo.com  
**Skills routed:** `ai-seo`, `competitors`, `copywriting`, `seo-audit`, `hubspot-page-aeo`

---

## Executive summary

The AEO revamp program has **94 clone drafts staged** (AEO Draft Ready). All pages
use generic **Profound Items Addressed** placeholders from batch processing — **31
CLEAN-6-1 rows still need live Profound-backed items** after MCP reconnect.

**Immediate action:** Connect Profound MCP, re-run visibility + citation pulls for
the pages below, then replace placeholder tracker text with prompt-specific fixes.

**One open tracker row:** `about-us/contact-us` — SEO **In Progress** (clone staged;
Profound Items Addressed empty).

---

## Profound MCP status

| Check | Status |
| --- | --- |
| Configured in `.cursor/mcp.json` | Yes (`https://mcp.tryprofound.com/mcp`) |
| Connected this session | **No** — connect in Settings → Tools & MCPs → `profound` |
| Fallback data used | Public page fetch + existing clone reports |

**Reconnect, then run:** `whoami` → `list_categories` → `list_domains` →
`get_visibility_report` + `get_citations_report` + `get_prompt_answers` per topic.

---

## Priority pages for Profound pull

High commercial intent + existing clone drafts ready for Profound validation:

| Slug | Assignee | AEO (after) | SEO (after) | Primary keyword (tracker) |
| --- | --- | ---: | ---: | --- |
| `solutions/hvac` | Neetu Rao | 95 | 90 | solutions hvac facility management |
| `solutions/commercial-handyman-services` | Erica Huddleston | 95 | 90 | solutions commercial handyman |
| `beverage-equipment-vixxo` | Neetu Rao | 95 | 90 | beverage equipment vixxo facility management |
| `facility-management-solutions` | Neetu Rao | 95 | 100 | facility management solutions |
| `solutions/food-service-equipment` | Erica Huddleston | 95 | 100 | solutions food service equipment |
| `about-us/contact-us` | Neetu Rao | 95 | 90 | about us contact us facility management |

---

## Page-level insights (pre-Profound)

### `solutions/hvac`

**Live page gap (public fetch):** Long narrative intro; weak answer-first block;
no visible FAQ; H2s are topic labels not question-phrased prompts.

**Profound prompts to pull:**
- "commercial HVAC maintenance for multi-site retail"
- "who manages HVAC for restaurant chains"
- "facilities management HVAC service provider network"

**Expected citation gap:** Competitor FM/HVAC providers likely cited for multi-site
HVAC queries; Vixxo clone has FAQ + answer-first staged — validate with
`get_citations_report`.

**Marketing skills:** `ai-seo` (answer blocks), `copywriting` (intro rewrite),
`competitors` (citation gap), `schema` (FAQ markup verify on clone).

**Clone editor:** [HubSpot](https://app-na2.hubspot.com/page-ui/7718689/management/pages/website-pages/367604474560/edit)

---

### `solutions/commercial-handyman-services`

**Live page gap:** Strong body copy but buried answer; no FAQ block on live page;
multiple H2s are statements not questions.

**Profound prompts to pull:**
- "commercial handyman services for retail chains"
- "multi-site handyman facilities management"
- "handyman repairs for restaurant locations"

**Marketing skills:** `ai-seo`, `copy-editing`, `content-strategy` (topic cluster
with `/facility-management/trade-services`).

**Clone editor:** [HubSpot](https://app-na2.hubspot.com/page-ui/7718689/management/pages/website-pages/367619079904/edit)

---

### `about-us/contact-us` (SEO In Progress)

**Live page gap:** Form-first layout; minimal entity-rich FM copy; no FAQ;
weak for AI extraction ("how do I contact Vixxo for facilities management?").

**Clone status:** AEO 95 / SEO 90 staged — answer-first intro, FAQ, internal links
per `_pages/aeo/reports/about-us-contact-us.md`.

**Profound prompts to pull:**
- "how to contact Vixxo facilities management"
- "Vixxo customer support multi-site FM"
- "request quote Vixxo facility services"

**Recommended Profound Items Addressed (pending live pull):**
- Visibility gap: contact/intent prompts — answer-first intro names Vixxo FM scope
- Prompt answer gap: FAQ mirrors "how do I reach Vixxo for multi-site FM?" structure
- Citation gap: link clone to `/facility-management-solutions` and `/solutions/hvac`

**Action:** Mark SEO **Draft Ready** in tracker; complete Profound Items after MCP pull.

**Clone editor:** [HubSpot](https://app-na2.hubspot.com/page-ui/7718689/management/pages/website-pages/367619079918/edit)

---

## Recommended actions

| Priority | Action | Skill | Owner |
| --- | --- | --- | --- |
| P0 | Connect Profound MCP in Cursor | — | User |
| P0 | Pull visibility + citations for 6 priority slugs above | `vixxo-profound-aeo` | Agent |
| P0 | Replace generic Profound Items in tracker (31 CLEAN-6-1 rows) | `hubspot-page-aeo` | Agent |
| P1 | Close `about-us/contact-us` SEO row → Draft Ready | `hubspot-page-aeo` | Neetu Rao |
| P1 | Validate clone FAQ schema in HubSpot editor | `schema`, `seo-audit` | Assignee |
| P2 | Site-wide citation competitor brief | `competitors`, `competitor-profiling` | Marketing |
| P2 | LLM test queries post-publish | `ai-seo` | Assignee |

---

## Suggested LLM test queries (site-wide)

Run in ChatGPT, Perplexity, and Google AI Overviews after publish:

1. What is Vixxo and who do they serve for multi-site facility management?
2. How does Vixxo handle commercial HVAC for retail and restaurant chains?
3. Who provides commercial handyman services for multi-location businesses?
4. How do I contact Vixxo for facility management services?
5. What beverage equipment maintenance services does Vixxo offer?

---

## Next run (after Profound connected)

```
Pull Profound AEO insights for solutions/hvac and update Profound Items Addressed
in the tracker for all Erica Huddleston CLEAN-6-1 rows.
```

**Draft only — no pages published.**
