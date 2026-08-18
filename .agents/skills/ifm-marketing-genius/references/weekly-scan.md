# Weekly IFM marketing scan

Use in **Brief** mode. Purpose: keep the operator current without drowning
them. One brief, not a news dump.

## Cadence

- Default: on request ("brief me," "what's new in IFM marketing").
- Recurring: only if the operator starts a loop (`/loop 1d` or similar) and
  wants this skill as the prompt. Do not start a loop unless asked.

## Pull order

1. **Profound** (if connected) — 3–5 prompts where Vixxo is weak or a
   competitor is over-cited. Follow `vixxo-profound-aeo` discovery. If MCP
   is down, say so and continue with public sources.
2. **Web search** — last 7–14 days unless they ask for a longer lookback.
   Query families:
   - `integrated facilities management` marketing OR strategy OR RFP
   - `facilities management` outsourcing trend retail OR restaurant
   - named competitors + "facilities" + "launch" OR "partnership" OR "AI"
   - IFMA / NRF / Facilities Dive / FacilitiesNet headlines
3. **Gong** (optional) — recurring objections this week if the ask is
   "what are buyers saying?"
4. **Repo context** — `_pages/aeo/` tracker or product-marketing.md if they
   want Vixxo-specific implication.

## Source quality

Prefer primary or trade press over listicles. Discard "10 AI tools for
marketers" unless there is an IFM application. Label vendor content as
vendor content.

## Brief template (always)

```markdown
# IFM marketing brief — [date]

## The one thing that matters
[Single sentence. If nothing material changed, say that.]

## Best practices to steal (max 5)
For each:
- Practice (what good operators are doing)
- Why it fits IFM (law or buyer job)
- Vixxo implication (one line)
- Do this week (one action)
- Source (link or "inference")

## Hype to ignore
[1–3 items and why the physics are wrong for this market]

## Competitive / category moves
[Only verified. No rumor.]

## AEO / demand capture
[Profound snapshot or "Profound not connected"]

## Drill (optional)
[One 10-minute exercise so the brief trains judgment]
```

Keep it narrow enough to read without scrolling sideways. No wall of text.

## Translation rule

Every "best practice" from general marketing must pass: *Would a VP of
Facilities forward this to procurement?* If not, it does not make the list
unless you are explicitly killing it in **Hype to ignore**.
