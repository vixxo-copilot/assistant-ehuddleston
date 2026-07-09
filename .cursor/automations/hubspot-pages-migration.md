# HubSpot CMS Pages — Migration Automation

Template for a Cursor Automation that runs the `hubspot-pages` skill against
the page inventory. Create in Cursor → Automations.

## Name

`HubSpot website page migration`

## Description

Process the page inventory: migrate existing pages to the target template and
create new draft pages. Never publish without human approval.

## Trigger

- **Type:** Manual (recommended for migration batches)
- **Alternative:** Schedule weekly during website refresh sprint

## Tools / MCP

- `hubspot-pages` (local — workspace `.cursor/mcp.json`)
- Optional: `hubspot` remote MCP for CRM context

Ensure HubSpot OAuth is connected (`hubspot_pages_auth_status` → `readyToStage`).

## Instructions (agent prompt)

```
Use the hubspot-pages skill.

1. Call hubspot_pages_get_config — stop if targetTemplatePath or OAuth is missing.
2. Read _pages/inventory/pages.inventory.yaml (or ask user to create from example).
3. Run hubspot_pages_run_inventory with dryRun:true — show planned migrate/create table.
4. After user approves the plan, run hubspot_pages_run_inventory with dryRun:false.
5. Return a summary table: action, page name/slug, pageId, templatePath, editorUrl, status.
6. Remind user to rebuild module content in HubSpot editor for migrated pages.
7. Do NOT publish unless user explicitly says publish/approved/go live.
```

## Inventory file

Maintain [`_pages/inventory/pages.inventory.yaml`](../../_pages/inventory/pages.inventory.yaml).

## To finish in editor

- Confirm `hubspot-pages` MCP is connected
- Fill `config.yaml` targetTemplatePath
- Fill page inventory migrate/create lists

## Related

- Skill: `.agents/skills/hubspot-pages/SKILL.md`
- MCP: `.cursor/bin/hubspot-pages/`
