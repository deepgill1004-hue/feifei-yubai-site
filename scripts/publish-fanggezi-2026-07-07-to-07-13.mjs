#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const source = "C:/Users/user/Downloads/下週（7_7–7_13）方格子 發布文案.md";
const assetDir = "assets/fanggezi-2026-07-07-to-07-13";
const bodyDir = "output/fanggezi-2026-07-07-to-07-13/bodies";
const dailyDocsDir = "output/fanggezi-2026-07-07-to-07-13/daily-docs";

const metadata = [
  {
    keyword: "玻尿酸 球形顆粒 注射安全",
    slug: "hyaluronic-acid-particle-selection",
    image: "D1_star_needle.png",
    description: "玻尿酸不能只比品牌、價格與維持期；顆粒特性、安全資料、注射層次與醫師判斷，才是選擇材料時真正要問的事。"
  },
  {
    keyword: "GLP-1 減重 GLP Face 臉部老化",
    slug: "glp-face-weight-loss-aging",
    image: "D2_glp_face.png",
    description: "快速減重可能同時流失脂肪與瘦組織，讓臉部凹陷、鬆弛更明顯；減重期間應同步管理營養、肌肉與臉部變化。"
  },
  {
    keyword: "Morpheus8 微針電波 傳統電波",
    slug: "morpheus8-vs-monopolar-rf",
    image: "D3_morpheus8.png",
    description: "傳統電波與微針電波不是升級關係，而是作用深度、治療目標與恢復期不同；先分清鬆弛、脂肪與膚質問題再選療程。"
  },
  {
    keyword: "玻尿酸 饅化臉 過度填充",
    slug: "hyaluronic-acid-filler-buildup",
    image: "D4_hyaluronic_buildup.png",
    description: "玻尿酸長期疊加可能讓臉部比例與動態逐漸失真；比繼續補量更重要的，是先停、評估殘留與重新規劃結構。"
  },
  {
    keyword: "單極電波 雙極電波 射頻",
    slug: "monopolar-vs-bipolar-rf",
    image: "D5_monopolar_bipolar.png",
    description: "單極與雙極電波的能量路徑、作用深度和適用問題不同；不要只看療程名稱與價格，要看你的問題位在哪一層。"
  },
  {
    keyword: "音波拉提 電波拉提 選擇",
    slug: "ultrasound-vs-radiofrequency-lifting",
    image: "D6_ultrasound_vs_rf.png",
    description: "音波偏向深層支撐與輪廓，電波偏向真皮緊實與膚質；先判斷下垂、鬆弛與脂肪分布，才能避免選錯機器。"
  },
  {
    keyword: "醫美諮詢 療程規劃 消費判斷",
    slug: "most-important-aesthetic-question",
    image: "D7_most_important_question.png",
    description: "做醫美前最重要的不是問哪台機器最新，而是先確認自己真正要改善什麼，以及眼前方案如何對應你的結構與長期規劃。"
  }
];

function extractArticles(raw) {
  const headers = [...raw.matchAll(/^##\s+\d+\/\d+[^\n]*$/gm)];
  return headers.map((header, index) => {
    const start = header.index + header[0].length;
    const end = headers[index + 1]?.index ?? raw.length;
    const chunk = raw.slice(start, end).trim();
    const title = chunk.match(/^\*\*標題：(.+)\*\*$/m)?.[1]?.trim();
    if (!title) {
      throw new Error(`無法解析文章標題：${header[0]}`);
    }
    let body = chunk.replace(/^\*\*標題：.+\*\*\s*/m, "").trim();
    body = body
      .replace(/\n想了解更多醫美真話，LINE 加入：@371arhqu\s*\n蘇菲餘白：https:\/\/deepgill1004-hue\.github\.io\/feifei-yubai-site\/?\s*$/m, "")
      .replace(/\n---\s*$/m, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
    return { title, body };
  });
}

function publishArticle(article, data) {
  fs.mkdirSync(path.join(root, bodyDir), { recursive: true });
  const bodyFile = path.join(root, bodyDir, `${data.slug}.md`);
  fs.writeFileSync(bodyFile, `# ${article.title}\n\n${article.body}\n`, "utf8");

  const image = path.posix.join(assetDir, data.image);
  if (!fs.existsSync(path.join(root, image))) {
    throw new Error(`找不到圖片：${image}`);
  }

  const result = spawnSync(process.execPath, [
    "scripts/sophie-publish.mjs",
    "--keyword", data.keyword,
    "--title", article.title,
    "--slug", data.slug,
    "--description", data.description,
    "--body-file", bodyFile,
    "--image", image,
    "--daily-docs-dir", dailyDocsDir,
    "--json"
  ], { cwd: root, encoding: "utf8" });

  if (result.status !== 0) {
    throw new Error(result.stderr || result.stdout);
  }
  return JSON.parse(result.stdout);
}

const raw = fs.readFileSync(source, "utf8");
const articles = extractArticles(raw);
if (articles.length !== 7) {
  throw new Error(`預期 7 篇，實際解析 ${articles.length} 篇。`);
}

const published = articles.map((article, index) => publishArticle(article, metadata[index]));
console.log(JSON.stringify({ published }, null, 2));
