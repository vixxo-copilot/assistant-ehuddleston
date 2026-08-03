# HubSpot CMS Pages MCP

Local MCP for HubSpot **site pages** and **landing pages** — template migration,
draft creation, **AEO page staging from topics**, **AEO + SEO page revamps**
(clone workflow), and batch inventory runs.

## Quick start

1. OAuth (shared with hubspot-content):

   ```powershell
   py -3 .cursor/bin/hubspot-content/hubspot_content.py login
   ```

2. Config:

   ```powershell
   copy .agents\skills\hubspot-pages\config.example.yaml .agents\skills\hubspot-pages\config.yaml
   ```

   Set `targetTemplatePath` from Design Manager (no leading `/`).

3. Inventory:

   ```powershell
   copy _pages\inventory\pages.inventory.example.yaml _pages\inventory\pages.inventory.yaml
   ```

4. Wire MCP in `.cursor/mcp.json` (already added if you pulled latest).

5. Install MCP deps:

   ```powershell
   cd .cursor\bin\hubspot-pages
   npm install
   ```

6. Restart Cursor MCP.

## CLI (without MCP)

```powershell
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py get-config
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py get-page-brief --topic "HVAC PM for retail"
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py stage-page --dry-run --package-file path/to/package.json
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py list-templates --search vixxo
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py migrate-template --slug about-us
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py run-inventory --dry-run
```

Topic → full AEO page workflow: see `.agents/skills/hubspot-page-content/SKILL.md`.

Existing page revamp (AEO + SEO on clone drafts): see `.agents/skills/hubspot-page-aeo/SKILL.md`.

```powershell
py -3 .cursor/bin/hubspot-pages/hubspot_pages.py clone-page --slug solutions/hvac
py -3 .cursor/bin/hubspot-pages/fix_url_hyperlinks.py
```

`fix_url_hyperlinks.py` renames C/D to **Before URL** / **After URL** and applies
clickable Excel hyperlinks (openpyxl `Hyperlink` + blue underline font).

## API surface

Uses HubSpot CMS Pages API `2026-03`:

- `GET/POST/PATCH /cms/pages/2026-03/site-pages`
- `GET/POST/PATCH /cms/pages/2026-03/landing-pages`
- `GET /cms/v3/templates`

## Attribution

Reuses `.hubspot/oauth-token.json` from hubspot-content OAuth login.
