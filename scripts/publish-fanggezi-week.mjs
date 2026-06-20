#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const DEFAULT_SOURCE = "C:/Users/user/Downloads/方格子 7 篇長文（6_16–6_22）.md";
const DEFAULT_ASSET_DIR = "assets/fanggezi-2026-06-16-to-06-22";
const BODY_DIR = "output/fanggezi-2026-06-16-to-06-22/bodies";

const metadata = {
  D1: {
    keyword: "孫淑媚 牙齒矯正 隱性醫美",
    slug: "sun-shu-mei-dental-anti-aging",
    image: "D1_sun_shumei_dental.png",
    description: "從孫淑媚拔牙矯正談隱性醫美：真正耐老的關鍵，不只是打針修補，而是長期結構性投資。"
  },
  D2: {
    keyword: "EECP 體外反搏 心血管抗衰老",
    slug: "eecp-cardiovascular-anti-aging",
    image: "D2_eecp_treatment.png",
    description: "EECP 體外反搏不是按摩，而是從心血管循環切入的抗衰老管理，適合先理解機制與適用邊界。"
  },
  D3: {
    keyword: "ILIB 靜脈雷射 光生物調節",
    slug: "ilib-laser-photobiomodulation",
    image: "D3_ilib_laser.png",
    description: "ILIB 靜脈雷射用光生物調節討論細胞能量、循環與慢性發炎，重點是理解它不是一次返老還童的神話。"
  },
  D4: {
    keyword: "黃曉明 醫美 年齡管理",
    slug: "huang-xiaoming-age-management-authenticity",
    image: "D4_huang_xiaoming_tv.png",
    description: "從黃曉明被追問醫美談名人年齡管理：比做不做更重要的，是真實性與不過度的長期策略。"
  },
  D5: {
    keyword: "關之琳 過度填充 玻尿酸",
    slug: "guan-zhilin-filler-overload",
    image: "D5_guan_zhilin_mirror.png",
    description: "關之琳僵臉話題提醒我們：飽滿不等於年輕，過度填充可能讓臉失去動態與高級感。"
  },
  D6: {
    keyword: "Lumenis SILARIOUS 醫美設備安全",
    slug: "lumenis-silarious-device-safety",
    image: "D6_lumenis_device_demo.png",
    description: "從 Lumenis 與 SILARIOUS 談醫美設備代差：消費者不只要問價格，也要問影像導航與安全標準。"
  },
  D7: {
    keyword: "EECP ILIB 循環抗衰老",
    slug: "eecp-ilib-circulation-longevity",
    image: "D7_eecp_ilib_synergy.png",
    description: "EECP 與 ILIB 的協同概念，代表未來循環抗衰老不再靠單一療法，而是整合式健康資產管理。"
  }
};

function parseArgs(argv) {
  const options = {
    source: DEFAULT_SOURCE,
    assetDir: DEFAULT_ASSET_DIR,
    dailyDocsDir: "output/fanggezi-2026-06-16-to-06-22/daily-docs",
    dryRun: false
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--source") options.source = argv[++index];
    else if (arg === "--asset-dir") options.assetDir = argv[++index];
    else if (arg === "--daily-docs-dir") options.dailyDocsDir = argv[++index];
    else if (arg === "--dry-run") options.dryRun = true;
    else if (arg === "--help" || arg === "-h") options.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

function usage() {
  return `Usage:
  node scripts/publish-fanggezi-week.mjs
  node scripts/publish-fanggezi-week.mjs --source "C:/path/week.md" --asset-dir assets/fanggezi-week

Options:
  --source <path>     Fanggezi week markdown. Default: ${DEFAULT_SOURCE}
  --asset-dir <path>  Extracted image directory relative to repo. Default: ${DEFAULT_ASSET_DIR}
  --daily-docs-dir <path> Daily document output directory. Default: output/fanggezi-2026-06-16-to-06-22/daily-docs
  --dry-run           Parse and print planned posts without writing site files.`;
}

function extractArticles(raw) {
  const headers = [...raw.matchAll(/^##\s+(D\d)[^\n]*$/gm)];
  return headers.map((header, index) => {
    const id = header[1];
    const start = header.index + header[0].length;
    const end = headers[index + 1]?.index ?? raw.length;
    const chunk = raw.slice(start, end).trim();
    const title = chunk.match(/^\*\*標題：\*\*\s*(.+)$/m)?.[1]?.trim();
    const bodyStart = chunk.search(/^\*\*正文：\*\*\s*$/m);
    if (!title || bodyStart < 0) {
      throw new Error(`${id} is missing title or body.`);
    }
    let body = chunk.slice(bodyStart).replace(/^\*\*正文：\*\*\s*/m, "").trim();
    body = body.split(/\n---\s*\n\*蘇菲餘白/)[0].trim();
    body = body
      .replace(/\*官方 LINE:\[連結\]\*/g, "")
      .replace(/\*蘇菲餘白網站:\[連結\]\*/g, "")
      .replace(/\[連結\]/g, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
    return { id, title, body };
  });
}

function titleExists(title) {
  const indexPath = path.join(root, "letters", "index.html");
  if (!fs.existsSync(indexPath)) return false;
  return fs.readFileSync(indexPath, "utf8").includes(title);
}

function writeBodyFile(article) {
  fs.mkdirSync(path.join(root, BODY_DIR), { recursive: true });
  const file = path.join(root, BODY_DIR, `${article.id}.md`);
  fs.writeFileSync(file, `# ${article.title}\n\n${article.body}\n`, "utf8");
  return file;
}

function publishArticle(article, options) {
  const data = metadata[article.id];
  if (!data) throw new Error(`No metadata for ${article.id}.`);
  const bodyFile = writeBodyFile(article);
  const image = path.posix.join(options.assetDir.replaceAll("\\", "/"), data.image);
  if (!fs.existsSync(path.join(root, image))) {
    throw new Error(`Image not found for ${article.id}: ${image}`);
  }
  const args = [
    "scripts/sophie-publish.mjs",
    "--keyword", data.keyword,
    "--title", article.title,
    "--slug", data.slug,
    "--description", data.description,
    "--body-file", bodyFile,
    "--image", image,
    "--daily-docs-dir", options.dailyDocsDir,
    "--json"
  ];
  const result = spawnSync(process.execPath, args, { cwd: root, encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`${article.id} publish failed:\n${result.stdout}\n${result.stderr}`);
  }
  return JSON.parse(result.stdout);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
    return;
  }
  const sourcePath = path.resolve(options.source);
  const raw = fs.readFileSync(sourcePath, "utf8");
  const articles = extractArticles(raw);
  if (articles.length !== 7) {
    throw new Error(`Expected 7 articles, parsed ${articles.length}.`);
  }
  if (options.dryRun) {
    console.log(JSON.stringify(articles.map((article) => ({
      id: article.id,
      title: article.title,
      keyword: metadata[article.id]?.keyword,
      slug: metadata[article.id]?.slug,
      image: metadata[article.id]?.image,
      exists: titleExists(article.title)
    })), null, 2));
    return;
  }
  const manifests = [];
  for (const article of articles) {
    if (titleExists(article.title)) {
      console.log(`SKIP ${article.id}: ${article.title}`);
      continue;
    }
    manifests.push(await publishArticle(article, options));
  }
  console.log(JSON.stringify({ published: manifests }, null, 2));
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
