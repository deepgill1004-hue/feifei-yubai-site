# Sophie 整合發文流水線

日期：2026-05-03

## 結論

現在的主流程改成：

```text
關鍵字 / 主題
→ Codex 套用 Sophie Agent 爆款邏輯與 PSE Gate
→ 生成網站文章
→ 生成主題標籤
→ 生成單一每日 Markdown 文檔：網站主文 / LINE / Threads / IG / 方格子 / 圖片提示詞全部放一起
→ 選用蘇菲形象圖或生成新圖
→ 更新 letters/index.html、feed.xml、sitemap.xml
→ commit / push
→ LINE OA 視需要 broadcast
```

主站是內容母體；LINE 官方帳號是主要導流與互動。**2026-05-03 起 Beehiiv 已停用**，所有公開內容只走「自家網站 letters/ + 官方 LINE + Hashtag」三件事，不再放任何電子報或外部訂閱平台連結。

## 觸發方式

之後你可以直接說：

```text
發文：肉毒抗體
```

這會產出網站文章、主題標籤、單一每日 Markdown 文檔，並更新文章列表、RSS、sitemap。LINE 只產出文案，不會自動發送。

如果要連 LINE 官方帳號一起推播，才使用：

```text
發文加 LINE：線雕修復
```

這代表文章上站後，會再執行 LINE OA broadcast。這個觸發字要非常明確，避免測試時誤發。

Codex 要做的事：

1. 讀 Sophie Agent 必要規則，不一次掃全部。
2. 先查是否已有站內文章，避免重複。
3. 醫療、法規、FDA、藥品、醫材、價格、平台規則等會變動內容，先查證。
4. 生成文章時必須附主題標籤，但網站頁面不顯示突兀的英文標題。
5. 寫入網站後，更新文章列表、RSS、sitemap。
6. 產出網站專案外的每日文檔，不再把分發稿散落在 `output/sophie-publishing/`。

## 每日文檔歸檔

所有平台內容統一輸出到網站資料夾外：

```text
C:\Users\user\Desktop\蘇菲每日文檔\YYYY-MM-DD\編號-slug-標題.md
```

單一 Markdown 內會包含：

- 發布資訊與網站文章連結
- 網站文章主文
- 方格子手貼版
- LINE OA 文案
- Threads 文案
- Instagram 文案
- 圖片提示詞
- 機器紀錄

如果需要改位置，可用：

```powershell
node scripts/sophie-publish.mjs --keyword "肉毒抗體" --daily-docs-dir "D:\蘇菲每日文檔"
```

## 散落素材整理

如果 Sophie Agent、桌面、Claude 產出的舊發文內容又散落，可以重跑整理腳本：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\consolidate-sophie-daily-docs.ps1
```

整理結果會放在：

```text
C:\Users\user\Desktop\蘇菲每日文檔
```

整理規則：

- 原始檔只複製，不刪除。
- 依檔名或路徑中的日期歸入 `YYYY-MM-DD`。
- 找不到日期時，使用檔案修改日期。
- 每日素材放在 `YYYY-MM-DD\素材\`。
- 每天產生 `_當日索引.md`。
- 總索引放在 `_index\總索引.md`。
- 明細 CSV 放在 `_index\inventory.csv`。

## 可執行指令

只驗證，不寫檔：

```powershell
node scripts/sophie-publish.mjs --keyword "肉毒抗體" --dry-run
```

產出網站文章與每日文檔：

```powershell
node scripts/sophie-publish.mjs --keyword "肉毒抗體" --title "肉毒打久突然沒效？先看抗體、頻率與靜態紋"
```

搭配 Sophie Agent 既有 MD：

```powershell
node scripts/sophie-publish.mjs --keyword "線雕" --source "C:\Users\user\sophie-agent\content\sophie-daily-content-2026-04-30.md"
```

如果本機 `.env` 有 `OPENAI_API_KEY`，可嘗試生成新圖：

```powershell
node scripts/sophie-publish.mjs --keyword "玻尿酸材料" --generate-image
```

如果沒有圖像 API 或圖片生成失敗，流程會改用已整理好的蘇菲形象圖，不中斷網站上架。

## LINE OA

LINE 官方帳號可以自動 PO 文，使用 Messaging API broadcast。

目前新增：

```powershell
node scripts/line-broadcast.mjs "推播文字"
```

這是 dry-run，不會發送。

真的要推播才加：

```powershell
node scripts/sophie-publish.mjs --keyword "線雕修復" --line-send
```

環境變數優先讀：

```text
LINE_CHANNEL_ACCESS_TOKEN
```

或：

```text
LINE_CHANNEL_ID
LINE_CHANNEL_SECRET
```

LINE 官方文件確認 Messaging API 支援 broadcast 給所有好友，也支援 push / multicast / narrowcast。  
官方文件：https://developers.line.biz/en/docs/messaging-api/sending-messages/

注意：LINE 官方帳號有月訊息額度。免費方案訊息數有限，推播前要注意當月剩餘額度。  
LINE 官方說明：https://help2.line.me/official_account_tw/web/pc?contentId=20011830&lang=en

## 方格子

方格子目前不放在「全自動正式發布」。

原因：

- 沒有穩定公開 API 可以安全發正式文章。
- Sophie Agent 裡已有 `tools/vocus-post.py`，可以用 Playwright 幫你開編輯器、填標題與內文。
- 最後發布按鈕仍建議人工確認，避免格式、分類、封面、付費設定出錯。

目前網站流水線會在每日 Markdown 內產出「方格子」段落：

```text
C:\Users\user\Desktop\蘇菲每日文檔\YYYY-MM-DD\編號-slug-標題.md
```

你可以從每日 Markdown 裡複製「方格子」段落手貼。若要用 Sophie Agent 的半自動工具，請先把「方格子」段落另存成暫存檔再填入，避免把 LINE / IG / Threads 段落一起貼進方格子：

```powershell
python C:\Users\user\sophie-agent\tools\vocus-post.py --login
python C:\Users\user\sophie-agent\tools\vocus-post.py --title "文章標題" --file "C:\Users\user\Desktop\蘇菲每日文檔\YYYY-MM-DD\fanggezi-temp.md"
```

## 每篇文章的固定檢查

每篇文章必須有：

- 網站文章 HTML
- `letters/index.html` 入口
- `feed.xml` RSS item
- `sitemap.xml` URL
- canonical URL
- meta description
- OG image
- 主題標籤
- LINE 文案
- Threads 文案
- IG 文案
- 方格子手貼版
- 圖片 prompt 或生成圖
- 每日 Markdown 總檔

## 爆款邏輯

每篇文章都要有這個骨架：

```text
人 / 場景 / 數字
→ 反常識鉤子
→ 蘇菲拆解
→ 消費者可執行問題
→ 風險或紅線
→ 主題標籤
→ LINE CTA
```

不寫空泛科普。  
不寫診所廣告。  
不寫沒有行動建議的漂亮文章。  
目標是：有人讀、有人回、能導回 LINE。

## Beehiiv

Beehiiv 現階段保留為備用 email 通道。

不再把 Beehiiv 當主流程必要步驟。  
真正的主流程是網站與 LINE。
