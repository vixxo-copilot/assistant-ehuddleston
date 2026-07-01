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

### 3. HubSpot credentials (OAuth — per user)

Create a [HubSpot public app](https://developers.hubspot.com/) (Vixxo can host one app for the team):

| Setting | Value |
|---|---|
| Redirect URI | `http://127.0.0.1:8765/callback` |
| Scopes | `content`, `files` |

Add to `.env`:

```env
HUBSPOT_CLIENT_ID=...
HUBSPOT_CLIENT_SECRET=...
```

Copy config and fill portal IDs:

```bash
cp .agents/skills/hubspot-content/config.example.yaml .agents/skills/hubspot-content/config.yaml
```

**Each person runs once** (opens browser, signs in as themselves):

```bash
python .cursor/bin/hubspot-content/hubspot_content.py login
```

Token saves to `.hubspot/oauth-token.json` (gitignored). HubSpot will attribute
blog/email edits to that user.

Check connection:

```bash
python .cursor/bin/hubspot-content/hubspot_content.py auth-status
```

Legacy fallback (not recommended): `HUBSPOT_ACCESS_TOKEN` private-app token.

Restart Cursor after env/MCP changes.

### 4. Fonts (social image script)

Preferred: place Wix Madefor Text in `.agents/skills/hubspot-content/assets/fonts/`:

- `WixMadeforText-ExtraBold.ttf` (required — used for all branded image headlines)
- or `WixMadeforText.ttf` (variable; not used when ExtraBold is present)

Campaign images render at **150 DPI**:

- Blog featured hero: 1200×675 display → 2500×1406 px
- Email header: 600×169 display → 1250×352 px
- Social card: 300×300 display → 625×625 px

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
| Breeze prompts | Blog, email, and optional social prompts |
| HubSpot Social | Link to paste post manually |

## MCP tools

| Tool | Purpose |
| --- | --- |
| `hubspot_content_get_package_brief` | **Step 1** — schema + rules for composing from a topic |
| `hubspot_content_stage_content_package` | **Step 2** — stage full bundle (blog, email, social, images, REVIEW.md) |
| `hubspot_content_login` | OAuth connect (browser) — per-user attribution |
| `hubspot_content_auth_status` | Show connected HubSpot user |
| `hubspot_content_logout` | Remove OAuth token |
| `hubspot_content_get_config` | Validate portal IDs + auth |
| `hubspot_content_create_blog_draft` | Stage blog HTML draft (`body` or `bodyFile`) |
| `hubspot_content_create_email_draft` | Stage marketing email draft (`htmlBody` or `htmlBodyFile`) |
| `hubspot_content_stage_social_pack` | Write `{platform}-post.txt` |
| `hubspot_content_upload_social_image` | Generate 300×300 card + upload to File Manager |
| `hubspot_content_write_review_doc` | Write consolidated `REVIEW.md` (include `visualTopic` for Breeze prompts) |
| `hubspot_content_breeze_image_prompt` | Breeze AI prompt per channel |
| `hubspot_content_get_staged_summary` | JSON summary of staged assets |

## Publishing this skill

This skill lives in `vixxo-copilot/assistant-ehuddleston` under
`.agents/skills/hubspot-content/`. To publish to the shared registry
(`vixxo-copilot/agent-skills`), mirror this folder and open a PR there.

## License

Internal Vixxo use. HubSpot API subject to HubSpot terms.
