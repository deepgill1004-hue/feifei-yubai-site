# Codex 接手 Sophie Agent 產文與發文流程

這份文件把 `C:\Users\user\sophie-agent` 裡 Claude 使用的 Sophie Agent 產文規格，整理成 Codex 可直接接手的共用流程。

## 可共用的內容來源

- 每日內容包：`C:\Users\user\sophie-agent\content\sophie-daily-content-YYYY-MM-DD.md`
- 主控規則：`C:\Users\user\sophie-agent\CLAUDE.md`
- 長文規格：`C:\Users\user\sophie-agent\sophie-content-research-writer.md`
- 社群文案規格：`C:\Users\user\sophie-agent\sophie-ip-copywriter.md`
- 平台規格：`C:\Users\user\sophie-agent\sophie-platform-ops.md`
- LINE 私域規格：`C:\Users\user\sophie-agent\sophie-private-domain.md`

Codex 之後處理蘇菲內容時，優先讀每日內容包；需要判斷文章結構時再讀長文規格，不要一次掃整個 Sophie Agent 資料夾。

## 網站文章新增流程

1. 從每日內容包中挑最適合放到蘇菲餘白網站的段落。
2. 優先選「方格子長文 / SEO 長文 / 完整故事主稿」。
3. 如果原文太長，裁成網站文章節奏：標題、前言、3 到 7 個小節、文末行動建議。
4. 若適合電子報，另做 Beehiiv HTML 與 `beehiiv/posts/*.json`；若不適合，不硬轉。
5. 更新 `letters/index.html`，讓最新文章出現在文章列表。
6. 視需要更新首頁最新文章區與 `feed.xml`。
7. 文末固定附共同連結區塊。

## 文末共同連結區塊

每篇完整文章、網站文章、電子報版本、方格子長文，都用這三個名稱，不使用內部工程說法。

```
官方 LINE：https://line.me/R/ti/p/@371arhqu
蘇菲餘白網站：https://deepgill1004-hue.github.io/feifei-yubai-site/
電子報：https://sophie-yubai.beehiiv.com/
```

可加上的自然承接句：

```
我會在 LINE 裡用更白話的方式拆，也會把完整文章與延伸整理留在網站和電子報。
```

## 自動發文分工

- GitHub Pages：Codex 可直接更新網站、commit、push。
- Beehiiv：Codex 先建立 draft 定義，透過 `scripts/create-beehiiv-drafts.mjs --dry-run` 驗證；正式同步仍以草稿為主。
- LINE OA：涉及對外推播，Codex 需要在發送前明確告知並取得允許。
- 方格子 / 其他社群：先產出可貼上的定稿與連結區塊；正式登入發布需另外建立安全流程。

## 發布前檢查

- 文章是否能單獨成立，不只是社群貼文片段。
- 文末是否包含官方 LINE、蘇菲餘白網站、電子報三個連結。
- `letters/index.html` 是否出現新文章。
- `feed.xml` 是否更新。
- Beehiiv draft dry-run 是否能正常讀取。
- `git status` 是否只提交本次文章相關檔案，不混入貼圖包、工具草稿或未確認素材。
