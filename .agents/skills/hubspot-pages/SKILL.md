---
name: hubspot-pages
description: >-
  Migrates existing HubSpot website pages to a new CMS template and creates new
  draft pages. Uses hubspot-pages MCP + OAuth. Draft-first — never publish without approval.
---

# HubSpot CMS Pages Agent

Migrate existing **site pages** and **landing pages** to a target template, and
create new pages as **DRAFT** for the Vixxo website refresh workflow.

## When to use

- User asks to move HubSpot pages to a new template
- User needs new website pages created on a specific template
- User references website refresh, CMS pages, or template migration
- User has (or will provide) a page inventory list

## MCP server

`hubspot-pages` (local) — CMS Pages API (`/cms/pages/2026-03/`).

| Tool | Purpose |
| --- | --- |
| `hubspot_pages_get_config` | Validate portalId + targetTemplatePath + OAuth |
| `hubspot_pages_list_templates` | Find template path in Design Manager |
| `hubspot_pages_list_pages` | Discover existing pages by slug/name/state |
| `hubspot_pages_get_page` | Fetch page + JSON backup |
| `hubspot_pages_migrate_template` | Change `templatePath` on one page |
| `hubspot_pages_create_page` | Create new DRAFT page |
| `hubspot_pages_update_page` | Update SEO/metadata on draft or live page |
| `hubspot_pages_run_inventory` | Batch migrate + create from inventory YAML |
| `hubspot_pages_publish_page` | Publish only after explicit user approval |

## Primary workflow

### 1 — Setup check

Call `hubspot_pages_get_config`. Confirm:

- `auth.oauthConnected` is true (same OAuth as hubspot-content)
- `config.targetTemplatePath` is set (Design Manager path, **no leading slash**)
- `config.portalId` matches the Vixxo portal (7718689)

If OAuth is missing, run `hubspot_pages_login` or:

```powershell
py -3 .cursor/bin/hubspot-content/hubspot_content.py login
```

### 2 — Confirm template

Call `hubspot_pages_list_templates` with a search term (theme name) to verify
`targetTemplatePath`. Update `.agents/skills/hubspot-pages/config.yaml` if needed.

### 3 — Build inventory

Copy `_pages/inventory/pages.inventory.example.json` → `pages.inventory.json`
(or use the YAML example).

Fill in:

- **migrate** — existing pages (by `slug` or `pageId`)
- **create** — new pages (name, slug, SEO fields)

### 4 — Dry run

`hubspot_pages_run_inventory` with `{ "dryRun": true }` — review planned actions.

### 5 — Execute

`hubspot_pages_run_inventory` with `{ "dryRun": false }`.

Each migrated page gets a JSON backup under `_pages/staging/{pageId}/`.

### 6 — Manual content pass (required)

Template migration updates `templatePath` only. Module/layout content must be
rebuilt in the HubSpot page editor. Return editor URLs from tool output and
instruct the user to:

1. Open each editor URL
2. Map content into the new template modules
3. Verify SEO, URLs, and internal links
4. Preview before publish

### 7 — Publish (explicit approval only)

Only when the user says **publish**, **go live**, or **approved to publish**:

`hubspot_pages_publish_page` with `{ "pageId": "...", "confirm": true }`

## Single-page shortcuts

**Migrate one page by slug:**

```
Use hubspot-pages — migrate /about-us to the 2026 template.
```

Agent calls `hubspot_pages_migrate_template` with `{ "slug": "about-us" }`.

**Create one new page:**

```
Use hubspot-pages — create draft page "Retail FM Solutions" at slug retail-fm-solutions.
```

## Guardrails

**Draft-first.** New pages are always created with `state: DRAFT`.

**Template migration is not content migration.** Changing templates may reset
drag-and-drop areas. Always backup (`get-page`) before bulk runs.

**Published pages.** Updates go to the `/draft` endpoint so live content stays
safe until publish.

**Never publish** without explicit user approval.

**Never use `HUBSPOT_ACCESS_TOKEN`** for writes — OAuth attributes edits to the
signed-in user (shared with hubspot-content).

## Config files

| File | Purpose |
| --- | --- |
| `.agents/skills/hubspot-pages/config.yaml` | portalId, targetTemplatePath, defaultDomain |
| `_pages/inventory/pages.inventory.yaml` | Batch migrate + create lists |
| `_pages/staging/` | Page JSON backups + run summaries (gitignored) |

## HubSpot OAuth scopes

The public app needs at minimum:

- `content` (CMS pages + templates)
- Optionally add `pages-write` if HubSpot requires it for your portal tier

Same `HUBSPOT_CLIENT_ID` / `HUBSPOT_CLIENT_SECRET` as hubspot-content.

## Example user prompts

```
Use hubspot-pages — list all site pages still on the old template.
```

```
Use hubspot-pages — dry-run the page inventory, then migrate and create drafts.
```

```
Use hubspot-pages — create draft pages for the new Solutions section from pages.inventory.yaml.
```

## Related

- **AEO page staging from topic:** `.agents/skills/hubspot-page-content/SKILL.md`
- Blog/email content (different agent): `.agents/skills/hubspot-content/SKILL.md`
- Remote HubSpot CRM MCP: `hubspot` in `.cursor/mcp.json`
- Automation template: `.cursor/automations/hubspot-pages-migration.md`
