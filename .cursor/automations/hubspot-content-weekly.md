# HubSpot Content — Weekly Staging Automation

Template for a Cursor Automation that runs the `hubspot-content` skill on a
recurring schedule. Create this automation in Cursor → Automations using the
settings below.

## Name

`HubSpot weekly content staging`

## Description

Review the content calendar and stage draft blog, email, and social assets in
HubSpot for human approval. Never publish or send.

## Trigger

- **Type:** Schedule
- **Cadence:** Weekly (e.g. Monday 9:00 AM local)
- **Alternative:** Manual trigger when planning content week

## Tools / MCP

Enable MCP tools for the automation runtime:

- `hubspot-content` (local — must be configured in workspace `.cursor/mcp.json`)

Ensure `HUBSPOT_ACCESS_TOKEN` is available to the automation environment.

## Instructions (agent prompt)

```
Use the hubspot-content skill.

1. Read the content calendar at _content/calendar.md (create if missing) for
   items due in the next 7 days.
2. For each due item, run the full workflow: intake → plan → compose → stage.
3. Generate one HubSpot Breeze AI image prompt per content piece (blog, email,
   each social post) via hubspot_content_breeze_image_prompt.
4. Stage blog and email as HubSpot drafts only. Stage social as `.txt` copy under `_content/social-ready/`.
5. Return a weekly summary table: campaign, channels, HubSpot IDs, editor URLs,
   Breeze prompts (pending/completed), social copy paths.
6. Do NOT publish, send, or schedule anything. Wait for explicit approval.
```

## Content calendar file

Maintain [`_content/calendar.md`](../../_content/calendar.md) with entries like:

```markdown
## 2026-07-01 — HVAC PM Q3
- Channels: blog, email, linkedin
- Audience: VP+ retail FM
- Topic: Preventative maintenance ROI at scale
- CTA: Download portfolio assessment guide
```

## To finish in editor

- Confirm MCP servers are connected and authenticated
- Set schedule timezone
- Add notification destination (optional Slack/email when run completes)

## Related

- Skill: `.agents/skills/hubspot-content/SKILL.md`
- Batch script (Phase 3): `scripts/hubspot-content-batch.mjs`
