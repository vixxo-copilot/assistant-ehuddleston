# HubSpot CMS Pages Agent

Migrate HubSpot website pages to a new template and create new draft pages.

See [SKILL.md](SKILL.md) for the full agent workflow.

## Setup checklist

1. OAuth: `py -3 .cursor/bin/hubspot-content/hubspot_content.py login`
2. `config.example.yaml` → `config.yaml` — set `targetTemplatePath`
3. `pages.inventory.example.yaml` → `pages.inventory.yaml` — list pages
4. Enable `hubspot-pages` MCP in `.cursor/mcp.json`
5. `cd .cursor/bin/hubspot-pages && npm install`

## Example prompt

```
Use hubspot-pages — dry-run the page inventory, then migrate existing pages and create new drafts.
```
