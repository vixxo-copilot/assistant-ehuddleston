---
name: hubspot-campaign-images
description: >-
  Resolve, upload, and auto-insert HubSpot-native campaign stock images into
  landing page modules. Companion to the hubspot MCP manage_landing_page tool.
  Uses File Manager upload + SET_MODULE_FIELDS; Breeze AI prompts when no API.
---

# HubSpot Campaign Images

Companion to the remote `hubspot` MCP (`https://vixxonow.com/mcp/hubspot`).
Adds automatic stock photo resolution and File Manager upload for campaign
landing pages.

## Limitations (important)

- **HubSpot Breeze AI image generation has no public API.** It is UI-only
  (Content editor > Generate with AI). This skill/MCP uploads validator-safe
  images and provides exact Breeze prompts for manual replacement.
- **Shutterstock via HubSpot UI** is also UI-only. Optional `SHUTTERSTOCK_API_TOKEN`
  enables preview search + upload through this pipeline.
- **Landing page writes** still require `landingpages-read` + `landingpages-write`
  on the main HubSpot MCP connector.

## MCP server

Local MCP: `hubspot-campaign-images` (wired in `.cursor/mcp.json`).

| Tool | Purpose |
| --- | --- |
| `hubspot_campaign_resolve_image` | Resolve URL + alt + Breeze prompt for a placement |
| `hubspot_campaign_insert_image` | Full pipeline → `manage_landing_page` SET_MODULE_FIELDS payload |
| `hubspot_campaign_breeze_prompts` | All standard HVAC PM campaign Breeze prompts |

## Environment

```env
# Required for File Manager upload
HUBSPOT_ACCESS_TOKEN=

# Optional — Shutterstock preview search (license before publish)
SHUTTERSTOCK_API_TOKEN=
```

Restart Cursor MCP after adding env vars.

## Workflow

1. Create/populate landing page via `hubspot_call_upstream_tool` → `manage_landing_page`.
2. Read module IDs: `action=MODULES`.
3. Call `hubspot_campaign_insert_image` with `prompt`, `placement`, `contentId`, `moduleId`.
4. Apply returned payload via `hubspot_call_upstream_tool` → `manage_landing_page` SET_MODULE_FIELDS.

## CLI (no MCP)

```bash
python .cursor/bin/hubspot-campaign-images/hubspot_campaign_images.py pipeline \
  --prompt "Nationwide retail HVAC portfolio" \
  --placement hero \
  --upload \
  --content-id 123456 \
  --module-id hero_1
```

## Placements

| Key | Use |
| --- | --- |
| `hero` | Landing page hero |
| `section_roi` | Executive ROI / boardroom |
| `section_scale` | Multi-site retail scale |
| `section_technician` | Commercial PM execution |
| `email_header` | Email banner |

## Breeze AI — manual UI steps

1. Open landing page in HubSpot editor.
2. Click image module → **Select image** → **Generate with AI**.
3. Paste prompt from `hubspot_campaign_breeze_prompts` for that placement.
4. **Save to files** then confirm insertion.

## Image validator

Never use external placeholder URLs (Unsplash direct, via.placeholder.com).
This pipeline uses HubSpot static CDN placeholders or HubSpot File Manager URLs
after upload.
