# Wretch Blog Revival

將 `backup/original/` 內的無名小站備份轉換成可長期保存的靜態 Blog。預設網站只輸出原本公開的文章，以及公開文章下的公開留言。

## 環境設定

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## 建置

```bash
python -m wretch_revival inspect
python -m wretch_revival import
python -m wretch_revival build --environment local
```

`build` 會自動重新分析及匯入資料，因此一般只需要執行最後一個命令。

## 本機預覽

```bash
python -m wretch_revival serve
```

然後瀏覽 `http://localhost:8000`。

本機測試網站位於 `dist/local/`，此目錄不會加入 Git。本機版會顯示全部 205 篇文章，非公開文章會標示為「隱藏」或「草稿」；請勿將本機輸出對外發布。

## 正式環境

正式網站必須在保有原始備份的本機產生：

```bash
python -m wretch_revival build --environment production
python scripts/verify_deployment.py dist/production
```

正式成品位於 `dist/production/`。這個目錄只包含原本公開的文章及留言，會加入 Git；`backup/original/`、`data/`、`reports/` 和 `dist/local/` 都不會上傳。

推送 `master` 後，[GitHub Pages workflow](.github/workflows/deploy-pages.yml) 會驗證並部署 `dist/production/`。第一次部署前，Repository 的 **Settings → Pages → Build and deployment → Source** 必須選擇 **GitHub Actions**。

正式網址：

```text
https://orangefallers.github.io/WretchMemoryBuild/
```

## 輸出

- `data/`：包含所有文章及留言的標準化 JSON。
- `reports/`：備份與建置完整性報告。
- `dist/local/`：本機測試網站，不加入 Git。
- `dist/production/`：正式公開網站，由 GitHub Pages 部署。
- `backup/original/`：原始資料，只讀取、不修改。

詳細需求請參閱 [SPEC.md](SPEC.md)。
