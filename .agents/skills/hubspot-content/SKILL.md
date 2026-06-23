---
name: hubspot-content
description: >-
  Plans and stages Vixxo facilities-management content bundles in HubSpot from
  a user topic: get brief, compose copy, stage blog + email + social + images +
  REVIEW.md in one MCP call. Draft-only — never publish or send without approval.
---

# HubSpot FM Content Bundle

Stage a **blog + email + social** content bundle for Vixxo facilities
management marketing. Final deliverable is always a single **`REVIEW.md`**
with every link in one place (same format as the hvac-pm-fm-2026 example).

## When to use

- User asks to create/stage HubSpot marketing content
- User gives a **topic prompt** or asks for **facilities management topic ideas**
- User wants blog + email + social for a campaign

## MCP server

`hubspot-content` (local) — one-call content package staging + individual channel tools.

| Tool | Purpose |
| --- | --- |
| `hubspot_content_get_package_brief` | Schema + suggested trade/visualTopic |
| `hubspot_content_stage_content_package` | Full bundle staging (all images 150 DPI) |
| `hubspot_content_get_campaign_links` | Consolidated link table for a staged campaign |
| `hubspot_content_refresh_campaign_images` | Re-render 150 DPI images on existing drafts |
| Individual channel tools | Blog, email, social, REVIEW.md, Breeze prompts |

## Topic → content package (primary workflow)

When a user provides a **topic**, Cursor composes copy and stages everything in **two MCP calls**:

### Step 1 — Get brief

`hubspot_content_get_package_brief` with `{ "topic": "..." }`

Returns composition schema, brand rules, suggested trade/visualTopic, and suggested campaign slug.

### Step 2 — Compose + stage

Cursor writes blog, email, and social copy per the schema (VP+ multi-site FM voice).
Then call **`hubspot_content_stage_content_package`** once with the full `package` object.

This stages in one step:

- **Topic-matched hero photo** (Adobe Stock → Shutterstock preview → trade fallback) for blog featured image, email banner background, and social card background
- Blog draft
- Email draft (150 DPI banner + body text)
- Social `.txt` copy
- 150 DPI social image (Wix Extra Bold)
- `REVIEW.md` with all links + topic-matched Breeze prompts

### Example user prompt

```
Use hubspot-content — create a content package for topic: emergency plumbing service due to frozen pipes in winter.
```

### Example MCP flow

1. `hubspot_content_get_package_brief` → `{ "topic": "emergency plumbing frozen pipes winter" }`
2. Cursor composes `package` JSON (see [reference/content-package.schema.json](reference/content-package.schema.json))
3. `hubspot_content_stage_content_package` → `{ "package": { ... } }`
4. Return consolidated link table + `REVIEW.md` path

## Setup

1. `HUBSPOT_ACCESS_TOKEN` in `.env` (Private App: `content`, optional `files`)
2. Copy [config.example.yaml](config.example.yaml) → `config.yaml` — fill
   `portalId`, `contentGroupId`, `blogAuthorId`
3. Wire MCP in `.cursor/mcp.json` (see [README.md](README.md))
4. Install `WixMadeforText-ExtraBold.ttf` in `assets/fonts/` (see README)
5. Restart Cursor MCP

## Guardrails

**Draft-only.** Never publish blog, send email, or schedule social without
explicit user approval ("publish", "send", "schedule", "approved").

**No CRM tasks. No contact notes.** Social copy lives in `.txt` only.

## Workflow

### 0. Topic (required before staging)

**User provided a topic?** → Confirm campaign slug + target date, then continue.

**No topic yet?** → Read [reference/topic-ideas.md](reference/topic-ideas.md),
offer 5–8 FM topics, wait for pick or custom brief. Do not stage until confirmed.

### 1. Plan

Use [templates/brief.md](templates/brief.md): audience (VP+ multi-site FM),
key messages, SEO meta, email subject/preheader, social hook.

Brand: Wix Madefor Text Extra Bold, Vixxo Green `#8E992E`, Gray `#3E4543`.

### 2. Compose

- [templates/blog-post.md](templates/blog-post.md)
- [templates/marketing-email.md](templates/marketing-email.md)
- [templates/social-post.md](templates/social-post.md)

Email body starts with **`Hi,`** only (no `{{contact.firstname}}`).

Social: short headline on image optional; **no subheading** on the 300×300 card.

### 3. Stage

Write HTML to `_content/staging/{campaign}/` first, then stage via MCP (prefer
`bodyFile` / `htmlBodyFile` for blog and email — avoids CLI length limits).

| Channel | Action |
| --- | --- |
| Blog | `hubspot_content_create_blog_draft` with `bodyFile` — sync `post_body` widget |
| Email | `hubspot_content_create_email_draft` with `htmlBodyFile` |
| Social copy | `hubspot_content_stage_social_pack` → `_content/social-ready/{campaign}/linkedin-post.txt` |
| Social image | `hubspot_content_upload_social_image` — generate 300×300 + upload to File Manager |
| Breeze | Included in `REVIEW.md`; prompts match the topic visual brief automatically |

**Topic-matched images:** Preferred workflow — generate hero in Cursor from `visualTopic`, save `ai-hero-bg.png`, call `hubspot_content_refresh_campaign_images` with `bgFile`. Automated fallback: Adobe Stock → Shutterstock → Pexels → Wikimedia → Vixxo trade hero. Set `ADOBE_STOCK_API_KEY` in `.env` for hands-off stock search.

Blog editor URL: `/blog/{portalId}/editor/{postId}` — not `/editor/post/{postId}`.

**Windows shell:** Use `Set-Location <repo>; py -3 ...` — PowerShell 5.x does not support `&&`.

### 4. Write REVIEW.md (mandatory)

Call `hubspot_content_write_review_doc` with campaign slug, blog ID, email ID,
social image CDN URL, social copy path, and **`visualTopic`** (auto-includes Breeze prompts).

Template: [templates/REVIEW.template.md](templates/REVIEW.template.md)

### 5. Return to user

Always return the **consolidated table** plus `REVIEW.md` path:

| Asset | Path / link |
| --- | --- |
| **Blog draft** | HubSpot editor URL |
| **Email draft** | HubSpot editor URL |
| **Social post (txt)** | Absolute path to `linkedin-post.txt` |
| **Social image** | HubSpot CDN URL |
| **HubSpot Social** | Social UI URL |
| **One doc** | `{repo}/_content/social-ready/{campaign}/REVIEW.md` |

## Example prompts

```
Use hubspot-content — create a content package for topic: multi-site HVAC PM programs.
```

```
Use hubspot-content — suggest FM topics and stage a bundle for the one I pick.
```

```
Use hubspot-content — stage blog + email + LinkedIn for topic: refrigeration PM in grocery retail.
```

## Limitations

- **Draft-only:** never publish, send, or schedule unless the user explicitly requests it
- Use `hubspot_content_verify_campaign_draft_status` to confirm all staged assets are DRAFT
- HubSpot Social has no API — paste from `.txt` manually
- Breeze AI images are UI-only (prompts live in `REVIEW.md`)
- Published emails cannot be edited via API — clone draft first
- Social image script requires `WixMadeforText-ExtraBold.ttf` in `assets/fonts/` (no system-font fallback)
- Branded images render at **150 DPI** for sharp email/social output
- `HUBSPOT_ACCESS_TOKEN` needs **`files`** scope for social image upload

## Additional resources

- FM topic bank: [reference/topic-ideas.md](reference/topic-ideas.md)
- Images: [reference/images.md](reference/images.md)
- Install & GitHub: [README.md](README.md)
