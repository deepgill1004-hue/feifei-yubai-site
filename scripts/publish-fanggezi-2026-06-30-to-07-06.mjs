#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const source = "C:/Users/user/Downloads/文件整理_2026-05-29/社群發布文案/下週（6_30–7_6）方格子 發布文案.md";
const assetDir = "assets/fanggezi-2026-06-30-to-07-06";
const bodyDir = "output/fanggezi-2026-06-30-to-07-06/bodies";
const dailyDocsDir = "output/fanggezi-2026-06-30-to-07-06/daily-docs";

const metadata = [
  {
    keyword: "IMCAS 國際醫美 醫師進修",
    slug: "imcas-doctor-training-reality",
    image: "D1_imcas_doctor_training.jpg",
    description: "台灣有世界級醫師，不代表每家診所都有同樣水準；真正該查的是醫師背景、持續進修與風險說明。"
  },
  {
    keyword: "醫美診所 偷拍 隱私安全",
    slug: "clinic-hidden-camera-privacy",
    image: "D2_clinic_privacy_warning.jpg",
    description: "從診間偷拍與停業爭議談醫美隱私：進療程室前，消費者必須查人、看空間並保留完整紀錄。"
  },
  {
    keyword: "泰國整形 跨境醫美 修復",
    slug: "thailand-crossborder-rhinoplasty-risk",
    image: "D3_crossborder-nose-surgery.jpg",
    description: "海外整鼻看似便宜，真正昂貴的是缺乏病歷、耗材不明與回台後無人願意承接的修復風險。"
  },
  {
    keyword: "Klotho 長壽醫學 抗老研究",
    slug: "klotho-longevity-treatment-reality",
    image: "D4_klotho-longevity-lab.jpg",
    description: "Klotho 讓長壽醫學看見主動修復的可能，但人體證據與長期安全性仍待確認，現在更重要的是管理健康壽命。"
  },
  {
    keyword: "Retatrutide 減重藥 慈悲使用",
    slug: "retatrutide-compassionate-use",
    image: "D5_retatrutide-weight-loss.jpg",
    description: "Retatrutide 的高減重潛力引發期待，也提醒我們：試驗性療法、資源公平與未知風險不能被搶先體驗掩蓋。"
  },
  {
    keyword: "無照密醫 玻尿酸 注射安全",
    slug: "unlicensed-filler-injection-death",
    image: "D6_unlicensed-injection-warning.jpg",
    description: "侵入性醫美不是熟人推薦就能放心；查診所、查醫師執照、看耗材批號，是進行注射前最低限度的自保。"
  },
  {
    keyword: "居家美容儀 微電流 LED 射頻",
    slug: "home-beauty-device-truth",
    image: "D7_home-beauty-device.jpg",
    description: "居家美容儀可以維護，不能取代診所治療；購買前要看能量參數、研究證據與自己的真實使用目標。"
  }
];

function extractArticles(raw) {
  const headers = [...raw.matchAll(/^##\s+\d+\/\d+[^\n]*$/gm)];
  return headers.map((header, index) => {
    const start = header.index + header[0].length;
    const end = headers[index + 1]?.index ?? raw.length;
    const chunk = raw.slice(start, end).trim();
    const title = chunk.match(/^#\s+(.+)$/m)?.[1]?.trim();
    const subtitle = chunk.match(/^副標題：(.+)$/m)?.[1]?.trim();
    const firstRule = chunk.indexOf("\n---", chunk.indexOf(subtitle ?? ""));
    if (!title || !subtitle || firstRule < 0) {
      throw new Error(`無法解析文章：${header[0]}`);
    }
    let body = chunk.slice(firstRule + 4).trim();
    body = body.split(/\n---\s*\n\s*想了解更多醫美真話/)[0].trim();
    body = body.replace(/\n{3,}/g, "\n\n");
    return { title, subtitle, body };
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
