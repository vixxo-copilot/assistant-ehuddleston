---
name: hubspot-content
description: >-
  Plans and stages Vixxo facilities-management content bundles in HubSpot:
  blog draft, email draft, social .txt copy, branded 300x300 image, and a
  consolidated REVIEW.md. Accepts a user topic or suggests FM content ideas.
  Draft-only — never publish or send without explicit approval.
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

`hubspot-content` (local) — blog/email drafts, social `.txt`, `REVIEW.md`.

Optional: `hubspot-campaign-images` for email banner upload.

## Setup

1. `HUBSPOT_ACCESS_TOKEN` in `.env` (Private App: `content`, optional `files`)
2. Copy [config.example.yaml](config.example.yaml) → `config.yaml` — fill
   `portalId`, `contentGroupId`, `blogAuthorId`
3. Wire MCP in `.cursor/mcp.json` (see [README.md](README.md))
4. Restart Cursor MCP

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

| Channel | Action |
| --- | --- |
| Blog | `hubspot_content_create_blog_draft` — sync `post_body` widget with HTML body |
| Email | `hubspot_content_create_email_draft` + banner via campaign-images if available |
| Social copy | `hubspot_content_stage_social_pack` → `_content/social-ready/{campaign}/linkedin-post.txt` |
| Social image | Run [scripts/generate_social_image.py](scripts/generate_social_image.py), upload to HubSpot File Manager, note CDN URL |
| Breeze | `hubspot_content_breeze_image_prompt` per channel (UI-only generation) |

Blog editor URL: `/blog/{portalId}/editor/{postId}` — not `/editor/post/{postId}`.

### 4. Write REVIEW.md (mandatory)

Call `hubspot_content_write_review_doc` with campaign slug, blog ID, email ID,
social image CDN URL, and social copy path.

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
Use hubspot-content — suggest FM topics and stage a bundle for the one I pick.
```

```
Use hubspot-content — stage blog + email + LinkedIn for topic: refrigeration PM in grocery retail.
```

```
Use hubspot-content — write REVIEW.md for campaign hvac-pm-fm-2026.
```

## Limitations

- HubSpot Social has no API — paste from `.txt` manually
- Breeze AI images are UI-only
- Published emails cannot be edited via API — clone draft first

## Additional resources

- FM topic bank: [reference/topic-ideas.md](reference/topic-ideas.md)
- Images: [reference/images.md](reference/images.md)
- Install & GitHub: [README.md](README.md)
