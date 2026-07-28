# 政策性農業專案貸款業務手冊

114年度政策性農業專案貸款業務手冊的公開資料數位閱讀與實務索引版，提供完整目錄、359頁逐頁閱讀、瀏覽器端全文搜尋、23項貸款索引、函釋、常見問答、附件、書表及原始PDF頁面入口。

> 本網站為非官方數位閱讀與索引專案，不是農業部、全國農業金庫、農業信用保證基金或貸款經辦機構官方網站，也不提供資格認定、核貸判斷、授信建議或個案法律意見。

## 資料版本與來源

- 資料版本：114年度
- 發布狀態：Beta
- 數位版本：114.0.0-beta.2.7.1
- 來源文件：114年度政策性農業專案貸款業務手冊
- PDF實體頁數：359頁
- 來源保存：`source/policy-agri-loan-handbook-114.pdf`
- 網站下載：`site/downloads/policy-agri-loan-handbook-114.pdf`
- SHA-256：`0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54`

兩份PDF未重新壓縮、旋轉、刪頁、加浮水印或修改metadata；驗證腳本確認頁數、大小、SHA-256及位元內容一致。`SHA256SUMS.txt` 可供獨立驗證。

## 專案結構

- `source/`：原始PDF永久保存
- `data/114/`：版本資料、目錄、頁碼、貸款、函釋、常見問答、表單附件與覆核狀態
- `data/current/`：手冊出版後經人工核對之官方更新與檢核範圍
- `curation/current/`：官方更新候選逐筆決策
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
python scripts/build_all.py
python scripts/audit_content.py
python scripts/validate_display_text.py
python scripts/validate_interpretation_metadata.py
python scripts/validate_interpretation_decisions.py
python scripts/validate_index_quality.py
python scripts/validate_navigation_targets.py
python scripts/validate_page_rendering.py
python scripts/validate_visual_theme.py
python scripts/validate_search_experience.py
python scripts/validate_ux_structure.py
python scripts/validate_official_updates.py
python scripts/report_official_update_inventory.py
python scripts/validate_site.py
python3 -m http.server 8000 --directory site
```

完整正式 artifact 僅保證透過 `python scripts/build_all.py` 產生。`build_site(output_dir)` 與其他底層 builder function 是 `build_all.py` 使用的 internal building components，不保證可各自獨立形成完整網站。建置先在 `site.__building__` 完成全部頁面及搜尋索引，通過完整性檢查後才原子替換 `site/`；失敗時保留既有網站。Python相依套件列於 `requirements.txt`，Node與Playwright只用於測試，不是網站runtime依賴。

## 搜尋範圍

- 首頁搜尋：預設全手冊。
- 貸款工作頁的inline搜尋：預設本貸款。
- Section Hub的inline搜尋：預設本章。
- Header搜尋：不論目前頁面，預設仍為全手冊；在有情境的頁面可自行切換本貸款／本章。

任務捷徑只擴充至來源語料實際存在的正式用語，不產生資格、額度、利率或期限答案。語意依據見 `docs/TASK_SEARCH_SEMANTICS.md`。

目前507筆全文搜尋索引只涵蓋114年度手冊底本；手冊出版後官方資料另列於「官方更新」，本版本不把兩者混入同一搜尋結果。

## PDF文字與頁面呈現原則

本專案只使用PDF既有文字層，不使用OCR、AI辨識或LLM重建條文，不自行修正文號、日期、金額、比例或條次。原始文字層永久保存在 `pages.json`；搜尋文字只做Unicode及空白正規化。

一般條文以 `text` 顯示。複雜表格、正式書表、常見問答與附件以 `hybrid` 顯示，並同時提供原頁WebP預覽、PDF頁面連結和可展開文字層。若未來版本發現無文字層頁面，將採 `preview` 並明確標示未使用OCR。

## 全文搜尋與隱私

搜尋索引由 `scripts/build_all.py` 透過 `build_search_index.py` 產生，完全在瀏覽器內執行。資料載入後只預先正規化一次，首頁與dialog共用同一份prepared records、概念與意圖資料。正規化查詢上限256字、唯一token上限16、單一token上限128；超限會顯示錯誤且不掃描索引。沒有AI、後端、模型API、向量資料庫、外部搜尋服務、Cookie、分析服務或查詢紀錄上傳。

## 搜尋與閱讀工具

首頁搜尋與全站搜尋視窗共用同一套瀏覽器端搜尋核心，可依原文、貸款、函釋、常見問答、書表及附錄篩選；章節與貸款頁可切換目前範圍及全手冊搜尋。支援 Ctrl+K／Command+K、載入更多結果與長頁回到頂端。搜尋不使用 AI、後端、Cookie 或外部服務，查詢不會上傳。使用者旅程見 [`docs/UX_INFORMATION_ARCHITECTURE.md`](docs/UX_INFORMATION_ARCHITECTURE.md)，搜尋規則見 [`docs/SEARCH_EXPERIENCE.md`](docs/SEARCH_EXPERIENCE.md)。

## 視覺設計

本網站採明亮、清新且專業的公共服務工具風格，以暖白、淡薄荷及自然青綠為主，避免大面積深色背景、官方Logo、照片、外部字型及第三方圖示。視覺系統不影響原始PDF、法規文字、索引資料及搜尋內容。設計 token、版面與可及性規範見 [`docs/VISUAL_DESIGN_SYSTEM.md`](docs/VISUAL_DESIGN_SYSTEM.md)。

## 驗證

```bash
python scripts/audit_content.py
python scripts/validate_display_text.py
python scripts/validate_interpretation_metadata.py
python scripts/validate_index_quality.py
python scripts/validate_page_rendering.py
python scripts/validate_visual_theme.py
python scripts/validate_search_experience.py
python scripts/validate_ux_structure.py
python scripts/validate_official_updates.py
python scripts/validate_site.py
node scripts/test_search_core.cjs
node scripts/benchmark_search_core.cjs
python scripts/test_build_reproducibility.py
python scripts/test_validator_mutations.py
npm ci
npx playwright install chromium
npx playwright test
git diff --check
```

官方更新資料在提交前另須人工執行 `python scripts/audit_official_update_sources.py`；此檢查會連線逐筆核對官方網址、allowlist，以及官方標題或文號。因官方網站可能暫時離線，這項線上檢查是人工更新流程的必要步驟，但不列為一般 Pages CI 的硬性閘門。

驗證涵蓋兩份PDF、359頁資料、頁碼映射、23項貸款索引、嚴格函釋標頭、來源索引與候選庫分類、原頁預覽、搜尋URL、內部連結、H1、重複ID、canonical、免責聲明、Project Pages相對路徑、外部程式碼與追蹤服務禁用規則。`source-indexed` 為可依來源規則追溯的索引，不等於人工逐件確認；`machine-assisted-source-review` 是透過來源頁比對完成候選分類，不等於業務單位覆核；`pending-review` 表示來源資料仍不足以可靠判定。書表未分類候選為0，不代表書表內容已逐頁覆核；函釋結束頁仍待人工確認。人工覆核項目見 `docs/REVIEW_GUIDE.md`。

## 新版更新與版本保存

新版手冊必須使用新version ID並新增PDF，不得覆蓋舊檔。每版均重新計算頁數與SHA-256、建立頁碼映射、擷取文字、重建目錄與搜尋索引、判定複雜頁面並完整驗證。流程見 `docs/UPDATE_CHECKLIST.md`。

本輪只建立數位網站第一版，不建立Git tag或GitHub Release；待人工內容抽查後再另案建立正式Release。

## GitHub Pages部署

`.github/workflows/pages.yml` 在push至 `main` 或手動執行時，使用唯一建置入口，執行Python驗證器、Node搜尋核心與效能測試、可重現建置、28項以上突變及Playwright Chromium整合測試；全部成功後才上傳 `site/` 並部署。Pages來源必須設定為GitHub Actions，不使用 `gh-pages` branch。

正式網址：<https://chaohuang-tw.github.io/policy-agri-loan-handbook/>

## 與範本專案的關係

本專案的數位出版架構與視覺系統，參考同一作者之 `acgf-guarantee-manual` 專案重新建置；兩者資料來源、repository、版本與部署完全分離。本專案不是fork，也不是官方委託系統。

## 免責聲明

內容如與現行法規、主管機關公告或正式文件不一致，以正式發布資料為準。實際申貸資格、額度、期限、利率及應備文件，由貸款經辦機構依現行規定及個案審查結果認定。
