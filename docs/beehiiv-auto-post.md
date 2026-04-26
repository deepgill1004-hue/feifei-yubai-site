# beehiiv 自動貼文流程

這個 repo 已經準備好把 `beehiiv/posts/*.json` 對應的內容送到 beehiiv，建立成草稿。

## 需要先設定的 GitHub Secrets

到 GitHub repo：

`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

新增：

- `BEEHIIV_API_KEY`
- `BEEHIIV_PUBLICATION_ID`
- `BEEHIIV_POST_TEMPLATE_ID`，可選

## 重要限制

beehiiv 的 Create post / Send API 目前屬於 Enterprise beta 功能。若帳號沒有權限，GitHub Action 會失敗並顯示 beehiiv API 錯誤。

## 如何觸發

只要更新並 push `beehiiv/**`，GitHub Actions 會自動執行：

`Sync beehiiv draft`

它會呼叫：

`scripts/create-beehiiv-drafts.mjs`

並建立 `draft`，不會直接寄出。

## 本機測試

```bash
node scripts/create-beehiiv-drafts.mjs --dry-run
```

## 目前第一篇

設定檔：

`beehiiv/posts/001.json`

HTML 內容：

`beehiiv/sophie-yubai-simple-template.html`
