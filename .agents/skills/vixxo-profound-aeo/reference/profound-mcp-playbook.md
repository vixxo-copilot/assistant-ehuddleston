# Profound MCP Playbook — Vixxo AEO

Endpoint: `https://mcp.tryprofound.com/mcp` (configured as `profound` in
`.cursor/mcp.json`).

Auth: OAuth via Cursor MCP UI, or optional `PROFOUND_API_KEY` for Bearer auth.
See `.cursor/mcp.README.md` and `.env.example`.

---

## Discovery sequence (every session)

```
1. whoami
2. list_categories          → note Vixxo category_id
3. list_domains             → confirm www.vixxo.com
```

Do not proceed with visibility/citation claims until `whoami` succeeds.

---

## Report tools (by investigation goal)

### Visibility — "Are we showing up for key prompts?"

```
get_visibility_report
  category_id: <from list_categories>
  domain: www.vixxo.com
  date_range: last 30 days (or user-specified)
```

**Extract:** share of voice, prompt list with scores, model breakdown, trend.

**Route to:** `ai-seo`, `content-strategy`, tracker **Primary Keyword** column.

---

### Citations — "Which URLs win citations?"

```
get_citations_report
  category_id: <from list_categories>
  domain: www.vixxo.com
```

**Extract:** cited vixxo.com paths, competitor URLs, uncited prompt clusters.

**Route to:** `competitors`, `hubspot-page-aeo`, internal link plan.

---

### Prompt answers — "What do AI engines actually say?"

```
get_prompt_answers
  prompts: [<top 5–10 weak prompts from visibility report>]
  models: [all available, or user-specified]
```

**Extract:** verbatim AI answers, cited sources, Vixxo mention yes/no.

**Route to:** `copywriting`, FAQ blocks, **LLM Test Queries** tracker column.

---

### Sentiment — "What themes attach to us or competitors?"

```
get_sentiment_report
  category_id: <from list_categories>
  domain: www.vixxo.com
```

**Extract:** positive/negative/neutral themes, competitor sentiment contrast.

**Route to:** `marketing-psychology`, `copy-editing`, hero/FAQ tone.

---

### Bots — "Are AI crawlers reaching our pages?"

```
get_bots_report
  domain: www.vixxo.com
```

**Extract:** crawl frequency by path, blocked resources, agent user-agents.

**Route to:** `seo-audit` (robots, indexability), `schema`.

---

### Referrals — "Is AI traffic hitting specific pages?"

```
get_referrals_report
  domain: www.vixxo.com
```

**Extract:** referral sources (ChatGPT, Perplexity, etc.), landing paths.

**Route to:** `analytics`, `attribution`, prioritize revamp rows.

---

## Mapping Profound → tracker columns

| Profound output | Tracker column |
| --- | --- |
| Weak prompt cluster | Primary Keyword |
| Prompts used in FAQ/H2 work | LLM Test Queries |
| Prompts/themes/gaps fixed | Profound Items Addressed |
| Pre-revamp visibility baseline | AEO Score (Before) — note Profound context in report |
| Post-revamp target prompts | AEO Score (After) — re-check after publish (manual) |

---

## Fallback when MCP unavailable

1. Stop page revamp work that depends on citation/visibility data
2. Insights-only mode: use Mia's weekly exports or SharePoint
   `Vixxo_AEO_Heading_Analysis.xlsx` if user provides path
3. Label report **"Profound MCP offline — fallback data"**

Never fabricate Profound metrics.

---

## Example Profound Items Addressed (tracker)

```
- Visibility gap: "multi-site HVAC maintenance provider" — added answer-first intro + FAQ Q1
- Citation gap: competitor /solutions/hvac cited; added internal links + question H2
- Sentiment: "slow response time" theme — countered with licensed technician network copy
- Prompt answer gap: ChatGPT omitted Vixxo — FAQ mirrors AI answer structure with brand entity
```
