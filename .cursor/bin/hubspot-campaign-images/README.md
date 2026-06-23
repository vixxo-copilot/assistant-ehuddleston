# HubSpot Campaign Images MCP

Local companion MCP for automatic campaign stock photo resolution and
File Manager upload. Pairs with the remote `hubspot` MCP for
`manage_landing_page` SET_MODULE_FIELDS insertion.

## Activate

1. Add to `.env`:
   - `HUBSPOT_ACCESS_TOKEN` (Private App with `files` scope) for uploads
   - Optional `SHUTTERSTOCK_API_TOKEN` for preview search
2. **Restart Cursor** (or reload MCP) to pick up `hubspot-campaign-images` in `.cursor/mcp.json`.
3. Reauthorize main `hubspot` MCP with `landingpages-read` + `landingpages-write` for landing page drafts.

## Tools

- `hubspot_campaign_resolve_image`
- `hubspot_campaign_insert_image`
- `hubspot_campaign_breeze_prompts`

See `.agents/skills/hubspot-campaign-images/SKILL.md` for full workflow.

## Breeze AI

No public API. Use `hubspot_campaign_breeze_prompts` for UI copy-paste into
**Generate with AI** in the HubSpot image picker.
