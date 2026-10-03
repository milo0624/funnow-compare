# 高雄住宿・休息比價（FunNow vs 官方價）

需要時手動抓 FunNow 高雄的住宿與休息方案，和店家官方定價比較，網頁放在 GitHub Pages。

## 檔案

| 檔案 | 用途 |
|---|---|
| `index.html` | 比價網頁 |
| `scrape.py` | 爬蟲（只用 Python 標準函式庫） |
| `data.json` | 爬蟲產生的價格資料，手動執行時更新 |
| `official.json` | 選填：自己查到的官網實際售價 |
| `.github/workflows/update.yml` | 手動執行爬蟲（Actions → Run workflow） |

## 上線步驟

1. 在 GitHub 建一個新的 public repo（例如 `funnow-compare`），把這個資料夾的所有檔案 push 上去（含 `.github` 資料夾）。
2. Settings → Pages → Source 選 `Deploy from a branch`，Branch 選 `main`、資料夾選 `/ (root)`。
3. Settings → Actions → General → Workflow permissions 選 `Read and write permissions`。
4. Actions → 「更新 FunNow 價格」→ Run workflow，跑完後 `data.json` 就是完整資料。
5. 網址：`https://<你的帳號>.github.io/funnow-compare/`

## 選日期

網頁上可選日期，顯示那一天的 FunNow 價（當日最便宜時段）。可選範圍是更新當下 FunNow 開放預訂的日期：休息約 7 天、住宿約 30 天。更新一次約 8 分鐘。

## 填官網實際售價（選填）

`official.json` 的格式：方案編號（網頁每列的 `#編號`）對應價格與網址。

```json
{
  "3031908708988": { "price": 850, "url": "https://飯店官網" }
}
```

## 調整

`scrape.py` 最上方可改：`CITY`（縣市）、`CATEGORIES`（分類）、`DELAY`（請求間隔）。
