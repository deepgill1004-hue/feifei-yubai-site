#!/usr/bin/env node
import path from "node:path";
import {
  buildMetadata,
  defaultOutDir,
  generateImage,
  loadDotEnv,
  loadPresets,
  rootDir,
  savePromptMetadata
} from "./imgen-core.mjs";

loadDotEnv();

const args = process.argv.slice(2);

function usage() {
  return `用法:
  node scripts/imgen-topic-tool.mjs "主題文字"
  node scripts/imgen-topic-tool.mjs "鳳凰電波術後保養" --generate
  node scripts/imgen-topic-tool.mjs --list

選項:
  --topic <slug>       指定模板，不自動判斷
  --generate           有 OPENAI_API_KEY 時直接呼叫 OpenAI 影像 API
  --model <model>      預設讀 IMAGE_MODEL，否則使用 gpt-image-2
  --size <WxH>         覆蓋模板尺寸，例如 1024x1536
  --quality <value>    low, medium, high, auto
  --format <value>     png, jpeg, webp，預設 png
  --out <dir>          輸出資料夾，預設 output/imgen
  --json               只輸出 JSON metadata
  --list               列出可用模板`;
}

function parseArgs(rawArgs) {
  const options = {
    generate: false,
    json: false,
    list: false,
    outDir: defaultOutDir,
    model: process.env.IMAGE_MODEL || "gpt-image-2",
    outputFormat: "png"
  };
  const textParts = [];

  for (let i = 0; i < rawArgs.length; i += 1) {
    const arg = rawArgs[i];
    if (arg === "--generate") options.generate = true;
    else if (arg === "--json") options.json = true;
    else if (arg === "--list") options.list = true;
    else if (arg === "--topic") options.topic = rawArgs[++i];
    else if (arg === "--model") options.model = rawArgs[++i];
    else if (arg === "--size") options.size = rawArgs[++i];
    else if (arg === "--quality") options.quality = rawArgs[++i];
    else if (arg === "--format") options.outputFormat = rawArgs[++i];
    else if (arg === "--out") options.outDir = path.resolve(rawArgs[++i]);
    else if (arg === "--help" || arg === "-h") options.help = true;
    else textParts.push(arg);
  }

  return {
    ...options,
    input: textParts.join(" ").trim()
  };
}

async function main() {
  const options = parseArgs(args);
  if (options.help) {
    console.log(usage());
    return;
  }

  if (options.list) {
    for (const preset of loadPresets()) {
      console.log(`${preset.slug}\t${preset.name}\t${preset.size}\t${preset.quality}`);
    }
    return;
  }

  if (!options.input) {
    console.error(usage());
    process.exitCode = 1;
    return;
  }

  const metadata = buildMetadata(options);
  savePromptMetadata(metadata, false);

  let generated = false;
  if (options.generate) {
    await generateImage(metadata);
    generated = true;
  }

  const saved = savePromptMetadata(metadata, generated);

  if (options.json) {
    console.log(JSON.stringify(saved, null, 2));
    return;
  }

  console.log(`主題: ${saved.selectedName} (${saved.selectedTopic})`);
  console.log(`模型: ${saved.model}`);
  console.log(`尺寸/品質: ${saved.size} / ${saved.quality}`);
  console.log(`提示詞: ${path.relative(rootDir, saved.promptFile)}`);
  console.log(`metadata: ${path.relative(rootDir, saved.metadataFile)}`);
  if (generated) console.log(`圖片: ${path.relative(rootDir, saved.imageFile)}`);
  else console.log("圖片: 尚未生成；加上 --generate 並設定 OPENAI_API_KEY 後會輸出圖片。");
}

main().catch((error) => {
  console.error(error.message);
  if (/model/i.test(error.message) && /gpt-image-2/i.test(error.message)) {
    console.error("提示: 若你的帳號尚未支援 gpt-image-2，可改用 --model gpt-image-1.5 或設定 IMAGE_MODEL=gpt-image-1.5。");
  }
  process.exitCode = 1;
});
