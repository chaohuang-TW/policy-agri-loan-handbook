# beta.3.3 青壯年導覽與FAQ表格小範圍修正

Luna書表覆核PASS；原書表資料、curation、第一階段報告及humanReviewed=false均保留。未commit／push／部署。

| 導覽 | Before | After |
| --- | --- | --- |
| 申請資格 | P.212第五點文件 | P.211第三點貸款對象 |
| 貸款額度 | P.213第十一點期限 | P.213第十二點額度 |
| 貸款期限 | P.213第十一點 | 保留原落點 |

FAQ第2題原回答文字不變；主要展開區改用P.316–319既有原頁圖片與放大、Evidence、PDF入口；P.319明示另含其他題目。沒有重建HTML數值表。

搜尋507筆；本階段僅page-211的URL加上既有task-eligibility hash；其餘欄位與506筆紀錄完全不變。

以Luna覆核後、閱讀修正前的索引重算125組query/scope（另含青壯年貸款scope）：結果筆數、完整順序、score、所有match evidence及snippet range完全相同；intentOnly=0、scopeLeak=0。[完整比較](search-regression.json)。這不同於書表階段與舊main間的合法metadata變化。

## 實際執行

| Command | Result |
| --- | --- |
| `python -B -c import sys;sys.path.insert(0,"scripts");from build_site import build_site,SITE;from build_search_index import build_search_index;build_site(SITE);build_search_index(SITE)` | PASS |
| `python scripts/test_interpretation_parser.py` | PASS |
| `python scripts/audit_content.py` | PASS |
| `python scripts/validate_display_text.py` | PASS |
| `python scripts/validate_interpretation_metadata.py` | PASS |
| `python scripts/validate_interpretation_decisions.py` | PASS |
| `python scripts/validate_index_quality.py` | PASS |
| `python scripts/validate_navigation_targets.py` | PASS |
| `python scripts/validate_page_rendering.py` | PASS |
| `python scripts/validate_visual_theme.py` | PASS |
| `python scripts/validate_search_experience.py` | PASS |
| `python scripts/validate_ux_structure.py` | PASS |
| `python scripts/validate_official_updates.py` | PASS |
| `python scripts/validate_official_coverage.py` | PASS |
| `python scripts/validate_revision_consistency.py` | PASS |
| `python scripts/validate_disaster_official_gateway.py` | PASS |
| `python scripts/validate_reading_navigation.py` | PASS |
| `python scripts/validate_reference_lookup.py` | PASS |
| `python scripts/validate_official_updates_lookup.py` | PASS |
| `python scripts/validate_forms_source_review.py` | PASS |
| `python scripts/audit_search_precision.py` | PASS |
| `python scripts/audit_task_search_quality.py` | PASS |
| `python scripts/report_source_review_plan.py` | PASS |
| `python scripts/report_official_update_inventory.py` | PASS |
| `python scripts/report_official_coverage.py` | PASS |
| `python scripts/validate_site.py` | PASS |
| `python scripts/validate_forms_source_review.py --write-design-manifest` | PASS |
| `python scripts/design_integrity.py verify reports/forms-review/reading-faq-fix/allowed-forms-design-manifest.json` | PASS |
| `node scripts/test_search_core.cjs` | PASS |
| `node scripts/test_task_search_semantics.cjs` | PASS |
| `node scripts/test_official_updates_lookup.cjs` | PASS |
| `node scripts/benchmark_search_core.cjs` | PASS |
| `node scripts/benchmark_official_updates_lookup.cjs` | PASS |
| `git diff --check` | PASS |
| `python -B -c import sys;from pathlib import Path;sys.path.insert(0,"scripts");import test_forms_source_review_mutations as m;m.REPORT=Path("reports/forms-review/reading-faq-fix");m.main()` | PASS |
| `python scripts/audit_forms_source.py test-followup-mutations` | PASS |
| `python scripts/audit_forms_source.py reproduce-followup` | PASS |
| `node node_modules/@playwright/test/cli.js test --trace off --output tmp/reading-faq-browser-ae7d67f672c147b9a2fd11953abc3d86` | PASS |

## NOT RUN

- build_all.py atomic cleanup entry
- test_validator_mutations.py (70)
- test_reference_lookup_mutations.py (12)
- test_official_updates_lookup_mutations.py (16)
- test_build_reproducibility.py atomic failure/cleanup checks
- CI/production/deployment

上述Gate會清除目錄，依使用者限制留待親自執行；沒有把前輪122/122或172/172當作本輪重跑成績。

Playwright 180/180 PASS（既有172項保留、新增8項）；已重跑24項書表Mutation＋新增7項，共31/31 caught；其餘98項舊Mutation本輪未跑。33/33驗證指令通過。兩次無刪檔重建與目前site逐檔SHA相同；不等同原子失敗復原測試已通過。

所測瀏覽器流程console／pageerror／unhandled rejection／404／unexpected external requests均為0。首輪本機server曾有PDF下載在測試頁關閉後的BrokenPipe警告；最後180項重跑無此警告，最終log保留。

桌機1440px及手機390px前後畫面、原頁來源及差異見本資料夾；source-diff.patch只涵蓋本階段的既有檔案變化，不包含之前書表修正。新增audit_forms_source.py的後續報告／無刪檔驗證helper另依Git diff及本檔追溯，不在beforeFiles快照內。

## 視覺與來源

- FAQ：[390px Before](before-faq-390.png)／[After](after-faq-390.png)；[1440px Before](before-faq-1440.png)／[After](after-faq-1440.png)。
- Loan：[390px Before](before-loan-390.png)／[穩定定位After](after-loan-settled-390.png)；[1440px Before](before-loan-1440.png)／[穩定定位After](after-loan-settled-1440.png)。Before截圖部分仍位於導覽上方，錯誤原落點另由baseline與HTML parser記錄證明。
- [390px原圖入口](after-faq-zoom-390.png)／[1440px原圖入口](after-faq-zoom-1440.png)；原圖不重建數值欄列，實機pinch-to-zoom仍未測。
- 原PDF P.211／213已核對；P.213圖像確認第十一點期限與第十二點額度。[P.213來源圖](source-pdf-213.png)。Poppler曾輸出fontconfig cache警告，但輸出圖像已檢視；未改環境設定或權限。
- 手機完整表格縮圖字較小，需點擊原圖／PDF放大；不能宣稱手機縮圖上所有數值不用放大即清晰。

## 保留基準

HEAD與本機origin/main仍為`3bd8ba14f7e309e565fcb3d3be16bd294025cfbd`；branch為`codex/forms-source-review`，既有未提交書表修改仍保留。本階段沒有fetch／commit／merge／push／部署，也未查閱其他repository。

HTML／Sitemap／Canonical均399；Evidence359；Search507；Loans23；Interpretations87；Forms28；FAQ52題／4組；Sections7。Official Updates20、Coverage partial、verifiedThrough=null，Gateway不變。

PDF359頁、SHA-256 `0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54`；source與download bit-identical。原文、FAQ資料、書表核對資料及第一階段報告checksum均不變。

## 本階段來源檔案

- scripts/reading_navigation.py、scripts/build_site.py
- scripts/validate_reading_navigation.py、scripts/validate_reference_lookup.py、scripts/validate_forms_source_review.py
- scripts/audit_forms_regression.py、scripts/audit_forms_source.py
- tests/browser/handbook.spec.js、tests/browser/reference-lookup.spec.js
- .github/workflows/pages.yml、README.md、CHANGELOG.md
- 新增luna-review.md與本資料夾的baseline／檢查報告／截圖／diff；原書表報告保留。Generated FAQ、Loan及搜尋URL由既有build派生。

## 復原方式

本階段beforeFiles保留11份既有檔案全文，source-diff.patch可人工檢視並反向套用；不需reset整個工作樹，不得丟棄書表修改。Generated site可用恢復後renderer重新建置。新增報告及暫存輸出保留供稽核，不代為刪除。

已檢查：原文、原圖片checksum、399 routes、hash落點、來源連結、搜尋語意與效能。未測：真實手機／螢幕閱讀器及正式站。
