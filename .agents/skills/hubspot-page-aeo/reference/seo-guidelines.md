# SEO Guidelines — HubSpot Page Revamps

On-page SEO complements AEO for `hubspot-page-aeo`. Apply on **clone drafts**
only; live pages stay published until explicit human approval.

## Metadata (required)

| Field | Rule |
| --- | --- |
| `htmlTitle` | ≤60 characters; primary keyword near front; brand suffix optional (`\| Vixxo`) |
| `metaDescription` | ≤155 characters; include keyword + clear value prop + soft CTA |

Record staged values in tracker **Meta Title (After)** and **Meta Description (After)**.

## On-page structure

1. **Single H1** — hero module only; matches page intent.
2. **H2/H3 hierarchy** — logical outline; no skipped levels.
3. **Primary keyword** — in H1 or first 100 words; natural density (no stuffing).
4. **Internal links** — 2–4 links to verified live vixxo.com slugs (`hubspot_pages_list_pages`).
5. **Image alt text** — descriptive where modules expose alt fields.

## Schema & rich results

- FAQ module content should support FAQ schema where the template allows.
- Do not add unsupported custom schema via API unless template supports it.

## Scoring (tracker)

Use a simple 0–100 rubric or letter grade for **SEO Score (Before/After)**:

| Signal | Weight |
| --- | --- |
| Title + meta length/quality | 25% |
| H1/H2 structure | 20% |
| Keyword alignment | 20% |
| Internal links | 20% |
| Mobile/readability (short paragraphs) | 15% |

## Status values

| Status | Meaning |
| --- | --- |
| `Not Started` | Row seeded; no revamp work |
| `In Progress` | Clone created or draft being edited |
| `Draft Ready` | AEO + SEO pass complete on clone; ready for human review |
| `Published` | Human approved and live (agent does not set without explicit publish) |
| `Deferred (Legacy Template)` | Page not on CLEAN-6-1 |

## Draft-only

Never publish clone to replace live without explicit user approval.
