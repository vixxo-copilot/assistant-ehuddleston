# HubSpot AEO Site Page Agent

Create **AEO/SEO-optimized draft site pages** in HubSpot from a topic prompt.
Uses the **CLEAN-6-1-theme child X** templates and maps copy into live module
fields (`widgetContainers`).

See [SKILL.md](SKILL.md) for the full workflow.

## Setup

1. Complete [hubspot-pages setup](../hubspot-pages/README.md) (`config.yaml`, OAuth or private app token).
2. Ensure `hubspot-pages` MCP is enabled in `.cursor/mcp.json`.
3. Optional: copy [config.example.yaml](config.example.yaml) for case-study/contact template overrides.

## Example prompt

```
Use hubspot-page-content — create a HubSpot page for topic: multi-site HVAC preventive maintenance for retail chains.
```

## MCP tools

| Tool | Purpose |
| --- | --- |
| `hubspot_pages_get_page_brief` | Schema + AEO rules + slug/template inference |
| `hubspot_pages_stage_page` | Compose → images → modules → DRAFT site page |
