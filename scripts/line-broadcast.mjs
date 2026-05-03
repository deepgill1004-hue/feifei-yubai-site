#!/usr/bin/env node
import fs from "node:fs";

function loadDotEnv(path = ".env") {
  if (!fs.existsSync(path)) return;
  const lines = fs.readFileSync(path, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const match = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (!match) continue;
    let value = match[2].trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!process.env[match[1]]) process.env[match[1]] = value;
  }
}

function parseArgs(argv) {
  const options = { send: false };
  const parts = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--send") options.send = true;
    else if (arg === "--file") options.file = argv[++i];
    else if (arg === "--help" || arg === "-h") options.help = true;
    else parts.push(arg);
  }
  options.text = parts.join(" ").trim();
  return options;
}

function usage() {
  return `用法:
  node scripts/line-broadcast.mjs --file output/sophie-publishing/xxx/line.txt
  node scripts/line-broadcast.mjs --file output/sophie-publishing/xxx/line.txt --send
  node scripts/line-broadcast.mjs "推播文字" --send

環境變數:
  優先使用 LINE_CHANNEL_ACCESS_TOKEN
  或使用 LINE_CHANNEL_ID + LINE_CHANNEL_SECRET 取得短效 token

預設為 dry-run，不會真的推播。要對外發送必須加 --send。`;
}

async function getAccessToken() {
  if (process.env.LINE_CHANNEL_ACCESS_TOKEN) return process.env.LINE_CHANNEL_ACCESS_TOKEN;

  const channelId = process.env.LINE_CHANNEL_ID;
  const channelSecret = process.env.LINE_CHANNEL_SECRET;
  if (!channelId || !channelSecret) {
    throw new Error("缺少 LINE_CHANNEL_ACCESS_TOKEN，或 LINE_CHANNEL_ID + LINE_CHANNEL_SECRET。");
  }

  const body = new URLSearchParams({
    grant_type: "client_credentials",
    client_id: channelId,
    client_secret: channelSecret
  });

  const response = await fetch("https://api.line.me/v2/oauth/accessToken", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(`LINE token 取得失敗 (${response.status}): ${JSON.stringify(payload)}`);
  }
  return payload.access_token;
}

async function broadcast(text) {
  const token = await getAccessToken();
  const response = await fetch("https://api.line.me/v2/bot/message/broadcast", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      messages: [{ type: "text", text }]
    })
  });

  const detail = await response.text();
  if (!response.ok) {
    throw new Error(`LINE broadcast 失敗 (${response.status}): ${detail}`);
  }
  return response.status;
}

async function main() {
  loadDotEnv();
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
    return;
  }

  const text = options.file ? fs.readFileSync(options.file, "utf8").trim() : options.text;
  if (!text) {
    console.error(usage());
    process.exitCode = 1;
    return;
  }

  if (!options.send) {
    console.log(JSON.stringify({ mode: "dry-run", length: text.length, preview: text }, null, 2));
    return;
  }

  const status = await broadcast(text);
  console.log(`LINE broadcast OK (${status})`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
