# Campaign images

## Topic-matched heroes (primary — `stage_content_package`)

When staging a full content package, hero photography is **resolved from the user's topic** at generation time:

1. **Cursor AI** (recommended) — generate hero from `visualTopic` in Cursor, save to `_content/staging/{campaign}/ai-hero-bg.png`, then `refresh-campaign-images --bg-file` (source: `cursor_ai`)
2. **Adobe Stock** — if `ADOBE_STOCK_API_KEY` is set (best automated match)
3. **Shutterstock preview** — if `SHUTTERSTOCK_API_TOKEN` is set
4. **Pexels** — if `PEXELS_API_KEY` is set
5. **Wikimedia Commons** — automatic topic search (no key; Openverse may fail on corporate networks)
6. **Topic keyword match** — verified Vixxo CDN photo (e.g. plumbing, HVAC)
7. **Trade fallback** — Vixxo CDN hero for the inferred trade

The resolved URL is used for:

- Blog featured image (1200×675 @ 150 DPI → 2500×1406 px, uploaded to File Manager)
- Email banner background (150 DPI composite with Wix Extra Bold headline)
- Social card background (150 DPI composite)

`trade` and `visualTopic` are auto-inferred from the topic when omitted. Override only when you need sharper art direction.

Staging output includes `imageSource`, `visualTopic`, and `image-resolution.json` in the campaign staging folder.

## Breeze AI prompts (manual upgrade path)

HubSpot Breeze has **no public API**. `stage_content_package` writes **topic-matched Breeze prompts** to `REVIEW.md` so a human can regenerate in HubSpot UI if preferred.

| Channel | Breeze channel key | Where in HubSpot |
|---|---|---|
| Blog | `blog_featured` | Blog post editor → Featured image → Generate with AI |
| Email | `email_header` | Marketing email editor → Header image → Generate with AI |
| Social | `social` | Marketing → Social → Add image → Generate with AI |

For each channel, call `hubspot_content_breeze_image_prompt` with the package `visualTopic`.

### HubSpot UI steps

1. Open the staged draft in HubSpot editor
2. Click image area → **Select image** → **Generate with AI**
3. Paste the `breezePrompt` from `REVIEW.md`
4. Generate → review → **Save to files**
5. Confirm insertion

## Individual channel tools

`hubspot_content_upload_social_image` and email banner attach still accept `--trade` or `--bg-url` when staging channels separately (without the full package workflow).

## Guardrail

Image generation and draft staging do not publish content. No asset goes live without explicit user approval.
