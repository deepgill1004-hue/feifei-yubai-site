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

## analytics.json：訪客統計（Cloudflare Web Analytics）

只有一個欄位 `cf_beacon_token`：Cloudflare 網站分析給的 token（一串英數字，本來就會公開在每一頁的原始碼裡，不是密碼）。

- 取得方式：Cloudflare 後台 Web Analytics → Add a site → 輸入 `sophieyubai.com` → 選手動放 JS 代碼（網站在 GitHub Pages，不用改 DNS）→ 代碼裡 `data-cf-beacon='{"token": "…"}'` 的那串。
- 填好後跑 `python3 -B scripts/yubai_site.py apply-theme` 兩次（第二次要顯示 `changed 0 files`），再跑 `check`，沒有 ERROR 才上線。全站每一頁會在 yubai.js 後面多一段 `<!--yubai:analytics-->` 代碼。
- 留空就不裝；清空後重跑 apply-theme 會把代碼全部拿掉。
- check 會擋：token 格式不對（貼成整段代碼）、某頁缺代碼或重複、token 已清空但頁面還留著代碼。
- 不用 cookie，不需要另外放同意橫幅。

## imgen-prompt-presets.json

圖片產線的提示詞預設值（imgen-core.mjs 使用）。

## ai_questions.json：AI 引用面板固定 20 題

每月第一個週二 08:06，ChatGPT（臨時聊天）、Perplexity、Google AI 摘要、Copilot 各問一次，記「有沒有引用 sophieyubai.com、引用哪一頁、前三個來源是誰」。`expect` 是對應文章（`also` 是同主題的其他篇）。題目固定才看得出每月進步，改題目要寫進週報。

週報出檔程式 `scripts/weekly_report.py` 讀這個檔；每週的原始數據（Search Console、Bing、Cloudflare）放在 repo 外面的「蘇菲餘白週報」資料夾，不進 repo、不公開。用法寫在程式開頭。
