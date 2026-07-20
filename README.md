# 政策性農業專案貸款業務手冊

114年度政策性農業專案貸款業務手冊的公開資料數位閱讀與實務索引版，提供完整目錄、359頁逐頁閱讀、瀏覽器端全文搜尋、23項貸款索引、函釋、FAQ、附件、書表及原始PDF頁面入口。

> 本網站為非官方數位閱讀與索引專案，不是農業部、全國農業金庫、農業信用保證基金或貸款經辦機構官方網站，也不提供資格認定、核貸判斷、授信建議或個案法律意見。

## 資料版本與來源

- 資料版本：114年度
- 發布狀態：Beta
- 數位版本：114.0.0-beta.2.1
- 來源文件：114年度政策性農業專案貸款業務手冊
- PDF實體頁數：359頁
- 來源保存：`source/policy-agri-loan-handbook-114.pdf`
- 網站下載：`site/downloads/policy-agri-loan-handbook-114.pdf`
- SHA-256：`0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54`

兩份PDF未重新壓縮、旋轉、刪頁、加浮水印或修改metadata；驗證腳本確認頁數、大小、SHA-256及位元內容一致。`SHA256SUMS.txt` 可供獨立驗證。

## 專案結構

- `source/`：原始PDF永久保存
- `data/114/`：版本資料、目錄、頁碼、貸款、函釋、FAQ、表單附件與覆核狀態
- `scripts/`：擷取、預覽、搜尋、建置與驗證腳本
- `templates/`、`assets/`：靜態網站模板、CSS、JavaScript與預覽圖
- `site/`：GitHub Pages部署成品
- `docs/`：資料模型、更新、呈現與人工覆核文件

## 本機建置

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/extract_manual.py
python scripts/render_page_previews.py
python scripts/test_interpretation_parser.py
python scripts/build_site.py
python scripts/build_search_index.py
python scripts/audit_content.py
python scripts/validate_display_text.py
python scripts/validate_interpretation_metadata.py
python scripts/validate_index_quality.py
python scripts/validate_page_rendering.py
python scripts/validate_site.py
python3 -m http.server 8000 --directory site
```

所有必要套件均列於 `requirements.txt`，不依賴Codex私有工具、Node建置鏈、後端、資料庫或雲端API。

## PDF文字與頁面呈現原則

本專案只使用PDF既有文字層，不使用OCR、AI辨識或LLM重建條文，不自行修正文號、日期、金額、比例或條次。原始文字層永久保存在 `pages.json`；搜尋文字只做Unicode及空白正規化。

一般條文以 `text` 顯示。複雜表格、正式書表、FAQ與附件以 `hybrid` 顯示，並同時提供原頁WebP預覽、PDF頁面連結和可展開文字層。若未來版本發現無文字層頁面，將採 `preview` 並明確標示未使用OCR。

## 全文搜尋與隱私

搜尋索引由 `scripts/build_search_index.py` 產生，完全在瀏覽器內執行。沒有後端、模型API、向量資料庫、外部搜尋服務、Cookie、分析服務或查詢紀錄上傳。

## 驗證

```bash
python scripts/audit_content.py
python scripts/validate_display_text.py
python scripts/validate_interpretation_metadata.py
python scripts/validate_index_quality.py
python scripts/validate_page_rendering.py
python scripts/validate_site.py
git diff --check
```

驗證涵蓋兩份PDF、359頁資料、頁碼映射、23項貸款索引、嚴格函釋標頭、來源索引與候選庫分類、原頁預覽、搜尋URL、內部連結、H1、重複ID、canonical、免責聲明、Project Pages相對路徑、外部程式碼與追蹤服務禁用規則。`source-indexed` 為可依來源規則追溯的索引，不等於人工逐件確認；`pending-review` 才是尚待人工判定的候選，candidate inventory total 則包含提升、重複與待覆核紀錄。人工覆核項目見 `docs/REVIEW_GUIDE.md`。

## 新版更新與版本保存

新版手冊必須使用新version ID並新增PDF，不得覆蓋舊檔。每版均重新計算頁數與SHA-256、建立頁碼映射、擷取文字、重建目錄與搜尋索引、判定複雜頁面並完整驗證。流程見 `docs/UPDATE_CHECKLIST.md`。

本輪只建立數位網站第一版，不建立Git tag或GitHub Release；待人工內容抽查後再另案建立正式Release。

## GitHub Pages部署

`.github/workflows/pages.yml` 在push至 `main` 或手動執行時，安裝Python依賴、先清除並重建網站，再產生確認資料限定的搜尋索引及執行五項驗證；成功後只上傳 `site/`，再使用GitHub官方Pages actions部署。Pages來源必須設定為GitHub Actions，不使用 `gh-pages` branch。

正式網址：<https://chaohuang-tw.github.io/policy-agri-loan-handbook/>

## 與範本專案的關係

本專案的數位出版架構與視覺系統，參考同一作者之 `acgf-guarantee-manual` 專案重新建置；兩者資料來源、repository、版本與部署完全分離。本專案不是fork，也不是官方委託系統。

## 免責聲明

內容如與現行法規、主管機關公告或正式文件不一致，以正式發布資料為準。實際申貸資格、額度、期限、利率及應備文件，由貸款經辦機構依現行規定及個案審查結果認定。
