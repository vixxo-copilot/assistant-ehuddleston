#!/usr/bin/env node
/**
 * Local MCP server: HubSpot CMS site/landing page migration and creation.
 * Draft-first — publish requires explicit user approval.
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.join(__dirname, "..", "..", "..");
const PYTHON_SCRIPT = path.join(__dirname, "hubspot_pages.py");
const ENV_FILE = path.join(ROOT_DIR, ".env");

function loadEnvFile() {
  if (!fs.existsSync(ENV_FILE)) return;
  for (const line of fs.readFileSync(ENV_FILE, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
    const eq = trimmed.indexOf("=");
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (key && process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}

function resolvePythonCmd() {
  if (process.env.HUBSPOT_PAGES_PYTHON) return process.env.HUBSPOT_PAGES_PYTHON;
  if (process.platform === "win32") return "py -3";
  return "python3";
}

loadEnvFile();
process.env.HUBSPOT_PAGES_PYTHON =
  process.env.HUBSPOT_PAGES_PYTHON || resolvePythonCmd();

function runPython(args) {
  const pyCmd = process.env.HUBSPOT_PAGES_PYTHON || "python3";
  const pyParts = pyCmd.split(" ");
  return new Promise((resolve, reject) => {
    const proc = spawn(pyParts[0], [...pyParts.slice(1), PYTHON_SCRIPT, ...args], {
      cwd: ROOT_DIR,
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
  { name: "hubspot-pages", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

const DRAFT_FIRST =
  "DRAFT-FIRST: create pages as DRAFT. Never publish unless the user explicitly requests publish.";

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "hubspot_pages_get_config",
      description:
        "Read portal config (portalId, targetTemplatePath, defaultDomain) and OAuth readiness. " +
        "Call first before migration work.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hubspot_pages_auth_status",
      description: "Check HubSpot OAuth connection and which user edits will attribute to.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hubspot_pages_login",
      description: "Connect HubSpot OAuth (opens browser). Reuses hubspot-content token store.",
      inputSchema: {
        type: "object",
        properties: { noBrowser: { type: "boolean" } },
      },
    },
    {
      name: "hubspot_pages_logout",
      description: "Remove stored HubSpot OAuth token.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hubspot_pages_list_templates",
      description: "List CMS templates from Design Manager (filter by path substring).",
      inputSchema: {
        type: "object",
        properties: {
          search: { type: "string", description: "Filter template path contains" },
          limit: { type: "number", default: 100 },
        },
      },
    },
    {
      name: "hubspot_pages_list_pages",
      description: "List site or landing pages with optional filters.",
      inputSchema: {
        type: "object",
        properties: {
          pageType: { type: "string", enum: ["site-page", "landing-page"], default: "site-page" },
          state: { type: "string", description: "e.g. DRAFT, PUBLISHED_OR_SCHEDULED" },
          nameContains: { type: "string" },
          slug: { type: "string" },
          limit: { type: "number", default: 50 },
        },
      },
    },
    {
      name: "hubspot_pages_get_page",
      description: "Fetch a page by ID and write a JSON backup under _pages/staging/.",
      inputSchema: {
        type: "object",
        required: ["pageId"],
        properties: {
          pageId: { type: "string" },
          pageType: { type: "string", enum: ["site-page", "landing-page"], default: "site-page" },
        },
      },
    },
    {
      name: "hubspot_pages_migrate_template",
      description:
        "Transfer an existing page to a new template by updating templatePath. " +
        "Backs up page JSON first. User must rebuild modules in HubSpot editor after migration. " +
        DRAFT_FIRST,
      inputSchema: {
        type: "object",
        properties: {
          pageId: { type: "string" },
          slug: { type: "string", description: "Lookup page by slug when pageId omitted" },
          templatePath: {
            type: "string",
            description: "Design Manager path without leading slash; defaults to config targetTemplatePath",
          },
          pageType: { type: "string", enum: ["site-page", "landing-page"], default: "site-page" },
        },
      },
    },
    {
      name: "hubspot_pages_create_page",
      description: "Create a new DRAFT site or landing page with the target template. " + DRAFT_FIRST,
      inputSchema: {
        type: "object",
        required: ["name"],
        properties: {
          name: { type: "string" },
          slug: { type: "string" },
          htmlTitle: { type: "string" },
          metaDescription: { type: "string" },
          domain: { type: "string" },
          templatePath: { type: "string" },
          pageType: { type: "string", enum: ["site-page", "landing-page"], default: "site-page" },
          layoutJson: { type: "string", description: "Optional layoutSections JSON string" },
        },
      },
    },
    {
      name: "hubspot_pages_update_page",
      description: "Update page metadata (name, slug, SEO, template). Uses draft endpoint for live pages.",
      inputSchema: {
        type: "object",
        required: ["pageId"],
        properties: {
          pageId: { type: "string" },
          name: { type: "string" },
          slug: { type: "string" },
          htmlTitle: { type: "string" },
          metaDescription: { type: "string" },
          templatePath: { type: "string" },
          pageType: { type: "string", enum: ["site-page", "landing-page"], default: "site-page" },
        },
      },
    },
    {
      name: "hubspot_pages_clone_page",
      description:
        "Clone a live site/landing page to draft and set internal name with — Edited YYYY-MM-DD suffix. " +
        DRAFT_FIRST,
      inputSchema: {
        type: "object",
        properties: {
          pageId: { type: "string", description: "Live source page ID" },
          slug: { type: "string", description: "Lookup live page by slug when pageId omitted" },
          pageType: { type: "string", enum: ["site-page", "landing-page"], default: "site-page" },
        },
      },
    },
    {
      name: "hubspot_pages_run_inventory",
      description:
        "Process _pages/inventory/pages.inventory.yaml — batch migrate existing pages and create new drafts. " +
        "Use dryRun:true first. " + DRAFT_FIRST,
      inputSchema: {
        type: "object",
        properties: {
          inventoryFile: { type: "string", description: "Path to inventory YAML" },
          dryRun: { type: "boolean", default: false },
        },
      },
    },
    {
      name: "hubspot_pages_get_page_brief",
      description:
        "Step 1 of topic → AEO site page workflow. Returns composition schema, brand voice, " +
        "AEO/SEO rules, template/slug inference, and module blueprint paths. " + DRAFT_FIRST,
      inputSchema: {
        type: "object",
        properties: {
          topic: {
            type: "string",
            description: "Required. Free-form FM topic (e.g. 'multi-site HVAC preventive maintenance').",
          },
        },
        required: ["topic"],
      },
    },
    {
      name: "hubspot_pages_stage_page",
      description:
        "Step 2 of topic → AEO site page workflow. After Cursor composes the page package, " +
        "resolves hero + section images, maps copy into CLEAN-6-1 modules, and creates a DRAFT site page. " +
        DRAFT_FIRST,
      inputSchema: {
        type: "object",
        properties: {
          package: {
            type: "object",
            description:
              "Composed page package (see hubspot_pages_get_page_brief requiredSchema or hubspot-page-content skill).",
          },
          dryRun: {
            type: "boolean",
            default: false,
            description: "When true, validate and preview staging plan without creating the page.",
          },
        },
        required: ["package"],
      },
    },
    {
      name: "hubspot_pages_publish_page",
      description:
        "Publish a page. ONLY call when the user explicitly says publish/approved/go live.",
      inputSchema: {
        type: "object",
        required: ["pageId", "confirm"],
        properties: {
          pageId: { type: "string" },
          pageType: { type: "string", enum: ["site-page", "landing-page"], default: "site-page" },
          confirm: {
            type: "boolean",
            description: "Must be true — confirms explicit user approval to publish",
          },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;
  try {
    let result;
    switch (name) {
      case "hubspot_pages_get_config":
        result = await runPython(["get-config"]);
        break;
      case "hubspot_pages_auth_status":
        result = await runPython(["auth-status"]);
        break;
      case "hubspot_pages_login":
        result = await runPython(args.noBrowser ? ["login", "--no-browser"] : ["login"]);
        break;
      case "hubspot_pages_logout":
        result = await runPython(["logout"]);
        break;
      case "hubspot_pages_list_templates":
        result = await runPython([
          "list-templates",
          ...(args.search ? ["--search", args.search] : []),
          "--limit",
          String(args.limit ?? 100),
        ]);
        break;
      case "hubspot_pages_list_pages":
        result = await runPython([
          "list-pages",
          "--page-type",
          args.pageType || "site-page",
          ...(args.state ? ["--state", args.state] : []),
          ...(args.nameContains ? ["--name-contains", args.nameContains] : []),
          ...(args.slug ? ["--slug", args.slug] : []),
          "--limit",
          String(args.limit ?? 50),
        ]);
        break;
      case "hubspot_pages_get_page":
        result = await runPython([
          "get-page",
          "--page-id",
          args.pageId,
          "--page-type",
          args.pageType || "site-page",
        ]);
        break;
      case "hubspot_pages_migrate_template":
        result = await runPython([
          "migrate-template",
          ...(args.pageId ? ["--page-id", args.pageId] : []),
          ...(args.slug ? ["--slug", args.slug] : []),
          ...(args.templatePath ? ["--template-path", args.templatePath] : []),
          "--page-type",
          args.pageType || "site-page",
        ]);
        break;
      case "hubspot_pages_create_page":
        result = await runPython([
          "create-page",
          "--name",
          args.name,
          ...(args.slug ? ["--slug", args.slug] : []),
          ...(args.htmlTitle ? ["--html-title", args.htmlTitle] : []),
          ...(args.metaDescription ? ["--meta-description", args.metaDescription] : []),
          ...(args.domain ? ["--domain", args.domain] : []),
          ...(args.templatePath ? ["--template-path", args.templatePath] : []),
          ...(args.layoutJson ? ["--layout-json", args.layoutJson] : []),
          "--page-type",
          args.pageType || "site-page",
        ]);
        break;
      case "hubspot_pages_update_page":
        result = await runPython([
          "update-page",
          "--page-id",
          args.pageId,
          ...(args.name ? ["--name", args.name] : []),
          ...(args.slug ? ["--slug", args.slug] : []),
          ...(args.htmlTitle ? ["--html-title", args.htmlTitle] : []),
          ...(args.metaDescription ? ["--meta-description", args.metaDescription] : []),
          ...(args.templatePath ? ["--template-path", args.templatePath] : []),
          "--page-type",
          args.pageType || "site-page",
        ]);
        break;
      case "hubspot_pages_clone_page":
        result = await runPython([
          "clone-page",
          ...(args.pageId ? ["--page-id", args.pageId] : []),
          ...(args.slug ? ["--slug", args.slug] : []),
          "--page-type",
          args.pageType || "site-page",
        ]);
        break;
      case "hubspot_pages_run_inventory":
        result = await runPython([
          "run-inventory",
          ...(args.inventoryFile ? ["--inventory-file", args.inventoryFile] : []),
          ...(args.dryRun ? ["--dry-run"] : []),
        ]);
        break;
      case "hubspot_pages_get_page_brief":
        result = await runPython(["get-page-brief", "--topic", args.topic]);
        break;
      case "hubspot_pages_stage_page": {
        const packageJson = JSON.stringify(args.package ?? {});
        const pyArgs = ["stage-page", "--package-json", packageJson];
        if (args.dryRun) pyArgs.push("--dry-run");
        result = await runPython(pyArgs);
        break;
      }
      case "hubspot_pages_publish_page":
        if (!args.confirm) {
          throw new Error("Publishing requires confirm:true and explicit user approval.");
        }
        result = await runPython([
          "publish-page",
          "--page-id",
          args.pageId,
          "--page-type",
          args.pageType || "site-page",
          "--confirm",
        ]);
        break;
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
  } catch (err) {
    return {
      content: [{ type: "text", text: String(err?.message || err) }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
