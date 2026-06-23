# Breeze AI images (required — one per content piece)

Every staged asset must include **one HubSpot Breeze AI-generated image**.
HubSpot Breeze has **no public API** — the agent generates prompts and UI steps;
a human completes **Generate with AI** in HubSpot.

## Per-channel requirement

| Channel | Breeze channel key | Where in HubSpot |
|---|---|---|
| Blog | `blog_featured` | Blog post editor → Featured image → Generate with AI |
| Email | `email_header` | Marketing email editor → Header image → Generate with AI |
| Social (each post) | `social` | Marketing → Social → Add image → Generate with AI |

## Agent workflow

For each content piece, call `hubspot_content_breeze_image_prompt` with:

- `topic` — campaign visual brief (from content brief)
- `channel` — `blog_featured`, `email_header`, or `social`
- `audience` — optional, from brief

Include returned `breezePrompt` and `breezeUiSteps` in:

- Review summary for blog/email
- Social staging pack (`breezeImage` or `imagePrompt` on each post)
- CRM task body for social bundles

Prompts follow **Vixxo Brand Guidelines 2026** imagery rules: editorial,
authentic, bright natural light, commercial FM context, optimistic focal point.

## HubSpot UI steps (all channels)

1. Open the staged draft in HubSpot editor
2. Click image area → **Select image** → **Generate with AI**
3. Paste the `breezePrompt` from agent output
4. Generate → review → **Save to files**
5. Confirm insertion (featured image, email header, or social attachment)

## After Breeze generation

If the image is saved to File Manager and you have the HubSpot CDN URL:

- Blog: `hubspot_content_update_blog_draft` with `featuredImage` URL
- Email: update draft HTML with `<img src="..." alt="...">` header

If URL is not yet available, leave copy staged and flag image as **pending Breeze**
in the review summary.

## Stock images (fallback only)

Use `adobe-stock` or `hubspot-campaign-images` **only** when Breeze generation
is blocked or rejected. Default path is always Breeze AI per user requirement.

## Guardrail

Breeze generation does not publish content. Combined with draft-only staging,
no asset goes live without explicit user approval.
