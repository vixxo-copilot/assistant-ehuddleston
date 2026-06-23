# HubSpot content scripts

## Batch staging (Cursor SDK)

Run multi-channel staging from a JSON brief:

```bash
npm install @cursor/sdk
export CURSOR_API_KEY=cursor_...
node scripts/hubspot-content-batch.mjs scripts/briefs/example-bundle.json
```

Requires `HUBSPOT_ACCESS_TOKEN` in `.env` and `config.yaml` with HubSpot IDs.

See `.agents/skills/hubspot-content/SKILL.md` for the chat-driven workflow.
