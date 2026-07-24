# 搜尋體驗與驗證

114.0.0-beta.2.5 的搜尋是瀏覽器端、唯讀的全文檢索工具，不是AI、聊天、資格判斷或貸款推薦。索引固定為507筆：359筆原文頁面、23筆貸款索引、87筆函釋、4筆常見問答、28筆書表附件及6筆附錄附件。

## 單一內容歸屬模型

`scripts/content_model.py` 從正式的貸款、原文、函釋、書表、FAQ及附錄資料推導歸屬。`data/114/content-relationships.json` 只保存無法直接推導的section組合、既有公開函釋slug及少數共同規定例外。建站與搜尋索引都呼叫此模型；`search_scope.py` 只保留相容轉呼叫，不另維護映射。

Section頁由實際顯示的原文頁集合取得全部唯一scope，輸出 `data-search-scopes`。貸款頁使用 `data-search-scope-group="loan:<id>"`。FAQ使用 `faq:<id>`，附錄使用 `appendix`，兩者的scopeGroup均為null。

## Prepared search data

JSON只載入一次。`prepareSearchData()` 預先建立normalized title、headings、breadcrumb、text、canonical document number與stable original index；首頁搜尋及全站dialog共用同一Promise及prepared資料。每次查詢先驗證與正規化一次、去除重複token，再先套用scope及type，最後計分、排序和渲染需要的結果。

查詢限制為：

- 正規化後最多256字。
- 唯一token最多16個。
- 單一token最多128字。
- 空字串與純空白直接回傳空結果。
- 超限回傳可朗讀錯誤，不掃描507筆索引。

搜尋不使用Web Worker，因同步核心已低於效能門檻。

## 排名定義

所有權重集中在 `search-core.js` 的 `WEIGHTS`：

- `exactTitle` 只在完整正規化標題等於完整正規化查詢時套用。
- `phraseTitle` 只在標題包含完整查詢且不是完整相等時套用。
- `phraseBody` 是正文完整片語的較低權重。
- title token、headings、breadcrumb與body依不同原始token計分。
- `allTerms` 只考慮使用者原始token，不納入概念擴充詞。
- proximity在每詞有限命中位置中找最小涵蓋視窗。
- 文號使用NFKC、大小寫與空白正規化後的欄位精確比對。

基礎結果先以確定性O(n log n)排序，只對前80筆做有限動態分散；後段保持基礎順序。不使用隨機值。

## Unicode與搜尋片段

`normalizeWithMap()` 以UTF-16 code unit作為normalized text、startMap及endMap的共同索引單位。優先使用 `Intl.Segmenter` 的grapheme cluster；fallback至少保持代理對完整。NFKC轉換後的每個UTF-16 unit都映回完整原始grapheme。

片段蒐集每個詞最多8次命中，以固定240字視窗比較不同原始詞涵蓋、相關詞涵蓋、距離與權重；硬上限320字。只標記視窗內命中，重疊範圍合併，邊界不切斷grapheme。沒有命中時顯示前160字且不建立mark。直接詞使用 `search-highlight`；概念擴充詞使用較淡的 `search-highlight-related` 並附「包含相關詞命中」說明。

## 驗證

`scripts/test_search_core.cjs` 驗證12組固定查詢、23項貸款、87筆文號、28份書表、4組FAQ、6項附錄、7個section、20組Unicode及snippet邊界。`benchmark_search_core.cjs` 使用真實507筆索引，門檻為prepare 1000ms、一般平均100ms、p95 250ms、最大500ms、scope/type p95 200ms、超長防禦50ms、空查詢10ms，且任何搜尋不得超過1秒。

`validate_search_experience.py` 驗證scope、scopeGroup、URL、fragment、版本、列印標籤、安全API、資產一致性與索引計數。`test_validator_mutations.py` 必須攔截15/15突變。Playwright則以真正DOM驗證dialog、鍵盤、焦點、scope、type、注入安全、四個視口、網路、console、回頂端及列印呼叫。

完整命令：

```bash
python scripts/build_all.py
python scripts/validate_search_experience.py
node scripts/test_search_core.cjs
node scripts/benchmark_search_core.cjs
python scripts/test_build_reproducibility.py
python scripts/test_validator_mutations.py
npm ci
npx playwright install chromium
npx playwright test
```
