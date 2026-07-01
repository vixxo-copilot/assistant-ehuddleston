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
  { name: "hubspot-content", version: "2.7.0" },
  { capabilities: { tools: {} } }
);

const DRAFT_ONLY =
  "DRAFT-ONLY: never publish, send, or schedule HubSpot assets unless the user explicitly requests it.";

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "hubspot_content_get_package_brief",
      description:
        "Step 1 of topic → content package workflow. Returns composition schema, brand rules, " +
        "suggested trade/visualTopic, image-matching rules (Cursor AI -> Adobe Stock -> Wikimedia -> trade fallback), " +
        "draft-only guardrails, and workflow steps. " + DRAFT_ONLY,
      inputSchema: {
        type: "object",
        properties: {
          topic: {
            type: "string",
            description:
              "Required. Any free-form user topic prompt (e.g. 'multi-site LED lighting retrofit', " +
              "'seasonal FM readiness before peak summer', 'emergency plumbing frozen pipes'). " +
              "Drives copy, trade inference, visualTopic, and image search.",
          },
        },
      },
    },
    {
      name: "hubspot_content_stage_content_package",
      description:
        "Step 2 of topic → content package workflow. After Cursor composes copy, stages the full " +
        "HubSpot draft bundle in one call: topic-matched 150 DPI blog hero (2500×1406), email draft " +
        "(150 DPI banner + body), social .txt, 150 DPI social image (625×625), REVIEW.md, and " +
        "campaign-links.json. trade/visualTopic auto-inferred from topic when omitted. " +
        "For best topic-matched photos: generate a hero in Cursor from visualTopic, save to " +
        "_content/staging/{campaign}/ai-hero-bg.png, then call hubspot_content_refresh_campaign_images " +
        "with bgFile. " + DRAFT_ONLY,
      inputSchema: {
        type: "object",
        properties: {
          package: {
            type: "object",
            description: "Composed content package (see hubspot_content_get_package_brief requiredSchema)",
            properties: {
              topic: {
                type: "string",
                description:
                  "Required. User's topic in their own words — any FM subject (HVAC, plumbing, electrical, seasonal, etc.)",
              },
              campaign: {
                type: "string",
                description: "Optional slug; auto-generated from topic if omitted",
              },
              targetDate: { type: "string" },
              trade: {
                type: "string",
                enum: ["hvac", "plumbing", "electrical"],
                description: "Optional — auto-inferred from topic when omitted",
              },
              reviewTitle: { type: "string" },
              visualTopic: {
                type: "string",
                description:
                  "Optional editorial photo brief for images. Auto-generated from topic when omitted. " +
                  "Override for sharper art direction; used for Cursor AI hero, stock search, and Breeze prompts.",
              },
              breezeAudience: { type: "string" },
              blog: { type: "object" },
              email: { type: "object" },
              social: { type: "object" },
            },
            required: ["topic", "blog", "email", "social"],
          },
          packageFile: {
            type: "string",
            description: "Repo-relative path to package.json (alternative to inline package)",
          },
        },
      },
    },
    {
      name: "hubspot_content_refresh_campaign_images",
      description:
        "Re-render and upload all campaign images at 150 DPI for existing staged blog/email drafts: " +
        "blog featured hero (2500×1406), email banner (1250×352), social card (625×625). " +
        "Reads package.json from _content/staging/{campaign}/; blog/email IDs from staging-manifest.json " +
        "or explicit args. Updates REVIEW.md and image-resolution.json. " +
        "Without bgFile: resolves background via Adobe Stock (if ADOBE_STOCK_API_KEY) -> Shutterstock -> " +
        "Pexels -> Wikimedia -> verified Vixxo trade hero. " +
        "With bgFile: uses a local photo (e.g. Cursor AI-generated ai-hero-bg.png) — skips stock search. " +
        DRAFT_ONLY,
      inputSchema: {
        type: "object",
        properties: {
          campaign: {
            type: "string",
            description: "Campaign slug, e.g. refrigeration-pm-in-grocery-retail",
          },
          blogId: {
            type: "string",
            description: "HubSpot blog post ID (optional if staging-manifest.json exists)",
          },
          emailId: {
            type: "string",
            description: "HubSpot marketing email ID (optional if staging-manifest.json exists)",
          },
          bgFile: {
            type: "string",
            description:
              "Repo-relative path to local background photo (e.g. _content/staging/{campaign}/ai-hero-bg.png). " +
              "Use after generating a topic-matched hero in Cursor; sets image source to cursor_ai.",
          },
        },
        required: ["campaign"],
      },
    },
    {
      name: "hubspot_content_get_campaign_links",
      description:
        "Return consolidated link table for a staged campaign: blog/email editor URLs, 150 DPI image " +
        "CDN URLs (blog hero, email banner, social), social copy path, REVIEW.md path, and social UI. " +
        "Reads campaign-links.json or assembles from staging-manifest.json + image-resolution.json.",
      inputSchema: {
        type: "object",
        properties: {
          campaign: {
            type: "string",
            description: "Campaign slug, e.g. emergency-plumbing-frozen-pipes-2026",
          },
        },
        required: ["campaign"],
      },
    },
    {
      name: "hubspot_content_verify_campaign_draft_status",
      description:
        "Read-only safety check: confirm staged blog posts and marketing emails are DRAFT (not published or sent). " +
        "Scans all campaigns in _content/staging/ or a single campaign slug. Returns allDraft, anyLive, and per-asset state. " +
        "Does NOT publish, unpublish, send, or schedule. " + DRAFT_ONLY,
      inputSchema: {
        type: "object",
        properties: {
          campaign: {
            type: "string",
            description: "Optional campaign slug — omit to check all staged campaigns",
          },
        },
      },
    },
    {
      name: "hubspot_content_get_config",
      description:
        "Read HubSpot content config (portalId, contentGroupId, blogAuthorId, email folder). " +
        "Fails with setup instructions if required IDs are missing.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hubspot_content_login",
      description:
        "Connect HubSpot via OAuth so blog/email edits attribute to the signed-in user (not a shared private app token). Opens browser.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hubspot_content_auth_status",
      description: "Check whether HubSpot OAuth is connected and which user account will be attributed.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hubspot_content_logout",
      description: "Remove stored HubSpot OAuth token from this machine.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hubspot_content_create_blog_draft",
      description:
        "Create a DRAFT blog post via CMS Blog Posts API. " + DRAFT_ONLY,
      inputSchema: {
        type: "object",
        properties: {
          title: { type: "string" },
          metaDescription: { type: "string" },
          body: { type: "string", description: "HTML post body (use bodyFile for large HTML)" },
          bodyFile: { type: "string", description: "Repo-relative path to HTML body file" },
          slug: { type: "string" },
          featuredImage: { type: "string", description: "HubSpot CDN URL" },
          contentGroupId: { type: "string" },
          blogAuthorId: { type: "string" },
        },
        required: ["title", "metaDescription"],
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
        "Create a DRAFT marketing email via Marketing Emails API. " + DRAFT_ONLY,
      inputSchema: {
        type: "object",
        properties: {
          name: { type: "string", description: "Internal email name" },
          subject: { type: "string" },
          preheader: { type: "string" },
          htmlBody: { type: "string", description: "Use htmlBodyFile for large HTML" },
          htmlBodyFile: { type: "string", description: "Repo-relative path to HTML body file" },
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
        "Write the consolidated REVIEW.md (blog, email, 150 DPI image CDN URLs, social txt, Breeze prompts) " +
        "for a staged campaign.",
      inputSchema: {
        type: "object",
        properties: {
          campaign: { type: "string", description: "Campaign slug, e.g. hvac-pm-fm-2026" },
          title: { type: "string", description: "Human-readable campaign title for REVIEW.md header" },
          blogId: { type: "string" },
          emailId: { type: "string" },
          socialImageUrl: { type: "string", description: "HubSpot CDN URL for 150 DPI social image" },
          emailBannerUrl: { type: "string", description: "HubSpot CDN URL for 150 DPI email banner" },
          blogFeaturedImageUrl: { type: "string", description: "HubSpot CDN URL for 150 DPI blog hero" },
          socialCopyPath: { type: "string", description: "Absolute or repo-relative path to .txt copy" },
          visualTopic: {
            type: "string",
            description: "Visual brief — auto-generates Breeze prompts in REVIEW.md",
          },
          breezeAudience: { type: "string", description: "Audience for Breeze prompt generation" },
          breezePromptsJson: {
            type: "string",
            description: 'JSON object with blog_featured, email_header, social prompt strings',
          },
        },
        required: ["campaign", "blogId", "emailId", "socialImageUrl"],
      },
    },
    {
      name: "hubspot_content_upload_social_image",
      description:
        "Generate branded 300×300 social image at 150 DPI (625×625 px) and upload to HubSpot File Manager. " +
        "Requires HUBSPOT_ACCESS_TOKEN with files scope.",
      inputSchema: {
        type: "object",
        properties: {
          campaign: { type: "string", description: "Campaign slug" },
          headline: { type: "string", description: "Short headline on the 300x300 card (no subheading)" },
          filename: { type: "string", description: "Upload filename override" },
          folderPath: { type: "string", description: "HubSpot folder path, default /campaign-images/{campaign}" },
          trade: { type: "string", enum: ["hvac", "plumbing", "electrical"] },
          bgUrl: { type: "string", description: "Background photo URL override" },
        },
        required: ["campaign", "headline"],
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

  if (name === "hubspot_content_get_package_brief") {
    const pyArgs = ["get-package-brief"];
    if (args.topic) pyArgs.push("--topic", args.topic);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_stage_content_package") {
    const pyArgs = ["stage-content-package"];
    if (args.packageFile) {
      pyArgs.push("--package-file", args.packageFile);
    } else if (args.package) {
      pyArgs.push("--package-json", JSON.stringify(args.package));
    } else {
      throw new Error("stage_content_package requires package or packageFile");
    }
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_refresh_campaign_images") {
    const pyArgs = ["refresh-campaign-images", "--campaign", args.campaign];
    if (args.blogId) pyArgs.push("--blog-id", args.blogId);
    if (args.emailId) pyArgs.push("--email-id", args.emailId);
    if (args.bgFile) pyArgs.push("--bg-file", args.bgFile);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_get_campaign_links") {
    const result = await runPython(["get-campaign-links", "--campaign", args.campaign]);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_verify_campaign_draft_status") {
    const pyArgs = ["verify-campaign-draft-status"];
    if (args.campaign) pyArgs.push("--campaign", args.campaign);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_get_config") {
    const result = await runPython(["get-config"]);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_login") {
    const result = await runPython(["login"]);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_auth_status") {
    const result = await runPython(["auth-status"]);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_logout") {
    const result = await runPython(["logout"]);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_create_blog_draft") {
    const pyArgs = [
      "create-blog-draft",
      "--title",
      args.title,
      "--meta-description",
      args.metaDescription,
    ];
    if (args.bodyFile) {
      pyArgs.push("--body-file", args.bodyFile);
    } else if (args.body) {
      pyArgs.push("--body", args.body);
    } else {
      throw new Error("create_blog_draft requires body or bodyFile");
    }
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
    if (args.htmlBodyFile) {
      pyArgs.push("--html-body-file", args.htmlBodyFile);
    } else if (args.htmlBody) {
      pyArgs.push("--html-body", args.htmlBody);
    }
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
    if (args.visualTopic) pyArgs.push("--visual-topic", args.visualTopic);
    if (args.breezeAudience) pyArgs.push("--breeze-audience", args.breezeAudience);
    if (args.emailBannerUrl) pyArgs.push("--email-banner-url", args.emailBannerUrl);
    if (args.blogFeaturedImageUrl) pyArgs.push("--blog-featured-image-url", args.blogFeaturedImageUrl);
    if (args.breezePromptsJson) pyArgs.push("--breeze-prompts-json", args.breezePromptsJson);
    const result = await runPython(pyArgs);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }

  if (name === "hubspot_content_upload_social_image") {
    const pyArgs = [
      "upload-social-image",
      "--campaign",
      args.campaign,
      "--headline",
      args.headline,
    ];
    if (args.filename) pyArgs.push("--filename", args.filename);
    if (args.folderPath) pyArgs.push("--folder-path", args.folderPath);
    if (args.trade) pyArgs.push("--trade", args.trade);
    if (args.bgUrl) pyArgs.push("--bg-url", args.bgUrl);
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
