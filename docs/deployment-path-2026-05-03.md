# 蘇菲餘白部署路徑決策

日期：2026-05-03

## 結論

目前最適合、最省力、最完整、呈現最好的路徑是：

```
純靜態網站 HTML/CSS
→ GitHub 管版本
→ GitHub Pages 立即上線
→ Cloudflare Pages 作為下一階段正式部署
→ LINE 官方帳號負責私訊、推播與諮詢承接
→ Beehiiv 保留為備用 email 通道，不放在主發布流程
```

暫時不採用 WordPress、Ghost、Framer、Astro。

## 為什麼

### 1. 現在不需要 Astro

Astro 很適合未來大量文章、元件化、i18n、多作者或自動生成頁面。但現在網站只有首頁、關於、療程主題、FAQ、諮詢與少量文章，直接維護 HTML 比導入框架更省力。

等文章超過 30 篇、療程頁超過 20 頁，或真的要做多語系，再升級 Astro。

### 2. 現在不需要 WordPress / Ghost

WordPress 與 Ghost 的優點是後台管理與內容發布，但代價是主機、外掛、更新、安全與維護。蘇菲餘白目前最重要的是建立定位、SEO 結構、內容路徑與轉換，不需要先背 CMS 成本。

### 3. Vercel 可用，但不是第一選擇

Vercel 對 Next.js、Serverless、Preview Deployment 很強。如果未來要做表單 API、會員功能、AI 工具頁，Vercel 很適合。

但目前蘇菲餘白是純靜態站，Cloudflare Pages 或 GitHub Pages 已經足夠。

### 4. Cloudflare Pages 是正式站最佳下一步

Cloudflare Pages 支援 GitHub 自動部署、全球 CDN、靜態 HTML、預覽部署，也適合之後接自訂網域與安全標頭。對純靜態網站來說，設定少、速度快、成本低。

## 已完成的執行

- 首頁已從一頁式整合成完整品牌首頁。
- 新增 `about.html`、`treatments.html`、`faq.html`、`consult.html`。
- 新增五個療程主題頁：鳳凰電波、音波、玻尿酸、肉毒、水光。
- 新增 `sitemap.xml` 與 `robots.txt`。
- 新增 Cloudflare Pages 可讀取的 `_headers`。
- 新增 Vercel 相容的 `vercel.json`。
- 文件規則已收斂為「蘇菲餘白網站 + Beehiiv + LINE」。

## Cloudflare Pages 設定

如果改用 Cloudflare Pages：

- Project type：Pages
- Source：GitHub repository
- Production branch：`main`
- Build command：`exit 0`
- Build output directory：`/`
- Root file：`index.html`

部署後會得到 `*.pages.dev` 網址，再接正式網域。

## GitHub Pages 設定

目前 GitHub Pages 仍可直接使用：

- Source：Deploy from branch
- Branch：`main`
- Folder：`/root`
- `.nojekyll` 已存在，會直接部署靜態檔案。

## Vercel 設定

如果要用 Vercel：

- Framework preset：Other
- Build command：留空或 `echo "static site"`
- Output directory：`.`
- `vercel.json` 已加入乾淨 URL 與基本安全標頭。

## 下一階段再做

- 自訂網域。
- Google Search Console 提交 `sitemap.xml`。
- Google Analytics 或 Plausible。
- LINE 官方帳號關鍵字回覆與文章推播。
- Beehiiv 若 email 名單開始成長，再嵌入或升級。
- 若文章量變大，再升級 Astro 並把 `topics/` 與 `letters/` 轉成內容資料。
