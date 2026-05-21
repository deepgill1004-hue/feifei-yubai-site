#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const API_BASE = "https://api.beehiiv.com/v2";
const root = process.cwd();

function loadDotEnv() {
  const envPath = path.join(root, ".env");
  if (!fs.existsSync(envPath)) return;
  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    if (!line || line.trimStart().startsWith("#")) continue;
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)\s*$/);
    if (!match || process.env[match[1]]) continue;
    process.env[match[1]] = match[2].replace(/^["']|["']$/g, "");
  }
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function paragraph(text) {
  return `<p style="margin:0 0 18px;color:#4b4038;font-size:17px;line-height:1.9;">${escapeHtml(text)}</p>`;
}

function buildBodyContent(post) {
  const articleCards = post.articles
    .map((article, index) => {
      const number = String(index + 1).padStart(2, "0");
      return `
        <tr>
          <td style="padding:18px 0;border-top:1px solid #eadfd2;">
            <div style="color:#9a7b5d;font-size:13px;letter-spacing:.12em;margin-bottom:6px;">${number} / ${escapeHtml(article.label || "Sophie Yubai")}</div>
            <a href="${escapeHtml(article.url)}" style="color:#6c4f3d;text-decoration:none;font-size:21px;line-height:1.45;font-weight:700;">${escapeHtml(article.title)}</a>
            <p style="margin:8px 0 0;color:#5b514a;font-size:16px;line-height:1.75;">${escapeHtml(article.description)}</p>
          </td>
        </tr>`;
    })
    .join("");

  const sourceNotes = (post.source_notes || [])
    .map((note) => `<li style="margin:0 0 8px;color:#5b514a;font-size:15px;line-height:1.7;">${escapeHtml(note)}</li>`)
    .join("");

  return `
<div style="background:#fbf7f0;margin:0;padding:0;font-family:'Noto Serif TC','PMingLiU','Songti TC',Georgia,serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;background:#fbf7f0;">
    <tr>
      <td align="center" style="padding:28px 14px 42px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:720px;border-collapse:collapse;background:#fffdf8;border:1px solid #eadfd2;">
          <tr>
            <td style="padding:30px 30px 12px;">
              <div style="color:#9a7b5d;font-size:14px;letter-spacing:.16em;text-transform:uppercase;">Sophie Yubai Digest</div>
              <h1 style="margin:12px 0 12px;color:#493d35;font-size:30px;line-height:1.45;font-weight:700;">${escapeHtml(post.title)}</h1>
              <p style="margin:0;color:#77695f;font-size:17px;line-height:1.8;">${escapeHtml(post.subtitle || "")}</p>
            </td>
          </tr>
          <tr>
            <td style="padding:10px 30px 6px;">
              ${paragraph(post.intro || "")}
              <div style="margin:22px 0;padding:18px 20px;background:#f7efe5;border-left:4px solid #b9906b;">
                <p style="margin:0;color:#5b514a;font-size:16px;line-height:1.8;">${escapeHtml(post.curator_note || "")}</p>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:0 30px 10px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                ${articleCards}
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 30px 26px;">
              <div style="padding:18px 20px;background:#faf4ec;border:1px solid #eadfd2;">
                <p style="margin:0 0 10px;color:#493d35;font-size:17px;line-height:1.7;font-weight:700;">今天整理素材時抓出的三條線</p>
                <ul style="margin:0;padding-left:19px;">${sourceNotes}</ul>
              </div>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 30px 34px;">
              <a href="${escapeHtml(post.cta_url)}" style="display:inline-block;padding:13px 24px;background:#6c4f3d;color:#fffdf8;text-decoration:none;font-size:17px;letter-spacing:.08em;">${escapeHtml(post.cta_label || "閱讀文章")}</a>
              <p style="margin:16px 0 0;color:#8b7d73;font-size:14px;line-height:1.7;">${escapeHtml(post.footer_note || "")}</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</div>`.trim();
}

function discoverPostFiles(args) {
  if (args.length) return args.map((file) => path.resolve(root, file));
  const postsDir = path.join(root, "beehiiv", "posts");
  if (!fs.existsSync(postsDir)) return [];
  return fs.readdirSync(postsDir)
    .filter((file) => file.endsWith(".json"))
    .map((file) => path.join(postsDir, file))
    .sort();
}

async function beehiivFetch(pathname, options = {}) {
  const response = await fetch(`${API_BASE}${pathname}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${process.env.BEEHIIV_API_KEY}`,
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  const text = await response.text();
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = { raw: text };
  }
  if (!response.ok) {
    throw new Error(`beehiiv ${response.status}: ${JSON.stringify(json)}`);
  }
  return json;
}

async function postExists(slug) {
  if (!slug || process.env.BEEHIIV_ALLOW_DUPLICATE === "true") return false;
  const params = new URLSearchParams({
    status: "all",
    platform: "all"
  });
  params.append("slugs[]", slug);
  const publicationId = process.env.BEEHIIV_PUBLICATION_ID;
  const result = await beehiivFetch(`/publications/${publicationId}/posts?${params}`, {
    method: "GET"
  });
  return Array.isArray(result?.data) && result.data.length > 0;
}

async function createDraft(postFile, dryRun) {
  const post = JSON.parse(fs.readFileSync(postFile, "utf8"));
  const bodyContent = post.body_content || buildBodyContent(post);
  const publicationId = process.env.BEEHIIV_PUBLICATION_ID;
  const payload = {
    title: post.title,
    subtitle: post.subtitle,
    status: post.status || "draft",
    body_content: bodyContent,
    custom_link_tracking_enabled: true,
    content_tags: post.content_tags || ["sophie-yubai", "digest"],
    email_settings: {
      email_subject_line: post.email_subject_line || post.title,
      email_preview_text: post.email_preview_text || post.subtitle,
      display_title_in_email: true,
      display_subtitle_in_email: true
    },
    web_settings: {
      slug: post.slug,
      hide_from_feed: Boolean(post.hide_from_feed)
    },
    seo_settings: {
      default_title: post.seo_title || post.title,
      default_description: post.seo_description || post.subtitle,
      og_title: post.seo_title || post.title,
      og_description: post.seo_description || post.subtitle,
      twitter_title: post.seo_title || post.title,
      twitter_description: post.seo_description || post.subtitle
    }
  };

  if (process.env.BEEHIIV_POST_TEMPLATE_ID) {
    payload.post_template_id = process.env.BEEHIIV_POST_TEMPLATE_ID;
  }

  if (dryRun) {
    console.log(JSON.stringify({ postFile, payload }, null, 2));
    return null;
  }

  if (await postExists(post.slug)) {
    console.log(JSON.stringify({
      post_file: path.relative(root, postFile),
      slug: post.slug,
      status: "skipped_existing"
    }, null, 2));
    return null;
  }

  const created = await beehiivFetch(`/publications/${publicationId}/posts`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
  const postId = created?.data?.id;
  const fetched = postId
    ? await beehiivFetch(`/publications/${publicationId}/posts/${postId}`)
    : null;
  const webUrl = fetched?.data?.web_url || null;
  const appUrl = postId ? `https://app.beehiiv.com/posts/${postId}` : null;
  console.log(JSON.stringify({
    post_file: path.relative(root, postFile),
    post_id: postId,
    status: fetched?.data?.status || payload.status,
    web_url: webUrl,
    app_url: appUrl
  }, null, 2));
  if (webUrl) console.log(`BEEHIIV_WEB_URL=${webUrl}`);
  if (appUrl) console.log(`BEEHIIV_APP_URL=${appUrl}`);
  return { postId, webUrl, appUrl };
}

async function main() {
  loadDotEnv();
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const postArgs = args.filter((arg) => arg !== "--dry-run");
  if (!dryRun && (!process.env.BEEHIIV_API_KEY || !process.env.BEEHIIV_PUBLICATION_ID)) {
    throw new Error("Missing BEEHIIV_API_KEY or BEEHIIV_PUBLICATION_ID.");
  }
  const postFiles = discoverPostFiles(postArgs);
  if (!postFiles.length) throw new Error("No beehiiv post JSON files found.");
  for (const postFile of postFiles) {
    await createDraft(postFile, dryRun);
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
