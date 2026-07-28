# 手冊出版後官方更新維護流程

114手冊底本與507筆搜尋索引不因本流程改寫。更新層有兩條資料軌：`official-updates.json` 為制度與業務更新；`disaster-loan-announcements.json` 為中央主管機關明確「辦理低利貸款」或「辦理現金救助及低利貸款」的天然災害公告。地方／品項型公告不得混入制度主列表。

每次盤點先建立四類指定官方來源的 `source-review-log.json`，所有發現候選都必須在對應 decision inventory 有決策；只有 include 可進正式資料。搜尋引擎只作官方頁入口，最終證據必須是官方頁。

`verifiedThrough不是build date，也不是最新一筆資料日期，而是指定官方來源實際完成系統性盤點的日期。` 只有所有 required source review 都為 `complete` 時，才可宣告 complete 與 global `verifiedThrough`；否則必須為 partial，且不顯示誤導性的全球日期。

Source Audit 驗證「已收資料是真的」；Coverage Audit 驗證「指定官方來源是否有系統性盤點」。兩者皆必須完成，逐筆 URL 成功不能替代 Coverage complete。

上線前執行：

```bash
python scripts/validate_official_updates.py
python scripts/validate_disaster_loan_announcements.py
python scripts/validate_official_coverage.py
python scripts/report_official_update_inventory.py
python scripts/report_official_coverage.py
python scripts/audit_official_update_sources.py
python scripts/audit_disaster_announcement_sources.py
```

兩支 online audit 是人工 pre-commit mandatory，故不放 Pages CI hard gate，避免官方站瞬時離線阻擋部署。
