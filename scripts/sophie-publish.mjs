#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const SITE_URL = "https://deepgill1004-hue.github.io/feifei-yubai-site/";
const LINE_URL = "https://line.me/R/ti/p/@371arhqu";
const root = process.cwd();

const imagePool = [
  { file: "assets/sophie-portrait-serious.jpg", keywords: ["麻醉", "風險", "線雕", "法規", "糾紛", "栓塞", "安全"] },
  { file: "assets/sophie-portrait-tablet.jpg", keywords: ["玻尿酸", "肉毒", "材料", "紀錄", "清單", "比較"] },
  { file: "assets/sophie-portrait-home.jpg", keywords: ["媽媽", "50", "抗老", "停經", "保養", "膠原"] },
  { file: "assets/sophie-portrait-laugh.jpg", keywords: ["水光", "膚質", "口服", "日常", "入門"] },
  { file: "assets/sophie-portrait-clinic.jpg", keywords: ["診所", "諮詢", "醫美", "療程", "預算"] }
];

const keywordSlugMap = [
  ["黑眼圈", "dark-circles"],
  ["肉毒", "botox"],
  ["玻尿酸", "hyaluronic-acid"],
  ["線雕", "thread-lift"],
  ["舒眠", "anesthesia"],
  ["麻醉", "anesthesia"],
  ["電波", "thermage"],
  ["音波", "ultherapy"],
  ["水光", "skinbooster"],
  ["膠原", "collagen"],
  ["媽媽", "50-plus-aesthetic"],
  ["抗老", "anti-aging"],
  ["法規", "aesthetic-regulation"],
  ["新規", "aesthetic-regulation"],
  ["RADIESSE", "radiesse"],
  ["瘦瘦針", "glp1"]
];

function usage() {
  return `用法:
  node scripts/sophie-publish.mjs --keyword "肉毒抗體" --title "肉毒打久突然沒效？先看三件事"
  node scripts/sophie-publish.mjs --keyword "線雕修復" --source "C:\\Users\\user\\sophie-agent\\content\\xxx.md"
  node scripts/sophie-publish.mjs --keyword "玻尿酸材料" --slug filler-material-checklist --generate-image
  node scripts/sophie-publish.mjs --keyword "黑眼圈" --dry-run

選項:
  --keyword <文字>       觸發關鍵字，必填
  --title <標題>         不填時自動生成爆款標題
  --slug <slug>          不填時由關鍵字推導
  --source <md/txt>      從 Sophie Agent 或其他長文檔讀素材
  --body-file <md/txt>   直接使用該檔作為網站文章主體
  --description <文字>   SEO 描述
  --generate-image       有 OPENAI_API_KEY 時呼叫既有 imgen 工具生成圖
  --line-send            產出後直接 LINE broadcast，需環境變數與外部網路
  --dry-run              只列出計畫，不寫檔
  --json                 輸出 manifest JSON`;
}

function parseArgs(argv) {
  const options = { dryRun: false, generateImage: false, lineSend: false, json: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--keyword") options.keyword = argv[++i];
    else if (arg === "--title") options.title = argv[++i];
    else if (arg === "--slug") options.slug = argv[++i];
    else if (arg === "--source") options.source = argv[++i];
    else if (arg === "--body-file") options.bodyFile = argv[++i];
    else if (arg === "--description") options.description = argv[++i];
    else if (arg === "--dry-run") options.dryRun = true;
    else if (arg === "--generate-image") options.generateImage = true;
    else if (arg === "--line-send") options.lineSend = true;
    else if (arg === "--json") options.json = true;
    else if (arg === "--help" || arg === "-h") options.help = true;
  }
  return options;
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function escapeHtml(input = "") {
  return String(input)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function normalizeSlug(input) {
  return String(input || "")
    .toLowerCase()
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}

function inferSlug(keyword) {
  const found = keywordSlugMap.find(([key]) => keyword.includes(key));
  if (found) return found[1];
  const ascii = normalizeSlug(keyword);
  if (ascii) return ascii;
  let hash = 0;
  for (const char of keyword) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return `sophie-topic-${hash.toString(16).slice(0, 8)}`;
}

function getNextIssue() {
  const files = fs.readdirSync(path.join(root, "letters"));
  const max = files.reduce((acc, file) => {
    const match = file.match(/^(\d{3})-/);
    return match ? Math.max(acc, Number(match[1])) : acc;
  }, 0);
  return String(max + 1).padStart(3, "0");
}

function pickImage(keyword) {
  const hit = imagePool.find((item) => item.keywords.some((key) => keyword.includes(key)));
  return hit?.file || "assets/sophie-portrait-clinic.jpg";
}

function buildHashtags(keyword) {
  const tags = new Set(["#蘇菲餘白", "#醫美判斷力", "#醫美避坑", "#醫美諮詢", "#台灣醫美"]);
  if (keyword.includes("肉毒")) tags.add("#肉毒桿菌");
  if (keyword.includes("玻尿酸")) tags.add("#玻尿酸");
  if (keyword.includes("線雕")) tags.add("#線雕拉提");
  if (keyword.includes("電波")) tags.add("#鳳凰電波");
  if (keyword.includes("音波")) tags.add("#音波拉提");
  if (keyword.includes("水光")) tags.add("#水光針");
  if (keyword.includes("麻醉") || keyword.includes("舒眠")) tags.add("#醫美安全");
  if (keyword.includes("膠原") || keyword.includes("口服")) tags.add("#口服美容");
  if (keyword.includes("抗老") || keyword.includes("50")) tags.add("#抗老保養");
  if (keyword.includes("法規") || keyword.includes("新規")) tags.add("#醫美法規");
  return Array.from(tags).slice(0, 10);
}

function defaultTitle(keyword) {
  return `${keyword}不是你以為的那樣：進診所前先問三句話`;
}

function defaultDescription(keyword) {
  return `${keyword}相關醫美判斷整理：常見誤解、風險提醒、諮詢前必問問題與蘇菲的消費者自保清單。`;
}

function extractSourceText(sourcePath) {
  if (!sourcePath) return "";
  const raw = fs.readFileSync(sourcePath, "utf8").trim();
  const lines = raw.split(/\r?\n/);
  const start = lines.findIndex((line) => /方格子|SEO 長文|Vocus/.test(line));
  const sliced = start >= 0 ? lines.slice(start + 1) : lines;
  const end = sliced.findIndex((line, index) => index > 20 && /^##\s*(7|LinkedIn|LINE|TikTok|評論|蘇菲生圖|大字報)/i.test(line));
  return (end >= 0 ? sliced.slice(0, end) : sliced).join("\n").trim();
}

function markdownToHtml(markdown) {
  const lines = markdown.split(/\r?\n/);
  const html = [];
  let list = [];

  function flushList() {
    if (!list.length) return;
    html.push(`<ul class="letter-checks">${list.map((item) => `<li>${formatInline(item)}</li>`).join("")}</ul>`);
    list = [];
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || /^---+$/.test(line) || /^>?\s*📋/.test(line)) {
      flushList();
      continue;
    }
    if (/^#{1,2}\s+/.test(line)) {
      flushList();
      html.push(`<h2>${formatInline(line.replace(/^#{1,2}\s+/, ""))}</h2>`);
    } else if (/^#{3,6}\s+/.test(line)) {
      flushList();
      html.push(`<h3>${formatInline(line.replace(/^#{3,6}\s+/, ""))}</h3>`);
    } else if (/^[-*]\s+/.test(line)) {
      list.push(line.replace(/^[-*]\s+/, ""));
    } else if (/^\d+[.)、]\s+/.test(line)) {
      list.push(line.replace(/^\d+[.)、]\s+/, ""));
    } else if (/^>/.test(line)) {
      flushList();
      html.push(`<p>${formatInline(line.replace(/^>\s?/, ""))}</p>`);
    } else {
      flushList();
      html.push(`<p>${formatInline(line)}</p>`);
    }
  }
  flushList();
  return html.join("\n");
}

function stripInternalSections(markdown) {
  const internalHeading = /^(#{1,3})\s*(查核來源|參考來源|Sources|References)\s*$/i;
  const lines = markdown.split(/\r?\n/);
  const kept = [];
  let skipping = false;
  let skipLevel = 0;

  for (const line of lines) {
    const heading = line.trim().match(/^(#{1,6})\s+/);
    if (internalHeading.test(line.trim())) {
      skipping = true;
      skipLevel = line.trim().match(/^(#{1,6})/)?.[1].length || 2;
      continue;
    }
    if (skipping && heading && heading[1].length <= skipLevel) {
      skipping = false;
    }
    if (!skipping) kept.push(line);
  }

  return kept.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

function formatInline(text) {
  return escapeHtml(text)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" rel="noopener">$1</a>');
}

function buildDefaultArticleMarkdown({ keyword, title }) {
  return `# ${title}

她傳訊息來的時候，只問了一句：

「蘇菲，這個我是不是該做？」

我最怕的就是這種問題。不是因為不能回答，而是因為「該不該做」通常不是第一題。第一題應該是：你到底想改善什麼？你看到的問題，是真的問題，還是被療程名字帶走的焦慮？

## 先把問題講清楚

${keyword}最容易被賣成一個簡單答案。但醫美沒有這麼簡單。同一個困擾，可能來自皮膚、脂肪、肌肉、骨架、生活習慣，也可能只是期待值被廣告拉太高。

如果前面沒有分型，後面問價格、問幾 cc、問幾條、問幾發，都會變成錯的比較。

## 最常見的踩雷點

- 只看療程名稱，不看自己的狀態。
- 只問價格，不問風險與修正方案。
- 只看案例照，不問案例是不是跟自己同型。
- 只聽諮詢師說適合，沒有聽醫師說為什麼。

## 進診所前先問三句話

1. 我這個問題，你判斷是哪一型？依據是什麼？
2. 這個療程能改善什麼？不能改善什麼？
3. 如果效果不如預期，後續怎麼處理？

這三句話問完，很多話術會自己露出破綻。

## 蘇菲的話

我不是要你不要做醫美。我是要你不要在還沒弄懂問題前，就先買答案。

好的醫美不是做很多，而是判斷更準。`;
}

function buildArticleBody({ keyword, title, bodyMarkdown, hashtags }) {
  const publicMarkdown = stripInternalSections(bodyMarkdown);
  const core = markdownToHtml(publicMarkdown.replace(/^# .+$/m, "").trim());
  return `${core}

<p class="hashtag-line">${hashtags.map(escapeHtml).join(" ")}</p>

<section class="letter-cta">
  <h2>延伸整理</h2>
  <p>我會在 LINE 裡用更白話的方式拆，也會把完整文章與延伸整理留在網站。</p>
  <ul class="letter-checks">
    <li>官方 LINE：<a href="${LINE_URL}" rel="noopener">${LINE_URL}</a></li>
    <li>蘇菲餘白網站：<a href="${SITE_URL}" rel="noopener">${SITE_URL}</a></li>
  </ul>
  <div class="panel-actions">
    <a class="button primary" href="../consult.html">整理我的諮詢問題</a>
    <a class="button secondary" href="./index.html">回文章列表</a>
  </div>
</section>`;
}

function buildHtmlPage({ title, description, keyword, issue, slug, image, bodyHtml, hashtags }) {
  const relativeImage = image.startsWith("assets/") ? `../${image}` : image;
  const publicUrl = `${SITE_URL}letters/${issue}-${slug}.html`;
  return `<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)}｜蘇菲餘白</title>
    <meta name="description" content="${escapeHtml(description)}" />
    <meta property="og:title" content="${escapeHtml(title)}｜蘇菲餘白" />
    <meta property="og:description" content="${escapeHtml(description)}" />
    <meta property="og:type" content="article" />
    <meta property="og:image" content="${escapeHtml(relativeImage)}" />
    <link rel="canonical" href="${publicUrl}" />
    <link rel="stylesheet" href="../assets/styles-v2.css?v=20260503-2" />
  </head>
  <body>
    <header class="site-header" aria-label="主要導覽">
      <a class="brand" href="../index.html">蘇菲餘白</a>
      <nav>
        <a href="../about.html">關於</a>
        <a href="../treatments.html">療程主題</a>
        <a href="./index.html">文章</a>
        <a href="../faq.html">FAQ</a>
        <a href="../consult.html">諮詢</a>
      </nav>
    </header>

    <main>
      <section class="letter-masthead">
        <div class="section-inner letter-masthead-grid">
          <div>
            <p class="eyebrow">Sophie Publishing Pipeline</p>
            <h1>${escapeHtml(title)}</h1>
            <p class="letter-dek">${escapeHtml(description)}</p>
            <div class="letter-meta-row">
              <span>Sophie Agent</span>
              <span>${escapeHtml(keyword)}</span>
              <span>${escapeHtml(hashtags.slice(0, 3).join(" / "))}</span>
            </div>
          </div>
          <figure class="letter-portrait">
            <img src="${escapeHtml(relativeImage)}" alt="蘇菲整理 ${escapeHtml(keyword)} 醫美判斷重點" />
          </figure>
        </div>
      </section>

      <section class="section">
        <div class="section-inner letter-reading-grid">
          <aside class="letter-sidebar">
            <p class="path-label">爆款拆解</p>
            <ol>
              <li>先用真實困擾開場，不從名詞開場。</li>
              <li>把療程話術翻成消費者能問的問題。</li>
              <li>文末用主題標籤與 LINE CTA 承接互動。</li>
            </ol>
            <div class="panel-actions">
              <a class="button primary" href="../consult.html">整理我的問題</a>
              <a class="button secondary" href="${LINE_URL}" rel="noopener">加入 LINE</a>
            </div>
          </aside>

          <article class="letter-body">
${bodyHtml}
          </article>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <p>蘇菲餘白｜內容僅供衛教與消費判斷參考，不取代醫師診療。</p>
    </footer>
  </body>
</html>
`;
}

function insertAfter(content, marker, insertion) {
  const index = content.indexOf(marker);
  if (index < 0) throw new Error(`找不到插入點: ${marker}`);
  return content.slice(0, index + marker.length) + insertion + content.slice(index + marker.length);
}

function updateLettersIndex({ title, description, keyword, issue, slug }) {
  const file = path.join(root, "letters", "index.html");
  const content = fs.readFileSync(file, "utf8");
  const href = `./${issue}-${slug}.html`;
  if (content.includes(href)) return;
  const item = `
            <article class="letter-item">
              <a href="${href}" aria-label="閱讀 ${escapeHtml(title)}">
                <span class="letter-issue">${issue}</span>
                <div>
                  <p class="path-label">${escapeHtml(keyword)}</p>
                  <h3>${escapeHtml(title)}</h3>
                  <p>${escapeHtml(description)}</p>
                </div>
              </a>
            </article>
`;
  fs.writeFileSync(file, insertAfter(content, '<div class="letter-list">', item), "utf8");
}

function updateSitemap({ issue, slug }) {
  const file = path.join(root, "sitemap.xml");
  const content = fs.readFileSync(file, "utf8");
  const loc = `${SITE_URL}letters/${issue}-${slug}.html`;
  if (content.includes(loc)) return;
  const item = `  <url>
    <loc>${loc}</loc>
    <lastmod>${today()}</lastmod>
  </url>
`;
  fs.writeFileSync(file, content.replace("</urlset>", `${item}</urlset>`), "utf8");
}

function updateFeed({ title, description, issue, slug }) {
  const file = path.join(root, "feed.xml");
  const content = fs.readFileSync(file, "utf8");
  const link = `${SITE_URL}letters/${issue}-${slug}.html`;
  if (content.includes(link)) return;
  const now = new Date().toUTCString();
  const updated = content.replace(/<lastBuildDate>.*?<\/lastBuildDate>/, `<lastBuildDate>${now}</lastBuildDate>`);
  const item = `
    <item>
      <title>${escapeHtml(title)}</title>
      <link>${link}</link>
      <guid isPermaLink="true">${link}</guid>
      <pubDate>${now}</pubDate>
      <description><![CDATA[${description}]]></description>
      <content:encoded><![CDATA[
        <p>${description}</p>
        <p><a href="${link}">閱讀完整文章</a></p>
      ]]></content:encoded>
    </item>`;
  fs.writeFileSync(file, insertAfter(updated, /<lastBuildDate>.*?<\/lastBuildDate>/.exec(updated)[0], item), "utf8");
}

function buildDistribution({ title, description, keyword, issue, slug, hashtags, bodyMarkdown, imagePrompt }) {
  const url = `${SITE_URL}letters/${issue}-${slug}.html`;
  const hashtagLine = hashtags.join(" ");
  const publicMarkdown = stripInternalSections(bodyMarkdown);
  return {
    line: `${title}

${description}

完整文章：
${url}

回我「${keyword.slice(0, 8)}」，我再幫你整理諮詢前該問哪三句。`,
    threads: `${title}

${description}

我最想提醒的是：不要先買療程，先問清楚自己是哪一型。

${url}

${hashtagLine}`,
    ig: `${title}

先收藏這篇。下次進診所前，把「我適合嗎」換成三個更精準的問題：

1. 你判斷我是什麼型？
2. 這個療程不能改善什麼？
3. 如果不如預期怎麼處理？

完整文章在蘇菲餘白。
${url}

${hashtagLine}`,
    fanggezi: `${publicMarkdown}

---

${hashtagLine}

官方 LINE：${LINE_URL}
蘇菲餘白網站：${SITE_URL}
`,
    imagePrompt
  };
}

function buildImagePrompt(keyword, title) {
  return `蘇菲在明亮乾淨的醫美診所諮詢室，正在整理「${keyword}」的療程判斷筆記。畫面是直式社群封面，主標題留白可放「${title}」，氛圍專業、溫柔、帶一點清醒的提醒感。人物不特寫五官，重點放在姿態、資料夾、平板、診間空間與可收藏的知識感。禁咖啡廳，禁誇大療效，禁前後對比。`;
}

function maybeGenerateImage(keyword, slug) {
  const prompt = buildImagePrompt(keyword, keyword);
  const outDir = path.join(root, "output", "imgen");
  const result = spawnSync(process.execPath, [
    "scripts/imgen-topic-tool.mjs",
    prompt,
    "--topic",
    "social-carousel-cover",
    "--format",
    "jpeg",
    "--out",
    outDir,
    "--generate",
    "--json"
  ], { cwd: root, encoding: "utf8" });

  if (result.status !== 0) {
    return { ok: false, error: result.stderr || result.stdout };
  }

  const metadata = JSON.parse(result.stdout);
  const target = path.join(root, "assets", `sophie-generated-${slug}.jpeg`);
  fs.copyFileSync(metadata.imageFile, target);
  return { ok: true, image: `assets/sophie-generated-${slug}.jpeg`, metadata };
}

function writeDistribution(outDir, distribution, manifest) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, "line.txt"), distribution.line, "utf8");
  fs.writeFileSync(path.join(outDir, "threads.txt"), distribution.threads, "utf8");
  fs.writeFileSync(path.join(outDir, "ig.txt"), distribution.ig, "utf8");
  fs.writeFileSync(path.join(outDir, "fanggezi.md"), distribution.fanggezi, "utf8");
  fs.writeFileSync(path.join(outDir, "image-prompt.txt"), `${distribution.imagePrompt}\n`, "utf8");
  fs.writeFileSync(path.join(outDir, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
}

function runChecks() {
  assertXmlShape(path.join(root, "sitemap.xml"), "urlset");
  assertXmlShape(path.join(root, "feed.xml"), "rss");
}

function assertXmlShape(file, rootTag) {
  const xml = fs.readFileSync(file, "utf8");
  const label = path.relative(root, file);
  if (!xml.includes(`<${rootTag}`) || !xml.includes(`</${rootTag}>`)) {
    throw new Error(`${label} 缺少 ${rootTag} 根節點`);
  }
  if (/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/.test(xml)) {
    throw new Error(`${label} 含有 XML 不允許的控制字元`);
  }

  const withoutCdata = xml.replace(/<!\[CDATA\[[\s\S]*?\]\]>/g, "");
  const bareAmp = /&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)/.exec(withoutCdata);
  if (bareAmp) {
    throw new Error(`${label} 含有未跳脫的 & 字元`);
  }

  const stack = [];
  const tagPattern = /<([^!?][^>\s/]*)([^>]*)>|<\/([^>\s]+)>/g;
  let match;
  while ((match = tagPattern.exec(withoutCdata))) {
    if (match[3]) {
      const expected = stack.pop();
      if (expected !== match[3]) throw new Error(`${label} XML 標籤未正確閉合：${match[3]}`);
      continue;
    }
    const tag = match[1];
    const rest = match[2] || "";
    if (rest.trim().endsWith("/")) continue;
    stack.push(tag);
  }
  if (stack.length) throw new Error(`${label} XML 標籤未正確閉合：${stack.at(-1)}`);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
    return;
  }
  if (!options.keyword) {
    console.error(usage());
    process.exitCode = 1;
    return;
  }

  const issue = getNextIssue();
  const baseSlug = options.slug ? normalizeSlug(options.slug) : inferSlug(options.keyword);
  const slug = `${baseSlug}-${today().replaceAll("-", "")}`;
  const title = options.title || defaultTitle(options.keyword);
  const description = options.description || defaultDescription(options.keyword);
  const hashtags = buildHashtags(options.keyword);
  const imagePrompt = buildImagePrompt(options.keyword, title);

  let image = pickImage(options.keyword);
  let imageGeneration = null;
  if (options.generateImage && !options.dryRun) {
    imageGeneration = maybeGenerateImage(options.keyword, slug);
    if (imageGeneration.ok) image = imageGeneration.image;
  }

  const sourceText = options.bodyFile
    ? fs.readFileSync(options.bodyFile, "utf8")
    : extractSourceText(options.source);
  const bodyMarkdown = sourceText || buildDefaultArticleMarkdown({ keyword: options.keyword, title });
  const bodyHtml = buildArticleBody({ keyword: options.keyword, title, bodyMarkdown, hashtags });
  const pageHtml = buildHtmlPage({ title, description, keyword: options.keyword, issue, slug, image, bodyHtml, hashtags });
  const pageFile = path.join(root, "letters", `${issue}-${slug}.html`);
  const outDir = path.join(root, "output", "sophie-publishing", `${today()}-${slug}`);
  const distribution = buildDistribution({ title, description, keyword: options.keyword, issue, slug, hashtags, bodyMarkdown, imagePrompt });
  const manifest = {
    issue,
    slug,
    title,
    description,
    keyword: options.keyword,
    url: `${SITE_URL}letters/${issue}-${slug}.html`,
    image,
    hashtags,
    outDir: path.relative(root, outDir),
    pageFile: path.relative(root, pageFile),
    source: options.source || options.bodyFile || null,
    imageGeneration
  };

  if (options.dryRun) {
    console.log(JSON.stringify({ mode: "dry-run", manifest, distributionPreview: distribution }, null, 2));
    return;
  }

  fs.writeFileSync(pageFile, pageHtml, "utf8");
  updateLettersIndex({ title, description, keyword: options.keyword, issue, slug });
  updateSitemap({ issue, slug });
  updateFeed({ title, description, issue, slug });
  writeDistribution(outDir, distribution, manifest);
  runChecks();

  if (options.lineSend) {
    const lineResult = spawnSync(process.execPath, [
      "scripts/line-broadcast.mjs",
      "--file",
      path.join(outDir, "line.txt"),
      "--send"
    ], { cwd: root, encoding: "utf8" });
    manifest.lineBroadcast = {
      status: lineResult.status,
      stdout: lineResult.stdout.trim(),
      stderr: lineResult.stderr.trim()
    };
    fs.writeFileSync(path.join(outDir, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  }

  if (options.json) console.log(JSON.stringify(manifest, null, 2));
  else {
    console.log(`OK: ${manifest.url}`);
    console.log(`文章: ${manifest.pageFile}`);
    console.log(`分發包: ${manifest.outDir}`);
    if (imageGeneration && !imageGeneration.ok) console.log(`圖片生成未完成: ${imageGeneration.error}`);
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
