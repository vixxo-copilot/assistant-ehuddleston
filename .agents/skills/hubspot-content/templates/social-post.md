# Social Post Drafts

## Campaign context
- **Campaign:**
- **Target date:**
- **Related blog URL:** (after publish)
- **Related email:** (internal name)

---

## LinkedIn
**Copy:**
<!-- ≤3000 chars recommended -->

**Hashtags:**

**Link:**

**Image (required — HubSpot Breeze AI):**

Call `hubspot_content_breeze_image_prompt` with `channel: social`.

- **Breeze prompt:**
- **Generate in HubSpot:** Marketing → Social → Add image → Generate with AI

---

## Facebook
**Copy:**

**Link:**

---

## X (Twitter)
**Copy:** <!-- ≤280 chars -->

**Link:**

---

## Staging notes
Social posts have no HubSpot API. After composing:
1. Call `hubspot_content_stage_social_pack` to write `{platform}-post.txt` to `_content/social-ready/{campaign}/`
2. User schedules manually in HubSpot Marketing > Social
