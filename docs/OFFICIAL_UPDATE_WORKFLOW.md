# 手冊出版後官方更新維護流程

本流程只維護獨立的 `data/current/` 更新層，不修改 `data/114/` 的手冊原文、函釋、FAQ、書表或507筆搜尋索引。

1. 先讀 `data/current/coverage.json`，以 `searchStartDate` 為搜尋起點；`verifiedThrough` 只能在指定官方來源實際盤點完成後更新。
2. 逐一以共同規定、20項政策性農業專案貸款完整名稱、天然災害詞、FAQ／函示詞，以及3項全國農業金庫貸款完整名稱查詢。
3. 搜尋引擎僅用來找到官方頁；證據必須直接來自 allowlist 內的官方頁面。
4. 每個發現的候選都寫入 `curation/current/official-update-decisions.json`，決策只能是 `include`、`already-covered`、`exclude-irrelevant` 或 `needs-human-review`。
5. 只有 `include` 可以同步進 `data/current/official-updates.json`。標題、機關、文號、日期、受理期間與 `relationEvidence` 必須照官方來源，不寫摘要、不做新舊差異解釋。
6. 關聯貸款只能依標題、主旨、本文明確點名，或共同法規明確適用範圍建立；不確定時保留人工核對。
7. 執行離線 validator、inventory report、完整建置與全站驗證。上線前人工執行 online audit。

指令：

```bash
python scripts/validate_official_updates.py
python scripts/report_official_update_inventory.py
python scripts/audit_official_update_sources.py
```

Online audit 故意不放入 CI，避免官方站短暫網路狀況阻斷 Pages 部署；每次正式更新仍必須由維護者人工執行並保存結果。
