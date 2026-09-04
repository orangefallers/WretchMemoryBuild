# 無名小站 Blog 復刻專案－程式開發規格書

## 1. 文件資訊

- 專案名稱：Wretch Blog Revival
- 文件版本：v1.1
- 專案目錄：`NoNameBlog`
- 網站類型：Static Site 靜態網站
- 主要技術：Python 3、Jinja2、HTML、CSS、Vanilla JavaScript
- 主要目標：重現並長期保存無名小站 Blog 文章
- 規格依據：實際備份資料分析結果

---

## 2. 專案目的

使用既有的無名小站備份資料，建立一個：

1. 可長期保存。
2. 可在本機離線瀏覽。
3. 可部署至一般靜態網站空間。
4. 保留文章原文、日期、公開狀態與歷史留言。
5. 具有 2005～2012 年無名小站 Blog 閱讀風格。

本專案以 Blog 文章重現為主要需求。相簿、影音、訪客紀錄、好友與其他社群功能不屬於第一階段必要項目。

---

## 3. 開發原則

優先順序：

```text
歷史資料完整性
>
文章閱讀體驗
>
視覺重製
>
附加功能
```

必須遵守：

- 不修改原始備份檔案。
- 不改寫文章或留言內容。
- 不更改歷史日期。
- 不自動校正文句或錯字。
- 不偽造分類、留言、圖片或瀏覽人數。
- 草稿、隱藏文章及隱藏留言不得預設公開。
- 正式網站不得依賴已停止服務的無名小站網址。

---

## 4. 已知備份資料

備份位置：

```text
backup/original/orangefaller-data/
```

### 4.1 主要來源

```text
wretch_2013-09-02_blog.xml
```

用途：

- Blog ID、暱稱、標題與描述。
- 文章 ID、標題、本文與日期。
- 文章公開狀態。
- 留言內容及留言與文章的對應關係。
- 原始分類代碼與其他歷史欄位。

### 4.2 輔助來源

```text
wretch_2013-09-02-movable-type.txt
```

用途：

- 交叉驗證文章標題、日期與本文。
- 取得可用標籤。
- 補充 XML 媒體占位符對應的原始圖片網址。
- 驗證文章的 publish／draft 狀態。
- 驗證公開留言數。

### 4.3 實際資料統計

| 資料 | 數量 |
|---|---:|
| 文章總數 | 205 |
| 公開文章 | 147 |
| 草稿或隱藏文章 | 58 |
| 留言總數 | 475 |
| 公開留言 | 452 |
| 隱藏留言 | 23 |
| 有可用標籤的文章 | 130 |
| 無分類或標籤的文章 | 75 |
| 文章內圖片引用 | 7 |
| 備份內圖片實體檔案 | 0 |

資料檢查結果：

- 205 篇文章皆有 ID、標題、本文與日期。
- 文章 ID 沒有重複。
- 475 則留言皆可對應到現有文章。
- XML 宣告數量與實際節點數量一致。
- XML 與 Movable Type 的 205 篇文章標題及日期一致。
- 所有主要檔案均為 UTF-8。
- 原始日期未附時區，專案預設解讀為 `Asia/Taipei`。

---

## 5. 已知資料限制

### 5.1 分類

XML 的個人分類名稱為空，所有文章的 `category_id` 均為 `0`，不可據此還原原始個人分類。

Movable Type 檔有 130 篇文章帶有可用標籤，包括：

```text
心情
個人
心情小語
團體
學生
校園團體
創作
文學
愛戀情事
鬼話連篇
笑話
```

MVP 處理方式：

- 保留原始標籤。
- 沒有標籤的文章顯示為「未分類」。
- 不宣稱標籤等同於原始個人分類。
- 分類頁面不列為第一階段必要功能。

### 5.2 圖片

文章中共有 7 個圖片引用，分布於 2 篇文章：

- 1 張位於公開文章。
- 6 張位於草稿或隱藏文章。
- 備份中沒有圖片實體檔案。

部分 XML 內容使用以下占位格式：

```text
{###_orangefaller/3/1654601512.jpg_###}
```

Movable Type 檔可能保存相對應的舊圖片網址。Parser 必須辨識占位符，並以同篇文章的 Movable Type 內容補充媒體參照。

若沒有本機圖片檔，輸出頁面必須顯示：

```html
<div class="missing-image">歷史圖片已遺失</div>
```

缺失圖片不得阻止文章建置成功。

### 5.3 原始版型

備份不包含原始 Blog CSS、Banner 或完整介面素材，因此不要求像素級還原原版。MVP 使用自行建立的經典無名小站風格版面。

---

## 6. 公開狀態與隱私規則

### 6.1 預設輸出

正式網站預設只產生：

- 147 篇公開文章。
- 402 則位於公開文章下的公開留言。

### 6.2 非公開資料

以下資料必須解析並保存於標準化資料中，但預設不得產生公開頁面：

- 58 篇草稿或隱藏文章。
- 23 則隱藏留言。
- 50 則位於草稿或隱藏文章下的公開留言。

靜態網站沒有登入及權限控制，因此開啟非公開內容輸出時，使用者必須明確修改設定。

### 6.3 個人資料

預設可顯示：

- 暱稱。
- Blog 名稱。
- Blog 描述。

預設不得顯示：

- 電子郵件。
- MSN、Yahoo Messenger 或其他通訊帳號。
- 生日與其他個人檔案欄位。

---

## 7. 系統架構

```text
原始無名備份（唯讀）
        │
        ▼
Backup Scanner
        │
        ▼
XML Parser + Movable Type Parser
        │
        ▼
資料比對與合併
        │
        ▼
Normalized JSON
        │
        ▼
Jinja2 Static Site Builder
        │
        ▼
HTML / CSS / JavaScript
        │
        ▼
Integrity Check + Build Report
```

---

## 8. 專案目錄

```text
NoNameBlog/
├── README.md
├── SPEC.md
├── pyproject.toml
├── .gitignore
│
├── backup/
│   └── original/
│       └── orangefaller-data/
│
├── config/
│   ├── site.json
│   ├── theme.json
│   └── environments/
│       ├── local.json
│       └── production.json
│
├── .github/
│   └── workflows/
│       └── deploy-pages.yml
│
├── src/
│   └── wretch_revival/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── scanner.py
│       ├── xml_parser.py
│       ├── mt_parser.py
│       ├── merger.py
│       ├── normalizer.py
│       ├── sanitizer.py
│       ├── builder.py
│       ├── integrity.py
│       └── models.py
│
├── templates/
│   ├── base.html
│   ├── components/
│   └── pages/
│
├── static/
│   ├── css/
│   ├── js/
│   └── assets/
│
├── data/
│   ├── posts.json
│   ├── comments.json
│   ├── profile.json
│   └── tags.json
│
├── reports/
│   ├── backup-report.json
│   ├── build-report.json
│   └── build-errors.log
│
├── tests/
│   └── fixtures/
│
├── scripts/
│   └── verify_deployment.py
│
└── dist/
    ├── local/
    └── production/
```

`backup/original/` 內的檔案視為唯讀來源。所有轉換結果只能寫入 `data/`、`reports/` 或 `dist/`。

---

## 9. 備份解析要求

### 9.1 XML Parser

XML Parser 必須解析：

- Blog 基本資料。
- 文章 ID、標題、本文、日期與 PostTime。
- `isCloak` 公開狀態。
- 文章標籤代碼。
- 留言 ID、文章 ID、作者、內容、日期與公開狀態。
- 文章內 `{###_..._###}` 媒體占位符。

### 9.2 Movable Type Parser

Movable Type Parser 必須解析：

- `TITLE`
- `AUTHOR`
- `DATE`
- `TAGS`
- `STATUS`
- `BODY`
- `COMMENT`

Parser 不可只依賴固定行數，必須依區段分隔符與欄位名稱解析。

### 9.3 資料合併

合併規則：

1. XML 為文章及留言的主要來源。
2. Movable Type 以標題與日期配對文章。
3. 若標題與日期無法唯一配對，使用來源順序輔助比對並記錄警告。
4. 標籤由 Movable Type 補充。
5. XML 媒體占位符以 Movable Type 同篇文章中的圖片網址補充。
6. 兩份內容不一致時保留兩份來源資訊，並記錄於 `build-errors.log`。
7. 單篇資料錯誤不得中止其餘文章轉換。

---

## 10. 標準化資料

### 10.1 Post

```json
{
  "id": "2509302",
  "slug": "20060504-2509302",
  "title": "文章標題",
  "date": "2006-05-04T19:36:00+08:00",
  "post_time": "2006-05-04T19:36:57+08:00",
  "visibility": "public",
  "tags": [],
  "content_html": "<p>...</p>",
  "media": [],
  "comment_ids": [],
  "original_url": "http://www.wretch.cc/blog/orangefaller/2509302"
}
```

`visibility` 允許值：

```text
public
draft
hidden
unknown
```

### 10.2 Comment

```json
{
  "id": "comment-id",
  "post_id": "2509302",
  "author": "留言者",
  "date": "2006-05-05T10:06:01+08:00",
  "content_html": "留言內容",
  "visibility": "public"
}
```

留言者名稱為空時顯示「匿名」，不得自行推測作者。

### 10.3 Profile

```json
{
  "nickname": "使用者暱稱",
  "blog_title": "Blog 名稱",
  "description": "Blog 描述"
}
```

不將電子郵件或通訊帳號寫入網站輸出資料。

---

## 11. HTML 處理

文章內容以保真為優先。已知內容主要使用：

```html
<br>
<font>
<p>
<img>
```

允許保留：

```html
<p> <br> <img> <a> <strong> <b> <i> <em>
<blockquote> <font> <center> <table> <tbody> <tr> <td>
```

必須移除：

```html
<script> <iframe> <object> <embed> <applet>
```

同時移除：

- `javascript:` URL。
- 事件處理屬性，例如 `onclick`、`onerror`。
- ActiveX 與不可安全執行的舊元件。

清理後不得改變原始文字、換行順序及標點。

---

## 12. MVP 網站功能

### 12.1 首頁

URL：

```text
/
```

內容：

- Blog 標題與描述。
- 最新文章列表。
- 每頁 10 篇。
- 日期、標題、摘要與留言數。
- 分頁導覽。

### 12.2 單篇文章

URL：

```text
/blog/{slug}.html
```

內容：

- 文章日期。
- 文章標題。
- 原始本文。
- 可用標籤。
- 歷史公開留言。
- 上一篇與下一篇。
- 缺失媒體提示。

### 12.3 月份封存

URL：

```text
/archive/{year}/{month}.html
```

依日期由新到舊列出該月份的公開文章。

### 12.4 Sidebar

MVP 只包含：

- 暱稱。
- Blog 描述。
- 最新文章。
- 月份封存。

分類、最新回應、相簿、好友與訪客計數不列為必要功能。

---

## 13. 網站視覺

桌面版採用：

- 中央固定寬度版面。
- Header、主文章區與 Sidebar。
- 舊式邊框、按鈕與日期標頭。
- 低飽和經典配色。
- 系統字型，不依賴遠端字型服務。

手機版於 `768px` 以下改為：

```text
Header
Main Content
Sidebar
```

不得出現橫向捲軸、文字溢出或圖片破版。

MVP 僅提供 `classic` Theme。

---

## 14. 設定檔

`config/site.json`：

```json
{
  "site_name": "我的無名小站",
  "timezone": "Asia/Taipei",
  "posts_per_page": 10,
  "include_drafts": false,
  "include_hidden_comments": false,
  "show_comments": true,
  "missing_media": "placeholder",
  "category_fallback": "未分類",
  "robots": "noindex"
}
```

`include_drafts` 與 `include_hidden_comments` 預設必須為 `false`。

---

## 15. 建置命令

預計提供：

```bash
# 分析備份
python -m wretch_revival inspect

# 解析與標準化
python -m wretch_revival import

# 產生本機測試網站並執行完整性檢查
python -m wretch_revival build --environment local

# 產生正式公開網站
python -m wretch_revival build --environment production

# 本機預覽
python -m wretch_revival serve
```

本機預覽預設網址：

```text
http://localhost:8000
```

---

## 16. Build Output

```text
dist/
├── local/
│   └── ...本機測試網站
└── production/
    ├── .nojekyll
    ├── index.html
    ├── page/
    ├── blog/
    ├── archive/
    ├── css/
    ├── images/
    └── build-info.json
```

`dist/` 必須可以部署至：

- GitHub Pages。
- Cloudflare Pages。
- Netlify。
- 一般靜態網站空間。
- 本機 HTTP Server。

正式輸出不得依賴 PHP、MySQL、WordPress、外部 CMS、登入系統或專有 API。

環境規則：

- `dist/local/` 由 `.gitignore` 排除，只供本機測試。
- `dist/production/` 只包含篩選後的公開內容，必須加入 Git。
- GitHub Actions 只可上傳 `dist/production/`。
- 原始備份、標準化資料、報告與虛擬環境不得加入部署 Artifact。
- 正式頁面使用相對連結，以支援 GitHub Pages 的 `/WretchMemoryBuild/` 子路徑。

---

## 17. Integrity Check

原規格中的「原始文章數等於輸出文章數」改為依公開狀態核對。

預設設定下必須符合：

```text
解析文章總數 = 205
公開文章數 = 147
草稿或隱藏文章數 = 58
輸出文章頁數 = 147

解析留言總數 = 475
公開留言數 = 452
隱藏留言數 = 23
公開文章下的公開留言數 = 402
輸出留言數 = 402
```

`reports/build-report-local.json` 與 `reports/build-report-production.json` 範例：

```json
{
  "posts_parsed": 205,
  "posts_public": 147,
  "posts_private_or_draft": 58,
  "posts_generated": 147,
  "comments_parsed": 475,
  "comments_public": 452,
  "comments_hidden": 23,
  "comments_on_generated_posts": 402,
  "comments_generated": 402,
  "article_image_references": 7,
  "article_images_available": 0,
  "missing_images": 7,
  "orphan_comments": 0,
  "build_success": true
}
```

缺失圖片屬已知備份限制，只要頁面已顯示替代內容，不應令 `build_success` 變成 `false`。

---

## 18. 錯誤處理

所有警告與錯誤寫入：

```text
reports/build-errors.log
```

錯誤至少包含：

- 來源檔案。
- 文章或留言 ID。
- 錯誤類型。
- 是否跳過資料。
- 可用的替代處理。

單篇文章解析失敗不得讓整個 Build 直接停止。完整性報告必須明確列出失敗數量。

---

## 19. 驗收標準

### 19.1 資料

- 成功解析 205 篇文章。
- 文章標題、本文與日期不得遺失。
- 公開狀態正確對應。
- 475 則留言全部保留於標準化資料。
- 留言與文章的對應錯誤數為 0。
- 中文不得出現亂碼。
- 不修改原文、留言及日期。
- 缺失圖片不得顯示瀏覽器 Broken Image 圖示。

### 19.2 輸出

- 預設產生 147 個公開文章頁面。
- 預設顯示公開文章下的 402 則公開留言。
- 草稿、隱藏文章與隱藏留言不出現在公開導覽、封存或 HTML 中。
- 首頁、文章頁與月份封存在桌面及手機均可閱讀。
- 網站不依賴無名小站或 Yahoo 舊網址才能顯示文章。

### 19.3 瀏覽器

需在目前版本的以下瀏覽器正常閱讀：

- Chrome
- Edge
- Safari
- Firefox
- iOS Safari
- Android Chrome

---

## 20. 開發階段

### Phase 1：文章重現 MVP

- XML Parser。
- Movable Type Parser。
- 資料比對與合併。
- 文章與留言 JSON。
- HTML 安全處理。
- Blog 首頁。
- 單篇文章頁。
- 月份封存。
- 基本 Sidebar。
- 缺失圖片提示。
- RWD。
- Build Script。
- Integrity Check。

### Phase 2：閱讀功能

- 前端全文搜尋。
- 標籤頁面。
- 最新回應。
- 更多 Sidebar 模組。
- Theme 切換。

### Phase 3：其他備份內容

- 相簿。
- 影片與音訊保存。
- 留言板。
- 好友資料。
- 更接近原版的 Wretch Classic Mode。

Phase 2 與 Phase 3 均不影響 Phase 1 驗收。

---

## 21. 最終成果

Phase 1 完成後應取得：

1. 可重複執行的備份解析與網站建置程式。
2. 包含全部文章及留言的標準化保存資料。
3. 預設只顯示歷史公開內容的靜態 Blog。
4. 可直接部署或透過本機 HTTP Server 瀏覽的 `dist/`。
5. 可核對文章、留言與媒體缺失情況的建置報告。

最終網站的核心成果是：在不改寫歷史內容的前提下，重新提供接近當年無名小站 Blog 的文章閱讀體驗。
