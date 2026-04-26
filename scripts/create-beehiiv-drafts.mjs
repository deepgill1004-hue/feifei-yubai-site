import fs from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const postsDir = path.join(root, "beehiiv", "posts");
const dryRun = process.argv.includes("--dry-run") || process.env.BEEHIIV_DRY_RUN === "true";

const apiKey = process.env.BEEHIIV_API_KEY;
const publicationId = process.env.BEEHIIV_PUBLICATION_ID;
const templateId = process.env.BEEHIIV_POST_TEMPLATE_ID;
const allowDuplicate = process.env.BEEHIIV_ALLOW_DUPLICATE === "true";

function getBodyContent(html) {
  const match = html.match(/<body\b[^>]*>([\s\S]*?)<\/body>/i);
  return (match ? match[1] : html).trim();
}

async function readJson(file) {
  return JSON.parse(await fs.readFile(file, "utf8"));
}

async function requestBeehiiv(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  const text = await response.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }

  if (!response.ok) {
    const detail = typeof body === "string" ? body : JSON.stringify(body, null, 2);
    throw new Error(`beehiiv API ${response.status}: ${detail}`);
  }

  return body;
}

async function postExists(slug) {
  if (!slug || allowDuplicate) return false;
  const params = new URLSearchParams({
    status: "all",
    platform: "all"
  });
  params.append("slugs[]", slug);

  const url = `https://api.beehiiv.com/v2/publications/${publicationId}/posts?${params}`;
  const result = await requestBeehiiv(url, { method: "GET" });
  return Array.isArray(result?.data) && result.data.length > 0;
}

async function createDraft(postFile) {
  const post = await readJson(postFile);
  const templatePath = path.resolve(path.dirname(postFile), post.template);
  const html = await fs.readFile(templatePath, "utf8");

  const payload = {
    title: post.title,
    subtitle: post.subtitle,
    body_content: getBodyContent(html),
    status: post.status || "draft"
  };

  if (templateId) payload.post_template_id = templateId;

  if (dryRun) {
    console.log(JSON.stringify({ file: path.relative(root, postFile), payload }, null, 2));
    return;
  }

  if (!apiKey || !publicationId) {
    throw new Error("Missing BEEHIIV_API_KEY or BEEHIIV_PUBLICATION_ID.");
  }

  if (await postExists(post.slug)) {
    console.log(`Skipped existing beehiiv post slug: ${post.slug}`);
    return;
  }

  const url = `https://api.beehiiv.com/v2/publications/${publicationId}/posts`;
  const result = await requestBeehiiv(url, {
    method: "POST",
    body: JSON.stringify(payload)
  });

  console.log(`Created beehiiv draft: ${result?.data?.id || "(unknown id)"} ${post.title}`);
}

const entries = await fs.readdir(postsDir, { withFileTypes: true });
const postFiles = entries
  .filter((entry) => entry.isFile() && entry.name.endsWith(".json"))
  .map((entry) => path.join(postsDir, entry.name))
  .sort();

if (!postFiles.length) {
  console.log("No beehiiv post definitions found.");
}

for (const postFile of postFiles) {
  await createDraft(postFile);
}
