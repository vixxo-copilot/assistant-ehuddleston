# HubSpot AEO + SEO Page Revamp — Weekly Automation

Template for a Cursor Automation that runs the `hubspot-page-aeo` skill.
Create in Cursor → Automations.

## Name

`HubSpot AEO + SEO weekly page revamp`

## Description

Pick the next assigned tracker row, clone the live page, apply AEO and SEO
passes on the draft clone, and update the SharePoint workbook. Never publish.

## Trigger

- **Type:** Scheduled weekly (recommended) or Manual
- **Scope:** One CLEAN-6-1 page per run

## Tools / MCP

- `profound` — AEO visibility, citations, prompt answers, sentiment (required)
- `hubspot-pages` (local — workspace `.cursor/mcp.json`)
- `ms365` (org-mode) — optional SharePoint tracker upload

Ensure HubSpot OAuth is ready (`hubspot_pages_get_config` → `readyToWork`).
Ensure Profound is connected (Settings → Tools & MCPs → `profound` → Connect).

## Instructions (agent prompt)

```
Use vixxo-profound-aeo + hubspot-page-aeo (Profound-driven AEO + SEO revamp).

1. Read _pages/aeo/sharepoint-tracker.config.yaml and open the local workbook
   (or fetch from SharePoint if local copy is stale).
2. Select the next AEOPageStatus row where Template Family = CLEAN-6-1 and
   (AEO Status = Not Started OR SEO Status = Not Started OR In Progress),
   matching the current user's Assignment when possible.
3. Pull Profound AEO signals (vixxo-profound-aeo Step 1): whoami,
   list_categories, list_domains, then get_visibility_report,
   get_citations_report, get_prompt_answers, get_sentiment_report for the
   page topic/slug. Stop if profound MCP is not connected.
4. Clone the live page: hubspot_pages_clone_page (or clone-page CLI).
   Write After URL (column D) to the tracker; run fix_url_hyperlinks.py so
   Before/After links are clickable.
5. Fetch live page baseline; record AEO/SEO scores (Before) and current meta.
6. Apply AEO pass on clone using Profound snapshot + aeo-guidelines (answer-first,
   question H2s, FAQs from prompt gaps, internal links from citation report).
   Route to ai-seo / copywriting / seo-audit skills as needed.
7. Apply SEO pass (title ≤60, meta ≤155, H1/H2, internal links, keyword).
   Update clone via hubspot_pages_update_page.
8. Update tracker: statuses, scores (After), meta fields, Primary Keyword,
   Profound Items Addressed, LLM Test Queries, SEO Notes, editor URL, report.
9. Write _pages/aeo/reports/{slug}.md with Profound snapshot + before/after.
10. Save workbook locally; attempt SharePoint upload if not locked.
11. Return: live URL, clone URL, editor URL, AEO/SEO status, Profound items,
    report path.
12. Do NOT publish unless the user explicitly says publish/approved/go live.
```

## Example input

```
Run weekly revamp for my assigned tracker rows.
```

## Related

- Orchestration: `.agents/skills/vixxo-profound-aeo/SKILL.md`
- Page revamp: `.agents/skills/hubspot-page-aeo/SKILL.md`
- Tracker: `_pages/aeo/Vixxo-AEO-Website-Revamp-Status.xlsx`
- MCP: `.cursor/bin/hubspot-pages/`
