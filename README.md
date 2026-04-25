# 菲菲的餘白網站落地包

這個資料夾目前是一個可直接預覽、可部署到 GitHub Pages 的靜態網站 MVP。目標不是慢慢籌備，而是先把完整品牌入口、電子報入口、內容承接與 GitHub 部署一次做出來，之後只要定期更新。

## 目前包含

- `index.html`：一頁式品牌網站
- `assets/styles.css`：網站樣式
- `assets/main.js`：訂閱表單的本機互動
- `assets/hero-yubai.png`：首頁主視覺
- `docs/`：電子報、方格子、LINE、內容地圖與即刻上線文件

## 預覽方式

直接用瀏覽器打開 `index.html`。

## 上線路線

GitHub Pages 路線：

1. 在 GitHub 建立新 repo。
2. 上傳這個資料夾內容。
3. 到 repo 的 Settings > Pages，選擇從 `main` branch 的根目錄部署。
4. 自訂網域時，把 DNS 指向 GitHub Pages。

Framer / Carrd 路線：

1. 把 `index.html` 的文案搬到 Framer 或 Carrd。
2. 在 beehiiv 或 Brevo 建立《餘白來信》。
3. 把電子報 embed code 接到首頁的訂閱區。
4. 把方格子文章底部 CTA 全部導向這個網站。

## 下一步要替換

- LINE 連結：目前先接到 `@371arhqu`。
- 電子報表單：改成 beehiiv / Brevo 的正式表單。
- 閱讀路徑文章：補上方格子正式連結。
- LINE CTA：補上 LINE 官方帳號或 LIFF 連結。
