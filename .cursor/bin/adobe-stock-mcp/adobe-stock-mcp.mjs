#!/usr/bin/env node
/** Local MCP: Adobe Stock search + download for HubSpot campaign images. */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ADOBE_PY = path.join(__dirname, "adobe_stock_client.py");
const HUBSPOT_PY = path.join(__dirname, "..", "hubspot-campaign-images", "hubspot_campaign_images.py");

function runPython(script, args, parseJson = true) {
  const pyCmd = process.env.HUBSPOT_CAMPAIGN_IMAGES_PYTHON || "python3";
  const pyParts = pyCmd.split(" ");
  return new Promise((resolve, reject) => {
    const proc = spawn(pyParts[0], [...pyParts.slice(1), script, ...args], {
      cwd: path.join(__dirname, "..", "..", ".."),
      env: process.env,
    });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => (stdout += d));
    proc.stderr.on("data", (d) => (stderr += d));
    proc.on("close", (code) => {
      if (code !== 0) reject(new Error(stderr || stdout || `exit ${code}`));
      else if (!parseJson) resolve(stdout);
      else {
        try {
          resolve(JSON.parse(stdout));
        } catch {
          resolve({ raw: stdout.trim() });
        }
      }
    });
  });
}

const PLACEMENT_QUERIES = {
  hero: "commercial retail rooftop HVAC units aerial multi-site portfolio",
  section_roi: "facilities executive boardroom retail portfolio strategy meeting",
  section_scale: "retail store chain exterior nationwide locations commercial",
  section_technician: "commercial HVAC technician rooftop unit preventative maintenance",
  email_header: "commercial building rooftop HVAC equipment wide banner",
};

const server = new Server(
  { name: "adobe-stock", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "adobe_stock_search",
      description:
        "Search Adobe Stock photos by query. Requires ADOBE_STOCK_API_KEY. Returns asset IDs and metadata.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          limit: { type: "integer", default: 5 },
          orientation: { type: "string", enum: ["horizontal", "vertical", "square"], default: "horizontal" },
        },
        required: ["query"],
      },
    },
    {
      name: "adobe_stock_download",
      description:
        "Search Adobe Stock and download image bytes (licensed if ADOBE_STOCK_ACCESS_TOKEN set, else comp/thumbnail). " +
        "Optional --save path via outputPath. Returns metadata + base64 content.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          placement: { type: "string" },
          outputPath: { type: "string", description: "Optional local save path" },
        },
        required: ["query"],
      },
    },
    {
      name: "adobe_stock_import_to_hubspot",
      description:
        "Full pipeline: Adobe Stock search+download → HubSpot File Manager upload (/campaign-images/hvac-pm-2026). " +
        "Requires ADOBE_STOCK_API_KEY and HUBSPOT_ACCESS_TOKEN.",
      inputSchema: {
        type: "object",
        properties: {
          placement: {
            type: "string",
            enum: ["hero", "section_roi", "section_scale", "section_technician", "email_header"],
          },
          query: { type: "string", description: "Override default placement search query" },
          alt: { type: "string" },
          folder: { type: "string", default: "/campaign-images/hvac-pm-2026" },
        },
        required: ["placement"],
      },
    },
    {
      name: "adobe_stock_import_campaign_set",
      description:
        "Import all 5 HVAC PM campaign placements from Adobe Stock into HubSpot File Manager.",
      inputSchema: { type: "object", properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "adobe_stock_search") {
    // Lightweight search via python one-liner module
    const result = await runPython(ADOBE_PY, [args.query, "--placement", "search", "--json-only"], false);
    // adobe_stock_client CLI doesn't have search-only - use import script
    const pySearch = `
import json, os, sys
sys.path.insert(0, ${JSON.stringify(__dirname)})
from adobe_stock_client import load_dotenv, search_files
load_dotenv()
files = search_files(${JSON.stringify(args.query)}, limit=${args.limit || 5}, orientation=${JSON.stringify(args.orientation || "horizontal")})
out = [{"id": f.get("id"), "title": f.get("title"), "creator_name": f.get("creator_name"), "thumbnail_url": f.get("thumbnail_url") or f.get("thumbnail_500_url")} for f in files]
print(json.dumps(out, indent=2))
`;
    const proc = spawn(
      (process.env.HUBSPOT_CAMPAIGN_IMAGES_PYTHON || "python3").split(" ")[0],
      ["-c", pySearch],
      { cwd: path.join(__dirname, "..", "..", ".."), env: process.env }
    );
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => (stdout += d));
    proc.stderr.on("data", (d) => (stderr += d));
    await new Promise((res, rej) =>
      proc.on("close", (c) => (c === 0 ? res() : rej(new Error(stderr || stdout))))
    );
    return { content: [{ type: "text", text: stdout }] };
  }

  if (name === "adobe_stock_download") {
    const dlArgs = [args.query, "--placement", args.placement || "hero", "--json-only"];
    if (args.outputPath) dlArgs.push("--save", args.outputPath);
    const result = await runPython(ADOBE_PY, dlArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "adobe_stock_import_to_hubspot") {
    const query = args.query || PLACEMENT_QUERIES[args.placement];
    const result = await runPython(HUBSPOT_PY, [
      "adobe-import",
      "--placement",
      args.placement,
      "--query",
      query,
      ...(args.alt ? ["--alt", args.alt] : []),
      ...(args.folder ? ["--folder", args.folder] : []),
    ]);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "adobe_stock_import_campaign_set") {
    const results = [];
    for (const [placement, query] of Object.entries(PLACEMENT_QUERIES)) {
      try {
        const r = await runPython(HUBSPOT_PY, [
          "adobe-import",
          "--placement",
          placement,
          "--query",
          query,
        ]);
        results.push(r);
      } catch (e) {
        results.push({ placement, error: String(e.message || e) });
      }
    }
    return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
  }

  throw new Error(`Unknown tool: ${name}`);
});

async function main() {
  await server.connect(new StdioServerTransport());
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
