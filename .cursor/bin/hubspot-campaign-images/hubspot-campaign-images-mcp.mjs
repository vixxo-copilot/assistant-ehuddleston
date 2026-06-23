#!/usr/bin/env node
/**
 * Local MCP server: HubSpot campaign image auto-insert companion.
 * Wraps hubspot_campaign_images.py and returns insert specs for manage_landing_page.
 */
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
const PYTHON_SCRIPT = path.join(__dirname, "hubspot_campaign_images.py");

function runPython(args) {
  const pyCmd = process.env.HUBSPOT_CAMPAIGN_IMAGES_PYTHON || "python3";
  const pyParts = pyCmd.split(" ");
  return new Promise((resolve, reject) => {
    const proc = spawn(pyParts[0], [...pyParts.slice(1), PYTHON_SCRIPT, ...args], {
      cwd: path.join(__dirname, "..", "..", ".."),
      env: process.env,
    });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => (stdout += d));
    proc.stderr.on("data", (d) => (stderr += d));
    proc.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr || stdout || `exit ${code}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch {
        resolve({ raw: stdout.trim() });
      }
    });
  });
}

const server = new Server(
  { name: "hubspot-campaign-images", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "hubspot_campaign_resolve_image",
      description:
        "Resolve a campaign stock image for a placement (hero, section_roi, etc.). " +
        "Uses Shutterstock preview if SHUTTERSTOCK_API_TOKEN is set, else HubSpot-native placeholder. " +
        "Includes Breeze AI manual prompt for UI replacement (no Breeze API exists).",
      inputSchema: {
        type: "object",
        properties: {
          prompt: { type: "string", description: "Image subject / creative brief" },
          placement: {
            type: "string",
            enum: ["hero", "section_roi", "section_scale", "section_technician", "email_header"],
          },
          prefer: { type: "string", enum: ["auto", "shutterstock", "placeholder"], default: "auto" },
        },
        required: ["prompt", "placement"],
      },
    },
    {
      name: "hubspot_campaign_insert_image",
      description:
        "Full pipeline: resolve image, optionally upload to HubSpot File Manager (HUBSPOT_ACCESS_TOKEN), " +
        "return manage_landing_page SET_MODULE_FIELDS arguments for @hubspot/linked_image.",
      inputSchema: {
        type: "object",
        properties: {
          prompt: { type: "string" },
          placement: { type: "string" },
          alt: { type: "string", description: "Alt text; defaults from resolution" },
          contentId: { type: "integer", description: "Landing page content ID" },
          moduleId: { type: "string", description: "Target module ID from manage_landing_page MODULES" },
          upload: { type: "boolean", default: true, description: "Upload to HubSpot File Manager when token set" },
          folder: { type: "string", default: "/campaign-images/hvac-pm-2026" },
        },
        required: ["prompt", "placement"],
      },
    },
    {
      name: "hubspot_campaign_breeze_prompts",
      description:
        "Return HubSpot Breeze AI image prompts for all standard HVAC PM campaign placements (VP+ retail FM).",
      inputSchema: { type: "object", properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "hubspot_campaign_resolve_image") {
    const result = await runPython([
      "resolve",
      "--prompt",
      args.prompt,
      "--placement",
      args.placement,
      "--prefer",
      args.prefer || "auto",
    ]);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_campaign_insert_image") {
    const pyArgs = [
      "pipeline",
      "--prompt",
      args.prompt,
      "--placement",
      args.placement,
      "--prefer",
      "auto",
    ];
    if (args.upload !== false) pyArgs.push("--upload");
    if (args.folder) pyArgs.push("--folder", args.folder);
    if (args.alt) pyArgs.push("--alt", args.alt);
    if (args.contentId) pyArgs.push("--content-id", String(args.contentId));
    if (args.moduleId) pyArgs.push("--module-id", args.moduleId);

    const result = await runPython(pyArgs);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              ...result,
              next_step:
                result.manage_landing_page && args.contentId
                  ? "Call hubspot_call_upstream_tool with name=manage_landing_page and arguments from manage_landing_page field"
                  : "Provide contentId and moduleId to get SET_MODULE_FIELDS payload",
            },
            null,
            2
          ),
        },
      ],
    };
  }

  if (name === "hubspot_campaign_breeze_prompts") {
    const prompts = {
      campaign: "HVAC Preventative Maintenance 2026 — Retail Portfolio Leaders",
      audience: "VP+ nationwide retail facilities management",
      note: "HubSpot UI: Content editor or File Manager > Stock Images > Generate with AI (Breeze). No public API.",
      placements: {
        hero: {
          prompt:
            "Wide aerial view of multiple commercial retail buildings with rooftop HVAC units, " +
            "professional corporate photography, summer daylight, no residential, executive portfolio scale",
          alt: "Nationwide retail portfolio rooftops with commercial HVAC units",
        },
        section_roi: {
          prompt:
            "Senior facilities executive reviewing portfolio dashboard in modern boardroom, " +
            "retail chain context, professional business photography, strategic planning",
          alt: "Facilities executive reviewing portfolio performance metrics",
        },
        section_scale: {
          prompt:
            "Row of identical retail store exteriors showing multi-site chain operations, " +
            "commercial architecture, professional stock photo, nationwide brand consistency",
          alt: "Multi-site retail chain locations representing national portfolio scale",
        },
        section_technician: {
          prompt:
            "Licensed commercial HVAC technician inspecting rooftop package unit on retail building, " +
            "professional safety gear, preventative maintenance context, not residential",
          alt: "Commercial HVAC technician performing preventative maintenance on retail RTU",
        },
        email_header: {
          prompt:
            "Commercial retail building rooftop HVAC equipment at golden hour, " +
            "professional facilities management context, wide banner composition",
          alt: "Commercial retail HVAC rooftop equipment — seasonal readiness",
        },
      },
    };
    return { content: [{ type: "text", text: JSON.stringify(prompts, null, 2) }] };
  }

  throw new Error(`Unknown tool: ${name}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
