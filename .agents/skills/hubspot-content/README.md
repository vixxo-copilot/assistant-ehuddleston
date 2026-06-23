# HubSpot FM Content Bundle

Cursor skill + MCP that stages **blog draft**, **email draft**, **social `.txt` copy**,
**300×300 branded social image**, and a consolidated **`REVIEW.md`** — all draft-only.

## Install

### 1. Skill (this folder)

From a Vixxo assistant repo that includes `.agents/skills/`:

```bash
# Already present if you cloned assistant-ehuddleston with skills
ls .agents/skills/hubspot-content/SKILL.md
```

Or install from the shared skills registry when published:

```bash
npx skills add vixxo-copilot/agent-skills --skill hubspot-content
```

### 2. MCP server

Copy or symlink `.cursor/bin/hubspot-content/` into your repo and add to `.cursor/mcp.json`:

```json
"hubspot-content": {
  "command": "node",
  "args": [".cursor/bin/hubspot-content/hubspot-content-mcp.mjs"]
}
```

Install Node dependencies once:

```bash
cd .cursor/bin/hubspot-content && npm install
```

### 3. HubSpot credentials

```bash
cp .agents/skills/hubspot-content/config.example.yaml .agents/skills/hubspot-content/config.yaml
```

Edit `config.yaml`: `portalId`, `contentGroupId`, `blogAuthorId`.

Add to `.env`:

```env
HUBSPOT_ACCESS_TOKEN=pat-...
```

Private App scopes: **`content`** (required), **`files`** (optional, for image upload).

Restart Cursor after env/MCP changes.

### 4. Fonts (social image script)

Place Wix Madefor Text in `.agents/skills/hubspot-content/assets/fonts/`:

- `WixMadeforText-ExtraBold.ttf` (preferred)
- or `WixMadeforText.ttf`

Requires `pip install Pillow`.

## Usage

In Cursor chat:

```
Use hubspot-content — suggest facilities management topics and stage a full bundle.
```

Or with your own topic:

```
Use hubspot-content — stage blog, email, and LinkedIn for: multi-site HVAC PM programs.
```

## Output

Every run ends with `_content/social-ready/{campaign}/REVIEW.md`:

| Section | Content |
| --- | --- |
| Blog draft | HubSpot editor URL |
| Email draft | HubSpot editor URL |
| Social post | Path to `linkedin-post.txt` |
| Social image | HubSpot CDN URL |
| HubSpot Social | Link to paste post manually |

## MCP tools

| Tool | Purpose |
| --- | --- |
| `hubspot_content_get_config` | Validate portal IDs |
| `hubspot_content_create_blog_draft` | Stage blog HTML draft |
| `hubspot_content_create_email_draft` | Stage marketing email draft |
| `hubspot_content_stage_social_pack` | Write `{platform}-post.txt` |
| `hubspot_content_write_review_doc` | Write consolidated `REVIEW.md` |
| `hubspot_content_breeze_image_prompt` | Breeze AI prompt per channel |
| `hubspot_content_get_staged_summary` | JSON summary of staged assets |

## Publishing this skill

This skill lives in `vixxo-copilot/assistant-ehuddleston` under
`.agents/skills/hubspot-content/`. To publish to the shared registry
(`vixxo-copilot/agent-skills`), mirror this folder and open a PR there.

## License

Internal Vixxo use. HubSpot API subject to HubSpot terms.
