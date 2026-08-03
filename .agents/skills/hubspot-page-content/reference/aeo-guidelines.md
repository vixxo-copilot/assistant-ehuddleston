# AEO Guidelines — HubSpot Site Pages

Full AEO is the primary bar for `hubspot-page-content`. SEO metadata supports
answer-engine visibility; it does not replace structured on-page answers.

## Profound-driven inputs (required when MCP connected)

Before writing or revamping page copy, pull AEO signals from **Profound MCP**
via the `vixxo-profound-aeo` skill:

- **Visibility gaps** → question-phrased H2s and primary keyword
- **Prompt answers** → answer-first intro (40–60 words) and FAQ Q&As
- **Citation report** → internal links to cited or under-cited vixxo.com paths
- **Sentiment themes** → tone and objection handling in body copy

Record resolved items in tracker column **Profound Items Addressed**. Do not
guess visibility or citation data if Profound is disconnected.

## Required on every staged page

1. **Answer-first intro** — 40–60 words directly answering the topic query.
2. **Single H1** — in the hero module only.
3. **Question-phrased H2s** — where natural (People Also Ask alignment).
4. **FAQ block** — minimum 3 Q&As with schema-friendly markup.
5. **Entity-rich copy** — facilities management, multi-site, service provider
   network, work orders, retail/QSR/grocery context as relevant.
6. **Internal links** — 2–4 links to real vixxo.com pages (verify slugs exist).
7. **SEO fields** — `htmlTitle` ≤60 chars, `metaDescription` ≤155 chars.

## Voice

Match `hubspot-content`: VP+ multi-site FM audience, operational credibility,
no residential framing, no hype.

## Images

- Hero background — topic-matched via `hubspot-content` image pipeline.
- One section image — topic detail shot in the first body section.
- Text-only fallback is not acceptable for this agent (full visual pass).

## Draft-only

Never publish unless the user explicitly says publish / go live / approved.
