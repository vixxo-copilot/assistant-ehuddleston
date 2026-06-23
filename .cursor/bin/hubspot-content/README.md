# HubSpot Content MCP

Local MCP for staging blog drafts, marketing email drafts, and social copy files
in HubSpot. **Draft-only** — no publish, send, or schedule endpoints.

## Setup

1. Add `HUBSPOT_ACCESS_TOKEN` to `.env` (Private App scopes: `content`, optional `files`).
2. Copy `.agents/skills/hubspot-content/config.example.yaml` to `config.yaml`
   and fill in `portalId`, `contentGroupId`, `blogAuthorId`.
3. Restart Cursor MCP to load `hubspot-content` from `.cursor/mcp.json`.

On Windows the MCP runs via `node` directly (loads `.env` automatically). On macOS/Linux
you can still use `run-hubspot-content-mcp.sh` if preferred.

## Editor URLs

Blog drafts open at `/blog/{portalId}/editor/{postId}` (HubSpot redirects to `.../content`). Do **not** use `/editor/post/{postId}` — that route loads a blank skeleton.

The app host (`app-na2.hubspot.com`, etc.) is resolved from `config.yaml` or the
HubSpot account-info API.

## Tools

- `hubspot_content_get_config`
- `hubspot_content_create_blog_draft` / `hubspot_content_update_blog_draft`
- `hubspot_content_create_email_draft` / `hubspot_content_update_email_draft`
- `hubspot_content_stage_social_pack`
- `hubspot_content_write_review_doc`
- `hubspot_content_breeze_image_prompt`
- `hubspot_content_get_staged_summary`

See `.agents/skills/hubspot-content/SKILL.md` for the full agent workflow.

## CLI (no MCP)

```bash
python .cursor/bin/hubspot-content/hubspot_content.py get-config
python .cursor/bin/hubspot-content/hubspot_content.py create-blog-draft \
  --title "Title" --meta-description "Meta" --body "<p>HTML</p>"
```
