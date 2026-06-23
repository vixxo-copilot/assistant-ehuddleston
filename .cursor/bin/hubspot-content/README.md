# HubSpot Content MCP v2.6.0

Local MCP for staging blog drafts, marketing email drafts, and social copy files
in HubSpot. **Draft-only** — no publish, send, or schedule endpoints.

## Topic → content package

Users supply **any free-form topic** (required). The agent composes copy and stages
a full bundle; images are matched to that topic.

1. `hubspot_content_get_package_brief` — pass `{ "topic": "your topic here" }`
2. Compose `package` JSON (topic required; campaign slug optional)
3. `hubspot_content_stage_content_package`
4. **Recommended for topic-matched photos:** generate hero in Cursor from `visualTopic`,
   save `_content/staging/{campaign}/ai-hero-bg.png`, then
   `hubspot_content_refresh_campaign_images` with `bgFile`
5. `hubspot_content_verify_campaign_draft_status` — confirm nothing is live

### Image matching priority

1. **Cursor AI** (`bgFile` / `--bg-file`) — best match to user topic
2. Adobe Stock (`ADOBE_STOCK_API_KEY`)
3. Shutterstock / Pexels (API keys in `.env`)
4. Wikimedia Commons (automatic, topic-first search)
5. Verified Vixxo trade hero fallback

Stock search uses the user's **topic string first**, then keyword bundles with
whole-word matching (avoids false hits like `light` inside `daylight`).

## Setup

1. Add `HUBSPOT_ACCESS_TOKEN` to `.env` (Private App scopes: `content`, optional `files`).
2. Copy `.agents/skills/hubspot-content/config.example.yaml` to `config.yaml`
   and fill in `portalId`, `contentGroupId`, `blogAuthorId`.
3. Restart Cursor MCP to load `hubspot-content` from `.cursor/mcp.json`.

On Windows the MCP runs via `node` directly (loads `.env` automatically).

## Tools

- `hubspot_content_get_package_brief` — schema + suggested trade/visualTopic for **any topic**
- `hubspot_content_stage_content_package` — one-call full bundle staging (150 DPI images)
- `hubspot_content_refresh_campaign_images` — re-render images; optional `bgFile` for Cursor AI heroes
- `hubspot_content_verify_campaign_draft_status` — read-only draft/live check
- `hubspot_content_get_campaign_links` — consolidated link table
- Individual channel tools (blog, email, social, REVIEW.md, Breeze prompts)

All campaign images render at **150 DPI**: blog hero 2500×1406, email banner 1250×352, social 625×625.

See `.agents/skills/hubspot-content/SKILL.md` for the full agent workflow.

## CLI (no MCP)

```powershell
Set-Location C:\path\to\repo
py -3 .cursor\bin\hubspot-content\hubspot_content.py get-package-brief --topic "your topic"
py -3 .cursor\bin\hubspot-content\hubspot_content.py stage-content-package --package-file path\to\package.json
py -3 .cursor\bin\hubspot-content\hubspot_content.py refresh-campaign-images --campaign slug --bg-file path\to\ai-hero-bg.png
py -3 .cursor\bin\hubspot-content\hubspot_content.py verify-campaign-draft-status
```
