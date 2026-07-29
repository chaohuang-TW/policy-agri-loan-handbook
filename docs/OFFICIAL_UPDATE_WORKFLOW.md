# 手冊出版後官方更新維護流程

114手冊底本與507筆搜尋索引不因本流程改寫。更新層只有一條正式資料軌：`official-updates.json`，只收錄制度與業務更新。地方型天然災害公告不得混入此資料集。

## 天然災害地區／品項公告政策

- 不複製、不追蹤、不計數，也不宣稱完整。
- `updates/disasters/` 是農業金融署官方入口頁，不是本站公告資料庫。
- 一律導向 `https://www.afna.gov.tw/list.php?theme=natural_disaster&subtheme=`。
- 天然災害制度修正、表單、免息、利息補貼及特殊措施仍納入 `official-updates.json`。

真正的 Official Source Discovery 目前仍為人工／Codex 連線查核官方來源；每次盤點先建立四類指定官方來源的 `source-review-log.json`，所有發現候選都必須在對應 decision inventory 有決策；只有 include 可進正式資料。搜尋引擎只作官方頁入口，最終證據必須是官方頁。`report_source_review_plan.py` 只輸出應檢查的日期範圍、查詢、列表頁與狀態，不是 crawler。

`verifiedThrough不是build date，也不是最新一筆資料日期，而是指定官方來源實際完成系統性盤點的日期。` 只有所有 required source review 都為 `complete` 時，才可宣告 complete 與 global `verifiedThrough`；否則必須為 partial，且不顯示誤導性的全球日期。

Source Audit 驗證「已收資料是真的」；Coverage Audit 驗證「指定官方來源是否有系統性盤點」。兩者皆必須完成，逐筆 URL 成功不能替代 Coverage complete。

上線前執行：

```bash
python scripts/validate_official_updates.py
python scripts/validate_official_coverage.py
python scripts/validate_revision_consistency.py
python scripts/validate_disaster_official_gateway.py
python scripts/report_official_update_inventory.py
python scripts/report_official_coverage.py
python scripts/report_source_review_plan.py
python scripts/audit_official_update_sources.py
python scripts/audit_disaster_official_gateway.py
```

兩支 online audit 是人工 pre-commit mandatory，故不放 Pages CI hard gate，避免官方站瞬時離線阻擋部署。每次變更官方 gateway URL 前必須人工執行 gateway audit。
