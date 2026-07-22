# Beta.2.3 視覺設計系統

本版是 Visual refresh only，不修改 PDF、法規資料、索引、候選判定、頁碼、搜尋資料或網址。

- 語氣：明亮、清新、專業、可信，服務長時間查閱政策農貸資料的讀者。
- 色彩：暖白與淡薄荷作背景，青綠作主色，湖水藍作資訊帶，暖黃只作 Beta／提醒。
- 形狀：卡片採一致 14px 圓角，狀態使用膠囊；以細線、留白與淡色底建立層級。
- 動效：只有輕微 hover／focus；prefers-reduced-motion 會停用 transition、transform 與 smooth scroll。
- 無障礙：維持 skip link、landmark、鍵盤 focus、aria-live、單一 H1、相對連結與列印樣式。
## 搜尋與閱讀工具

搜尋對話視窗使用白色表面、淡綠邊框與低透明深墨綠 backdrop；結果以低飽和類型標籤和淡暖黃 `mark.search-highlight` 標示命中詞。浮動工具列維持白色輕量卡片，不使用深色浮動球或聊天泡泡。手機 dialog 使用接近全螢幕的可捲動結果區；回到頂端與列印工具遵循安全區域及 reduced-motion 規則。
