# data/

## videos.json：YouTube 短影片清單

網站上所有 YouTube 影片的唯一資料來源。本機上架產線每上一支新影片，就往陣列最後面追加一筆，接著跑：

```
python scripts/yubai_site.py apply-theme
```

這一步會一起更新：有對應文章的文章頁（嵌入影片＋VideoObject 結構化資料）、影片總覽頁 `videos.html`、`sitemap.xml` 裡 `videos.html` 的 lastmod、`llms.txt`。不要手改任何 HTML。

### 每筆欄位

| 欄位 | 必填 | 型別 | 說明 |
|---|---|---|---|
| `id` | 是 | 字串 | YouTube 影片 ID，11 碼（網址 `youtube.com/shorts/<id>` 的那段）。格式不對的整筆會被略過 |
| `title` | 是 | 字串 | 影片標題，照 YouTube 上的標題原樣填 |
| `publishedDate` | 建議 | 字串或 `null` | 上架日期，ISO 8601。可寫 `2026-10-20`，知道時間更好：`2026-10-20T19:00:00+08:00`。這是 VideoObject 的 `uploadDate`，Google 影片搜尋必填；沒填時網站照常產頁，但 apply-theme 會提醒，結構化資料也會缺這一欄 |
| `topic` | 否 | 字串 | 主題短詞，例如 `微針電波`、`瘦瘦針`、`水光`。沒有對應文章時，總覽頁會用它找相關療程主題頁（電波、音波、玻尿酸、肉毒、水光） |
| `article` | 否 | 字串或 `null` | 對應文章，相對站台根目錄，例如 `letters/045-morpheus8-vs-monopolar-rf-20260705.html`。檔案不存在時當作 `null`。只有主題真的相符才填 |
| `description` | 建議 | 字串 | 一兩句白話說明，給結構化資料與總覽頁用。沒填就用標題 |

### 規則

- 只寫影片本身講的事，不加療程價格；對外連結只放官方 LINE、蘇菲餘白網站、YouTube 頻道與既有 FB 粉專。
- 同一篇文章可以對應多支影片，文章頁會全部嵌入。
- 縮圖固定用 `https://i.ytimg.com/vi/<id>/hqdefault.jpg`，不用另外填。

## analytics.json：訪客統計（Cloudflare Web Analytics）與 LINE 按鈕點擊計數

`cf_beacon_token`：Cloudflare 網站分析給的 token（一串英數字，本來就會公開在每一頁的原始碼裡，不是密碼）。

- 取得方式：Cloudflare 後台 Web Analytics → Add a site → 輸入 `sophieyubai.com` → 選手動放 JS 代碼（網站在 GitHub Pages，不用改 DNS）→ 代碼裡 `data-cf-beacon='{"token": "…"}'` 的那串。
- 填好後跑 `python3 -B scripts/yubai_site.py apply-theme` 兩次（第二次要顯示 `changed 0 files`），再跑 `check`，沒有 ERROR 才上線。全站每一頁會在 yubai.js 後面多一段 `<!--yubai:analytics-->` 代碼。
- 留空就不裝；清空後重跑 apply-theme 會把代碼全部拿掉。
- check 會擋：token 格式不對（貼成整段代碼）、某頁缺代碼或重複、token 已清空但頁面還留著代碼。
- 不用 cookie，不需要另外放同意橫幅。

### line_click_endpoint：LINE 按鈕點擊計數

Cloudflare 網站分析不支援自訂事件（官方 FAQ），收不到按鈕點擊，所以另外計數。填了接收端網址，apply-theme 會在同一段 `<!--yubai:analytics-->` 裡多載入 `assets/yubai-click.js`；讀者點任何 LINE 連結時送一次，連結本身不改。

- 網站送出的內容（POST，`text/plain`）：`{"site":"sophieyubai.com","ev":"line","page":"/letters/….html","pos":"end"}`。只送頁面路徑和位置，不用 cookie、不送個人資料；只在 sophieyubai.com 上送，本機預覽不送。
- 位置 `pos`：`end` 文末（加入 LINE 按鈕與「延伸整理」區，週報「文末加入 LINE 點擊」算這個）、`answer` 開頭結論框、`video` 影片卡、`sidebar` 側欄、`fab` 右下角浮動鈕、`header` 頁首、`footer` 頁尾、`page` 其他頁（首頁、諮詢頁…）。
- 接收端：`scripts/line-click-worker/`（Cloudflare Worker＋D1，不存 IP、不存 cookie）。在蘇菲電腦上部署（要她已登入的 Cloudflare；`npx wrangler whoami` 沒登入就停下來請她處理，不輸入密碼）：
  1. 把 `worker.js`、`schema.sql`、`wrangler.toml.example` 複製到 repo 外面（例：`../蘇菲餘白週報/line-click-worker/`），`wrangler.toml.example` 改名 `wrangler.toml`。
  2. `npx wrangler d1 create yubai-line-click`，把給的 database_id 填進 wrangler.toml。
  3. `npx wrangler d1 execute yubai-line-click --remote --file schema.sql`
  4. `npx wrangler secret put STATS_TOKEN`：貼一串自己產的亂數（週報排程讀數字用），同一串存在 repo 外面，不進 repo。
  5. `npx wrangler deploy`，拿到 `https://yubai-line-click.<子網域>.workers.dev`。Worker 名稱不要用真名；這個網址會出現在每一頁的原始碼裡。
  6. 網址填進 `line_click_endpoint`，跑 apply-theme 兩次（第二次要 `changed 0 files`）、check 沒有 ERROR，照上架流程推上 main。
  7. 上線後到任一篇文章點一次文末的加入 LINE，再用 `curl -H "Authorization: Bearer <STATS_TOKEN>" "<網址>/stats?days=2"` 看得到那一筆，就是通了（這一筆是測試，週報要扣掉）。
- 每週二週報排程：讀 `/stats?days=14`，把資料週（週一～週日）`pos=end` 加總填 `local.json` 的 `line.clicks`、全部位置加總填 `line.total`、各位置填 `line.by_pos`（格式見 `scripts/weekly_report.py` 開頭）。
- check 會擋：網址格式不對、填了網址但 `assets/yubai-click.js` 不見、某頁缺代碼或重複；還沒填時出一則 WARN 提醒。

## imgen-prompt-presets.json

圖片產線的提示詞預設值（imgen-core.mjs 使用）。

## ai_questions.json：AI 引用面板固定 20 題

每月第一個週二 08:06，ChatGPT（臨時聊天）、Perplexity、Google AI 摘要、Copilot 各問一次，記「有沒有引用 sophieyubai.com、引用哪一頁、前三個來源是誰」。`expect` 是對應文章（`also` 是同主題的其他篇）。題目固定才看得出每月進步，改題目要寫進週報。

週報出檔程式 `scripts/weekly_report.py` 讀這個檔；每週的原始數據（Search Console、Bing、Cloudflare）放在 repo 外面的「蘇菲餘白週報」資料夾，不進 repo、不公開。用法寫在程式開頭。
