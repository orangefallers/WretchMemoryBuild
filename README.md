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
python -m wretch_revival build
```

`build` 會自動重新分析及匯入資料，因此一般只需要執行最後一個命令。

## 本機預覽

```bash
python -m wretch_revival serve
```

然後瀏覽 `http://localhost:8000`。

## 輸出

- `data/`：包含所有文章及留言的標準化 JSON。
- `reports/`：備份與建置完整性報告。
- `dist/`：可直接部署的靜態網站。
- `backup/original/`：原始資料，只讀取、不修改。

詳細需求請參閱 [SPEC.md](SPEC.md)。

