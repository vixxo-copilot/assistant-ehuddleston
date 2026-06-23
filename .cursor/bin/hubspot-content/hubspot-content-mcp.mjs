#!/usr/bin/env node
/**
 * Local MCP server: HubSpot content staging (blogs, emails, social copy files).
 * Draft-only — no publish, send, or schedule tools.
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
const PYTHON_SCRIPT = path.join(__dirname, "hubspot_content.py");
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
  if (process.env.HUBSPOT_CONTENT_PYTHON) return process.env.HUBSPOT_CONTENT_PYTHON;
  if (process.platform === "win32") return "py -3";
  return "python3";
}

loadEnvFile();
process.env.HUBSPOT_CONTENT_PYTHON =
  process.env.HUBSPOT_CONTENT_PYTHON || resolvePythonCmd();

function runPython(args) {
  const pyCmd = process.env.HUBSPOT_CONTENT_PYTHON || "python3";
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
  { name: "hubspot-content", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "hubspot_content_get_config",
      description:
        "Read HubSpot content config (portalId, contentGroupId, blogAuthorId, email folder). " +
        "Fails with setup instructions if required IDs are missing.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hubspot_content_create_blog_draft",
      description:
        "Create a DRAFT blog post via CMS Blog Posts API. Never publishes.",
      inputSchema: {
        type: "object",
        properties: {
          title: { type: "string" },
          metaDescription: { type: "string" },
          body: { type: "string", description: "HTML post body" },
          slug: { type: "string" },
          featuredImage: { type: "string", description: "HubSpot CDN URL" },
          contentGroupId: { type: "string" },
          blogAuthorId: { type: "string" },
        },
        required: ["title", "metaDescription", "body"],
      },
    },
    {
      name: "hubspot_content_update_blog_draft",
      description: "Update an existing blog post draft. Keeps state DRAFT.",
      inputSchema: {
        type: "object",
        properties: {
          postId: { type: "string" },
          title: { type: "string" },
          metaDescription: { type: "string" },
          body: { type: "string" },
          featuredImage: { type: "string" },
        },
        required: ["postId"],
      },
    },
    {
      name: "hubspot_content_create_email_draft",
      description:
        "Create a DRAFT marketing email via Marketing Emails API. Never sends.",
      inputSchema: {
        type: "object",
        properties: {
          name: { type: "string", description: "Internal email name" },
          subject: { type: "string" },
          preheader: { type: "string" },
          htmlBody: { type: "string" },
          folderId: { type: "integer" },
          activeDomain: { type: "string" },
        },
        required: ["name", "subject"],
      },
    },
    {
      name: "hubspot_content_update_email_draft",
      description: "Update draft version of a marketing email. Never sends.",
      inputSchema: {
        type: "object",
        properties: {
          emailId: { type: "string" },
          name: { type: "string" },
          subject: { type: "string" },
          preheader: { type: "string" },
          htmlBody: { type: "string" },
        },
        required: ["emailId"],
      },
    },
    {
      name: "hubspot_content_stage_social_pack",
      description:
        "Write social staging pack (JSON + markdown) to _content/staging/. " +
        "HubSpot Social has no API — user schedules manually in UI.",
      inputSchema: {
        type: "object",
        properties: {
          campaign: { type: "string" },
          targetDate: { type: "string", description: "ISO date" },
          posts: {
            type: "array",
            items: {
              type: "object",
              properties: {
                platform: { type: "string" },
                copy: { type: "string" },
                hashtags: { type: "array", items: { type: "string" } },
                link: { type: "string" },
                imagePrompt: { type: "string" },
              },
            },
          },
          relatedBlogId: { type: "string" },
          relatedEmailId: { type: "string" },
        },
        required: ["campaign", "posts"],
      },
    },
    {
      name: "hubspot_content_write_review_doc",
      description:
        "Write the consolidated REVIEW.md (blog, email, social txt, social image URLs) for a staged campaign.",
      inputSchema: {
        type: "object",
        properties: {
          campaign: { type: "string", description: "Campaign slug, e.g. hvac-pm-fm-2026" },
          title: { type: "string", description: "Human-readable campaign title for REVIEW.md header" },
          blogId: { type: "string" },
          emailId: { type: "string" },
          socialImageUrl: { type: "string", description: "HubSpot CDN URL for 300x300 social image" },
          socialCopyPath: { type: "string", description: "Absolute or repo-relative path to .txt copy" },
        },
        required: ["campaign", "blogId", "emailId", "socialImageUrl"],
      },
    },
    {
      name: "hubspot_content_get_staged_summary",
      description: "Return review summary with editor URLs and checklist for staged assets.",
      inputSchema: {
        type: "object",
        properties: {
          blogId: { type: "string" },
          emailId: { type: "string" },
          stagingPath: { type: "string" },
          socialCopyPath: { type: "string", description: "Path to social .txt copy file" },
        },
      },
    },
    {
      name: "hubspot_content_breeze_image_prompt",
      description:
        "Build a HubSpot Breeze AI (Generate with AI) image prompt for one content piece. " +
        "Required: one Breeze image per blog, email, and social post. No public Breeze API — " +
        "user completes generation in HubSpot UI.",
      inputSchema: {
        type: "object",
        properties: {
          topic: { type: "string", description: "Campaign topic or visual brief" },
          channel: {
            type: "string",
            enum: ["blog_featured", "email_header", "social"],
          },
          audience: { type: "string", description: "Target audience for imagery context" },
        },
        required: ["topic", "channel"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  if (name === "hubspot_content_get_config") {
    const result = await runPython(["get-config"]);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_create_blog_draft") {
    const pyArgs = [
      "create-blog-draft",
      "--title",
      args.title,
      "--meta-description",
      args.metaDescription,
      "--body",
      args.body,
    ];
    if (args.slug) pyArgs.push("--slug", args.slug);
    if (args.featuredImage) pyArgs.push("--featured-image", args.featuredImage);
    if (args.contentGroupId) pyArgs.push("--content-group-id", args.contentGroupId);
    if (args.blogAuthorId) pyArgs.push("--blog-author-id", args.blogAuthorId);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_update_blog_draft") {
    const pyArgs = ["update-blog-draft", "--post-id", args.postId];
    if (args.title) pyArgs.push("--title", args.title);
    if (args.metaDescription) pyArgs.push("--meta-description", args.metaDescription);
    if (args.body) pyArgs.push("--body", args.body);
    if (args.featuredImage) pyArgs.push("--featured-image", args.featuredImage);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_create_email_draft") {
    const pyArgs = ["create-email-draft", "--name", args.name, "--subject", args.subject];
    if (args.preheader) pyArgs.push("--preheader", args.preheader);
    if (args.htmlBody) pyArgs.push("--html-body", args.htmlBody);
    if (args.folderId) pyArgs.push("--folder-id", String(args.folderId));
    if (args.activeDomain) pyArgs.push("--active-domain", args.activeDomain);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_update_email_draft") {
    const pyArgs = ["update-email-draft", "--email-id", args.emailId];
    if (args.name) pyArgs.push("--name", args.name);
    if (args.subject) pyArgs.push("--subject", args.subject);
    if (args.preheader !== undefined) pyArgs.push("--preheader", args.preheader);
    if (args.htmlBody) pyArgs.push("--html-body", args.htmlBody);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_stage_social_pack") {
    const pyArgs = [
      "stage-social-pack",
      "--campaign",
      args.campaign,
      "--posts-json",
      JSON.stringify(args.posts || []),
    ];
    if (args.targetDate) pyArgs.push("--target-date", args.targetDate);
    if (args.relatedBlogId) pyArgs.push("--related-blog-id", args.relatedBlogId);
    if (args.relatedEmailId) pyArgs.push("--related-email-id", args.relatedEmailId);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_write_review_doc") {
    const pyArgs = [
      "write-review-doc",
      "--campaign",
      args.campaign,
      "--blog-id",
      args.blogId,
      "--email-id",
      args.emailId,
      "--social-image-url",
      args.socialImageUrl,
    ];
    if (args.title) pyArgs.push("--title", args.title);
    if (args.socialCopyPath) pyArgs.push("--social-copy-path", args.socialCopyPath);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_get_staged_summary") {
    const pyArgs = ["get-staged-summary"];
    if (args.blogId) pyArgs.push("--blog-id", args.blogId);
    if (args.emailId) pyArgs.push("--email-id", args.emailId);
    if (args.stagingPath) pyArgs.push("--staging-path", args.stagingPath);
    if (args.socialCopyPath) pyArgs.push("--social-copy-path", args.socialCopyPath);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_breeze_image_prompt") {
    const pyArgs = ["breeze-prompt", "--topic", args.topic, "--channel", args.channel];
    if (args.audience) pyArgs.push("--audience", args.audience);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
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
