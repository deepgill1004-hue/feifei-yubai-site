# Sophie 整合發文流水線

日期：2026-05-03

## 結論

現在的主流程改成：

```text
關鍵字 / 主題
→ Codex 套用 Sophie Agent 爆款邏輯與 PSE Gate
→ 生成網站文章
→ 生成 Hashtag
→ 生成 LINE / Threads / IG / 方格子分發包
→ 選用蘇菲形象圖或生成新圖
→ 更新 letters/index.html、feed.xml、sitemap.xml
→ commit / push
→ LINE OA 視需要 broadcast
```

主站是內容母體；LINE 官方帳號是主要導流與互動；Beehiiv 先保留備用，不放在主發布路徑。

## 觸發方式

之後你可以直接說：

```text
Go：肉毒抗體
```

或：

```text
寫一篇：線雕修復
```

Codex 要做的事：

1. 讀 Sophie Agent 必要規則，不一次掃全部。
2. 先查是否已有站內文章，避免重複。
3. 醫療、法規、FDA、藥品、醫材、價格、平台規則等會變動內容，先查證。
4. 生成文章時必須附 Hashtag。
5. 寫入網站後，更新文章列表、RSS、sitemap。
6. 產出 `output/sophie-publishing/` 分發包。

## 可執行指令

只驗證，不寫檔：

```powershell
node scripts/sophie-publish.mjs --keyword "肉毒抗體" --dry-run
```

產出網站文章與分發包：

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
node scripts/line-broadcast.mjs --file output/sophie-publishing/某篇/line.txt
```

這是 dry-run，不會發送。

真的要推播才加：

```powershell
node scripts/line-broadcast.mjs --file output/sophie-publishing/某篇/line.txt --send
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

目前網站流水線會產出：

```text
output/sophie-publishing/某篇/fanggezi.md
```

你可以手貼；或先用 Sophie Agent 的半自動工具填入：

```powershell
python C:\Users\user\sophie-agent\tools\vocus-post.py --login
python C:\Users\user\sophie-agent\tools\vocus-post.py --title "文章標題" --file "output\sophie-publishing\某篇\fanggezi.md"
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
- Hashtag
- LINE 文案
- Threads 文案
- IG 文案
- 方格子手貼版
- 圖片 prompt 或生成圖

## 爆款邏輯

每篇文章都要有這個骨架：

```text
人 / 場景 / 數字
→ 反常識鉤子
→ 蘇菲拆解
→ 消費者可執行問題
→ 風險或紅線
→ Hashtag
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
