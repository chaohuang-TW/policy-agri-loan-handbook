# 資料模型

`data/versions.json` 保存版本清單；`data/114/` 保存本版手冊、目錄、359頁映射、23項貸款索引、函釋、FAQ、書表附件、呈現規則與人工覆核狀態。

`pages.json` 的 `pdfPage` 是PDF實體頁碼，`printedPage` 是手冊印刷頁碼。前兩頁為目錄；自PDF第3頁起，以九個代表錨點及連續頁碼驗證 `printedPage = pdfPage - 2`。每頁永久保留 `rawText`，搜尋使用僅正規化空白的 `searchText`。

`renderMode` 只允許 `text`、`preview`、`hybrid`。第一版所有頁面均有文字層；複雜表格、FAQ、附件與書表優先採 `hybrid`。
