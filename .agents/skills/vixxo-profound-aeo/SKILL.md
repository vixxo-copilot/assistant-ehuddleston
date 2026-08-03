---
name: vixxo-profound-aeo
description: >-
  Orchestrates Profound AEO insights with marketing skills for Vixxo website
  work. Use when the user asks for AEO insights, Profound data, AI visibility,
  citation gaps, sentiment themes, or wants marketing skills applied to
  answer-engine optimization on vixxo.com. Also use when running ai-seo,
  seo-audit, content-strategy, or hubspot-page-aeo in this repo — pull
  Profound signals first, then route to the right marketingskills workflow.
---

# Profound + Marketing Skills — AEO Integration

Connect **Profound MCP** (live AEO analytics) with **coreyhaines31/marketingskills**
(49 marketing skills) and Vixxo HubSpot page workflows.

## When to use

- User asks for AEO insights, Profound reports, or AI visibility on Vixxo
- User wants to optimize a page using Profound + marketing skills together
- User runs `ai-seo`, `seo-audit`, `content-strategy`, or `hubspot-page-aeo` on
  this repo — **start here** before generic skill playbooks
- User references citation gaps, prompt answers, visibility score, or sentiment
- Weekly revamp automation or tracker row work (`_pages/aeo/`)

**Not for:** Profound setup/auth (see `.cursor/mcp.README.md`), net-new pages
without AEO context (`hubspot-page-content`), or non-Vixxo domains.

## Prerequisites

| Requirement | Location |
| --- | --- |
| Profound MCP connected | Cursor → Settings → Tools & MCPs → `profound` → Connect |
| HubSpot pages MCP | `.cursor/mcp.json` → `hubspot-pages` |
| Marketing skills installed | `.agents/skills/` (49 from marketingskills) |
| Product context (optional) | `.agents/product-marketing.md` — read if present |
| AEO tracker | `_pages/aeo/Vixxo-AEO-Website-Revamp-Status.xlsx` |

If Profound MCP is missing or unauthenticated, **stop** and ask the user to
connect it. Do not guess visibility, citation, or sentiment data.

---

## Workflow overview

```
Profound MCP (signals)
        ↓
  Insight synthesis
        ↓
  Marketing skill routing  ←→  HubSpot clone/draft (if page work)
        ↓
  Tracker + report update
```

---

## Step 1 — Profound discovery (always first)

Run this sequence via **Profound MCP** (`profound`):

1. `whoami` — confirm org access
2. `list_categories` — resolve Vixxo category ID
3. `list_domains` — confirm `www.vixxo.com`

For the target topic, slug, or tracker row, pull as needed:

| Profound tool | What it tells you |
| --- | --- |
| `get_visibility_report` | Share of voice, weak prompts, model-level gaps |
| `get_citations_report` | Which vixxo.com paths are cited vs competitors |
| `get_prompt_answers` | Actual AI answers behind weak visibility |
| `get_sentiment_report` | Themes to reinforce or counter in copy |
| `get_bots_report` | Crawl/agent access patterns |
| `get_referrals_report` | Referral traffic from AI engines |

Full call patterns: [reference/profound-mcp-playbook.md](reference/profound-mcp-playbook.md)

Capture a short **Profound snapshot** before any edits:

- Top 3–5 prompts where Vixxo is invisible or under-cited
- Competitor URLs/pages winning citations
- Sentiment themes (positive gaps / negative risks)
- vixxo.com paths already cited (protect and link to)

---

## Step 2 — Route to marketing skills

Use Profound signals to pick skills — do not run all 49. Full routing table:
[reference/skill-routing.md](reference/skill-routing.md)

| Profound signal | Primary skills | Output |
| --- | --- | --- |
| Low visibility on prompts | `ai-seo`, `content-strategy` | Answer blocks, topic clusters, LLM test queries |
| Citation gaps vs competitors | `ai-seo`, `competitors`, `competitor-profiling` | Gap analysis, differentiation angles |
| Weak prompt answers | `copywriting`, `copy-editing`, `ai-seo` | Answer-first intros, FAQ Q&As |
| Sentiment themes | `marketing-psychology`, `copy-editing` | Tone adjustments, objection handling |
| On-page / meta issues | `seo-audit`, `schema` | Title/meta, H1/H2, FAQ schema |
| Internal link opportunities | `site-architecture`, `ai-seo` | Links to cited or under-cited slugs |
| Scale opportunities | `programmatic-seo`, `content-strategy` | Template pages for prompt clusters |
| Social / email amplification | `social`, `emails`, `hubspot-content` | Posts/emails for newly optimized pages |

**HubSpot page revamps:** hand off to `hubspot-page-aeo` for clone → AEO pass →
SEO pass → tracker update. This skill supplies the Profound snapshot; that skill
executes the page workflow.

---

## Step 3 — Apply AEO edits (page work)

When editing a HubSpot clone or drafting content, translate Profound into:

1. **Answer-first intro** (40–60 words) matching how AI engines summarize the
   top prompt from `get_prompt_answers`
2. **Question-phrased H2/H3** aligned to high-value prompts from visibility report
3. **FAQ block** (≥3 Q&As) filling gaps in prompt answers
4. **Internal links** to vixxo.com paths Profound shows as cited or under-cited
5. **Entity-rich FM copy** — Vixxo, multi-site, licensed technicians (see
   [aeo-guidelines.md](../hubspot-page-content/reference/aeo-guidelines.md))

Record **Profound Items Addressed** in the tracker — list specific prompts,
themes, or citation gaps fixed this pass.

---

## Step 4 — Insights-only mode (no page edits)

When the user only wants AEO insights (no HubSpot changes):

1. Run Step 1 (Profound discovery)
2. Synthesize using `ai-seo` audit framework + Profound data
3. Deliver structured report:

```markdown
## Profound AEO Insights — {topic}

### Visibility summary
- Score / share of voice: …
- Top weak prompts: …

### Citation landscape
- Vixxo cited paths: …
- Competitor paths winning: …

### Prompt answer gaps
- {prompt}: current AI answer vs recommended Vixxo angle

### Recommended actions
| Priority | Action | Marketing skill |
| --- | --- | --- |
| P0 | … | ai-seo / copywriting / … |

### Suggested LLM test queries
- …
```

Save to `_pages/aeo/reports/{slug-or-topic}.md` when scoped to a tracker row.

---

## Step 5 — Tracker + report (page revamps)

When working a tracker row, update:

| Tracker column | Source |
| --- | --- |
| AEO Score (Before/After) | Pre/post audit rubric + Profound baseline |
| SEO Score (Before/After) | `seo-audit` checklist |
| Primary Keyword | Top Profound prompt or visibility gap |
| Profound Items Addressed | Prompts/themes/gaps fixed |
| LLM Test Queries | From `get_prompt_answers` + ai-seo |
| Report File | `_pages/aeo/reports/{slug}.md` |

Tracker config: `_pages/aeo/sharepoint-tracker.config.yaml`

---

## Guardrails

- **Data-backed only** — no invented visibility or citation stats; use Profound MCP
- **Draft-only page edits** — never publish without explicit approval
- **Clone-only revamps** — never PATCH live published pages
- **Vixxo voice** — VP+ multi-site FM audience; see `hubspot-content` / brand skills
- **Upstream skills** — marketingskills in `.agents/skills/` may update via
  `npx skills update`; this skill is the stable Vixxo + Profound overlay

---

## Related

| Resource | Purpose |
| --- | --- |
| [skill-routing.md](reference/skill-routing.md) | Profound signal → marketing skill map |
| [profound-mcp-playbook.md](reference/profound-mcp-playbook.md) | MCP tool sequence and parameters |
| `hubspot-page-aeo` | Weekly page revamp workflow |
| `ai-seo` / `seo-audit` | Generic AEO/SEO playbooks (use after Profound pull) |
| `.cursor/mcp.README.md` | Profound auth and wiring |
| `.cursor/automations/hubspot-page-aeo-seo.md` | Weekly automation template |
