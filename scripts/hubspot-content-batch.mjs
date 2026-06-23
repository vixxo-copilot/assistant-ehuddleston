#!/usr/bin/env node
/**
 * Batch HubSpot content staging via Cursor SDK.
 *
 * Usage:
 *   npm install @cursor/sdk   # once, in repo root or globally
 *   export CURSOR_API_KEY=cursor_...
 *   node scripts/hubspot-content-batch.mjs briefs/example-bundle.json
 *
 * Runs a single Agent.prompt that executes the hubspot-content skill against
 * a JSON brief. Draft-only — no publish/send.
 */
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..");

async function main() {
  const briefPath = process.argv[2];
  if (!briefPath) {
    console.error("Usage: node scripts/hubspot-content-batch.mjs <brief.json>");
    process.exit(1);
  }

  const apiKey = process.env.CURSOR_API_KEY;
  if (!apiKey) {
    console.error("CURSOR_API_KEY is required");
    process.exit(1);
  }

  let brief;
  try {
    brief = JSON.parse(readFileSync(resolve(briefPath), "utf-8"));
  } catch (err) {
    console.error(`Failed to read brief: ${err.message}`);
    process.exit(1);
  }

  let Agent;
  try {
    ({ Agent } = await import("@cursor/sdk"));
  } catch {
    console.error("Install @cursor/sdk: npm install @cursor/sdk");
    process.exit(1);
  }

  const prompt = [
    "Use the hubspot-content skill to plan, compose, and stage all channels in this brief.",
    "Draft-only — never publish, send, or schedule.",
    "",
    "Brief JSON:",
    JSON.stringify(brief, null, 2),
    "",
    "Return: staged asset IDs, HubSpot editor URLs, social copy paths, review checklist.",
  ].join("\n");

  const mcpServers = {
    "hubspot-content": {
      command: "bash",
      args: [".cursor/bin/hubspot-content/run-hubspot-content-mcp.sh"],
    },
    hubspot: {
      url: "https://vixxonow.com/mcp/hubspot",
    },
    "hubspot-campaign-images": {
      command: "bash",
      args: [".cursor/bin/hubspot-campaign-images/run-hubspot-campaign-images-mcp.sh"],
    },
  };

  try {
    const result = await Agent.prompt(prompt, {
      apiKey,
      model: { id: "composer-2.5" },
      local: {
        cwd: REPO_ROOT,
        mcpServers,
      },
    });

    console.log("Status:", result.status);
    console.log("Result:\n", result.result);

    if (result.status === "error") {
      process.exit(2);
    }
  } catch (err) {
    console.error("Startup failed:", err.message);
    process.exit(1);
  }
}

main();
