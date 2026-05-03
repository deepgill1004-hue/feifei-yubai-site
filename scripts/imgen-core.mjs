import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const rootDir = path.resolve(__dirname, "..");
export const presetsPath = path.join(rootDir, "data", "imgen-prompt-presets.json");
export const defaultOutDir = path.join(rootDir, "output", "imgen");

export function loadDotEnv(envPath = path.join(rootDir, ".env")) {
  if (!fs.existsSync(envPath)) return false;

  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const match = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (!match) continue;

    const key = match[1];
    let value = match[2].trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!process.env[key]) process.env[key] = value;
  }

  return true;
}

export function loadPresets() {
  return JSON.parse(fs.readFileSync(presetsPath, "utf8"));
}

export function normalize(value) {
  return String(value || "").toLowerCase();
}

export function scorePreset(preset, input) {
  const normalized = normalize(input);
  return preset.keywords.reduce((score, keyword) => {
    const key = normalize(keyword);
    if (!key) return score;
    if (normalized.includes(key)) return score + Math.max(2, key.length > 4 ? 4 : 3);
    return score;
  }, 0);
}

export function pickPreset(input, topic, presets = loadPresets()) {
  if (topic) {
    const exact = presets.find((preset) => preset.slug === topic);
    if (!exact) {
      throw new Error(`找不到 topic "${topic}"。可用: ${presets.map((preset) => preset.slug).join(", ")}`);
    }
    return { preset: exact, score: 999, reason: "manual-topic" };
  }

  const ranked = presets
    .map((preset) => ({ preset, score: scorePreset(preset, input) }))
    .sort((a, b) => b.score - a.score);

  if (ranked[0].score <= 0) {
    const fallback = presets.find((preset) => preset.slug === "visual-poster") || presets[0];
    return { preset: fallback, score: 0, reason: "fallback" };
  }

  return { ...ranked[0], reason: "keyword-match" };
}

export function renderPrompt(template, input) {
  const subject = input.replace(/\s+/g, " ").trim();
  return template
    .replaceAll("{{subject}}", subject)
    .replaceAll("{{input}}", input.trim())
    .trim();
}

export function slugify(input) {
  const ascii = normalize(input)
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
  return ascii || `image-${Date.now()}`;
}

export function buildMetadata(options) {
  const presets = options.presets || loadPresets();
  const outDir = options.outDir || defaultOutDir;
  const picked = pickPreset(options.input, options.topic, presets);
  const size = options.size || picked.preset.size;
  const quality = options.quality || picked.preset.quality;
  const outputFormat = options.outputFormat || "png";
  const model = options.model || process.env.IMAGE_MODEL || "gpt-image-2";
  const prompt = renderPrompt(picked.preset.prompt, options.input);
  const baseName = `${new Date().toISOString().replace(/[:.]/g, "-")}-${picked.preset.slug}-${slugify(options.input)}`;

  return {
    input: options.input,
    selectedTopic: picked.preset.slug,
    selectedName: picked.preset.name,
    selectionReason: picked.reason,
    score: picked.score,
    model,
    size,
    quality,
    outputFormat,
    prompt,
    promptFile: path.join(outDir, `${baseName}.txt`),
    metadataFile: path.join(outDir, `${baseName}.json`),
    imageFile: path.join(outDir, `${baseName}.${outputFormat}`)
  };
}

export async function generateImage(metadata) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("缺少 OPENAI_API_KEY。請先在本機 .env 或環境變數設定金鑰，或先不加 --generate 只產生提示詞。");
  }

  const response = await fetch("https://api.openai.com/v1/images/generations", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: metadata.model,
      prompt: metadata.prompt,
      size: metadata.size,
      quality: metadata.quality,
      output_format: metadata.outputFormat,
      n: 1
    })
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload?.error?.message || response.statusText;
    throw new Error(`OpenAI 影像 API 失敗 (${response.status}): ${message}`);
  }

  const b64 = payload?.data?.[0]?.b64_json;
  if (!b64) {
    throw new Error("OpenAI 影像 API 回應中沒有 b64_json，無法寫入圖片。");
  }

  fs.writeFileSync(metadata.imageFile, Buffer.from(b64, "base64"));
}

export function savePromptMetadata(metadata, generated = false) {
  fs.mkdirSync(path.dirname(metadata.promptFile), { recursive: true });
  fs.writeFileSync(metadata.promptFile, `${metadata.prompt}\n`, "utf8");

  const saved = { ...metadata, generated };
  fs.writeFileSync(metadata.metadataFile, `${JSON.stringify(saved, null, 2)}\n`, "utf8");
  return saved;
}
