# 蘇菲餘白網站

這個資料夾是一個可直接部署到 GitHub Pages 或 Vercel 的靜態網站。主架構收斂為兩個資產：蘇菲餘白網站負責品牌、SEO 與內容沉澱；Beehiiv 負責電子報訂閱。

## 目前包含

- `index.html`：品牌首頁
- `about.html`：關於蘇菲餘白
- `treatments.html`：療程主題入口
- `topics/`：鳳凰電波、音波、玻尿酸、肉毒、水光主題頁
- `letters/`：《蘇菲餘白》文章 archive
- `faq.html`：常見問題
- `consult.html`：諮詢整理入口
- `assets/styles-v2.css`：網站樣式
- `feed.xml`：RSS feed
- `sitemap.xml`、`robots.txt`：搜尋引擎收錄用檔案
- `docs/`：內容地圖、發布文案與營運文件

## 預覽方式

直接用瀏覽器打開 `index.html`。

## 上線路線

推薦路線：

1. 目前維持 GitHub Pages 立即上線。
2. 正式網域準備好後，優先接 Cloudflare Pages。
3. Vercel 保留為未來需要 API、會員功能或 AI 工具頁時的選項。

GitHub Pages 路線：

1. 在 GitHub 建立新 repo。
2. 上傳這個資料夾內容。
3. 到 repo 的 Settings > Pages，選擇從 `main` branch 的根目錄部署。
4. 部署後把 `sitemap.xml` 提交到 Google Search Console。

Beehiiv 路線：

1. 網站文章與主題頁放在這個 repo。
2. Beehiiv 發電子報，文末導回網站文章與 LINE。
3. 社群平台只做分發，不再當主網站架構。

## 下一步

- 主網站：`https://deepgill1004-hue.github.io/feifei-yubai-site/`
- 電子報：`https://sophie-yubai.beehiiv.com/`
- LINE：目前使用 `@371arhqu`，未來可改成 LIFF 或正式表單。
- 部署決策：見 `docs/deployment-path-2026-05-03.md`
