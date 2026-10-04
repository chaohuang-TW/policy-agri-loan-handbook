# beta.3.3 本機發布 Gate 閉合紀錄

本紀錄補充先前階段報告，不覆寫其歷史結果。本機 Gate PASS 不代表 CI、push、Pages 部署或正式站已完成；這些狀態必須以後續實際執行結果確認。

## 基準與留存

- 唯一 repository：chaohuang-TW/policy-agri-loan-handbook。
- 開始 HEAD 與重新 fetch 後 origin/main：`3bd8ba14f7e309e565fcb3d3be16bd294025cfbd`。
- 使用既有 `codex/forms-source-review`；保留所有 beta.3.3 既有修改。
- 751 個 source/data/curation/assets/site 驗證輸入，與三份成功 release run 的 checksum 全部一致。
- 56 份原階段報告仍與 reading-faq-fix/baseline.json 的 checksum 一致。
- 建置、失敗 staging、先前站點及獨立 Mutation fixtures 全部受控留存於 `tmp/release-gates/`，不包含在 Pages artifact，不自動刪除。
- `humanReviewed=false`；Luna 模型覆核不是人工確認。

## 新增程式獨立覆核

書表來源覆核與建置／Mutation／CI 程式覆核分開。實際 gpt-6-luna 唯讀獨立覆核 PASS，見 [新程式覆核](luna-build-mutation-ci-review.md) 與 [case 56 補充覆核](luna-case56-review.md)。先前失敗 run 及其診斷全部保留，沒有以任意非零 exit 當作 caught。

## 補驗結果

| 實際 command | 結果 | 證據 |
| --- | --- | --- |
| `python -B scripts/test_build_reproducibility.py --retain-workspace` | PASS；兩次建置、正反順序、索引失敗、發布失敗復原與成功留存 | [結果](release-reproducibility-8cef2655d2ac403fb6acba785490c2ee/release-reproducibility-results.json) |
| `python -B scripts/test_validator_mutations.py --retain-workspace` | 70/70 caught；8 個未修改 positive controls PASS | [結果](release-mutations-9bc24197e29f49ee856eaf87de8d6448/release-mutations-results.json) |
| `python -B scripts/test_reference_lookup_mutations.py --retain-workspace` | 12/12 caught；positive control PASS | 同上 |
| `python -B scripts/test_official_updates_lookup_mutations.py --retain-workspace` | 16/16 caught；positive control PASS | 同上 |
| `python -B scripts/audit_official_update_sources.py` | 20/20 HTTP 與來源題名核對 PASS | [結果](release-online-9753625b77774b42a561f2a7979bc8d4/release-online-results.json) |
| `python -B scripts/audit_disaster_official_gateway.py` | PASS | 同上 |
| `python -B scripts/validate_revision_consistency.py` | PASS；beta.3.3、399 HTML | 實際 terminal output |
| `git diff --check` | PASS | 實際 terminal output |

本輪補跑 98 項檔案 Mutation；另保留已通過的 24 項書表與 7 項閱讀／FAQ Mutation，合計可追溯 129/129。沒有把 31 項既有成績說成這次重跑。

已通過的 33 項本機驗證／測試／benchmark 與 Playwright 180/180 不整套重跑，原結果與輸入仍一致，見 [驗證紀錄](../reading-faq-fix/validation-results.json)、[瀏覽器紀錄](../reading-faq-fix/browser-results.json) 與 [前後差異](../reading-faq-fix/report.md)。CI 會在 fresh checkout 執行完整發布 Gate。

## 內容與搜尋界線

- 青壯年貸款：申請資格第三點 P.211；額度第十二點 P.213；期限保留第十一點 P.213。原文順序、制度內容與既有 task hash 不變。
- FAQ 第2題使用既有 P.316–319 原頁圖片，原回答全文保留；P.319 其他題目明示分界。沒有重建 HTML 數值表或补值。
- 書表來源修正可造成六筆書表 metadata 的合法搜尋結果變化，原 Luna 覆核有記錄；不得宣稱與舊 main 所有 ranking 完全相同。
- 小範圍閱讀修正僅改 page-211 URL hash，125 組 query/scope 的完整排序、score、evidence 與 snippet ranges 不變；intentOnly=0、scopeLeak=0。
- PDF 359 頁，SHA-256 `0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54`，source/download bit-identical。
- HTML/Sitemap/Canonical 399、Evidence 359、Search 507、Loans 23、Interpretations 87、Forms 28、FAQ 52 題/4 組、Sections 7、Official Updates 20；Coverage partial、verifiedThrough=null、Gateway 不變。

## 尚未以本紀錄認證的事項

branch CI、main CI、Pages artifact／部署、正式站版本及互動讀回仍是必要發布 Gate，任何失敗即停止。真實手機、螢幕閱讀器與 pinch-to-zoom 未測；手機表格縮圖需原圖或 PDF 放大，不能宣稱所有數值無須放大即可清楚辨讀。全書、函釋末頁及書表的人工覆核未完成。
