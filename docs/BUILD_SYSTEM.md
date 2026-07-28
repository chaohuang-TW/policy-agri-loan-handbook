# 原子化建置系統

正式建置的唯一入口是：

```bash
python scripts/build_all.py
```

`build_all.py` 在目標旁建立 `site.__building__`，先由 `build_site.build_site(output_dir)` 產生HTML、CSS、JavaScript、預覽、PDF、概念與意圖資料，再由 `build_search_index.build_search_index(output_dir)` 產生507筆搜尋索引。只有398份HTML與全部必要資產存在時，才以檔案系統rename原子替換 `site/`。

若任何步驟失敗，暫存目錄會清除，既有 `site/` 維持不變。替換期間若發生錯誤，`site.__previous__` 會復原；成功後備份目錄會清除。

兩個底層builder是可匯入且在import時不執行的 internal building components：

- `build_site(output_dir)`：建立網站本體，不依賴舊搜尋索引，但不保證單獨形成完整正式artifact。
- `build_search_index(output_dir)`：只安全更新指定輸出的搜尋索引，不刪除其他內容。

完整正式artifact僅保證透過 `build_all.py` 產生。為維持舊操作安全，直接執行 `build_site.py` 會轉呼叫完整的 `build_all.py`；直接執行 `build_search_index.py` 只更新已存在網站的索引，不清除網站。

`scripts/test_build_reproducibility.py` 在不同暫存輸出驗證：

- 已提交site與全新建置完全一致。
- 連續兩次build_all完全一致。
- build_site後build_search_index完全一致。
- 先執行search index更新再完整build_site CLI語意完全一致。
- 檔案清單、每檔SHA-256、sitemap、HTML、CSS、JavaScript與search index一致。
- 注入建置失敗時舊site不變，暫存與備份目錄均清除。
- PDF與受保護核心資料在測試前後SHA-256不變。

產物不包含時間戳或隨機順序。GitHub Actions也只以 `python scripts/build_all.py` 作正式建置，所有驗證通過後才部署。
