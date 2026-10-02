# beta.3.2 baseline audit

基準：7d9b75d，beta.3.1.1。2026-10-02，Chromium 1.61.1，zh-TW，1x，390×844／1440×1000。全部是模擬視口，非真機。截圖在 `tmp/design-audit/before/`，由 `node scripts/capture_design_audit.cjs before` 重現；此目錄不進正式 site。

|頁型／視口|實際現象|類型／影響|截圖|預計修法|
|---|---|---|---|---|
|首頁390／1440|資料狀態大面積薄荷框排在任務與四入口前；同權重膠囊很多|視覺／操作：核心入口較難掃描|home-first-screen-390.png、home-1440.png|任務優先重排；關鍵字與需求區分；書頁式兩欄Hero|
|貸款索引390／1440|每筆厚框與大量重複類別；卡高約200px|視覺：掃描效率低|loans-390.png、loans-1440.png|將索引變成緊湊編輯式列表，保留完整名称及來源|
|長貸款390／1440|側欄在手機先占約170px；6筆官方更新全展開，原文很後面|操作：定位原文要長距離捲动|long-loan-390.png、long-loan-1440.png|原生收合更新詳情與手機導覽；舒適閱讀欄|
|Section390／1440|H1與側欄上緣不一致；更新列表比本章內容搶眼|視覺／操作|section-390.png、section-1440.png|弱化附加資料，sidebar安全sticky與原生手機TOC|
|FAQ390／1440|主提示、工具提示、外層綠框、內層白框、fieldset重疊|視覺／操作：查閱框手機接近底部|faq-390.png、faq-open-1440.png|統一查閱表單；範圍清楚但低干擾；答案保留details|
|函釋390／1440|單筆文號結果仍被類別快速導覽與大工具框推到下方|操作：搜到後不易立即看到|interpretations-390.png、interpretations-1440.png|原生收合類別入口；標題／文號清楚階層|
|更新390／1440|Coverage大區塊先占手機首屏，查閱框不在主要位置|操作：新查閱功能難發現|updates-390.png、updates-filter-1440.png|保留partial說明，先提供查閱，再提供完整檢核範圍|
|Gateway390／1440|簡單外部入口包綠框與暖色框；內容重複強調|視覺：不必要層級|gateway-390.png、gateway-1440.png|單一清楚官方CTA與來源文字；不改URL|
|text Evidence390／1440|正文16px，文字行寬偏長，來源頁也有厚圓框|視覺：長時間閱讀疲勞|text-evidence-390.png、text-evidence-1440.png|18px桌機／17px手機；閱讀欄約40全形字；細頁界|
|hybrid Evidence390／1440|手機先看逐頁導覽而非頁題；影像正確完整|操作；影像本身無內容問題|hybrid-evidence-390.png、hybrid-evidence-1440.png|緊湊手機導覽；保留影像比例及放大入口|
|原書目錄390／1440|不同level多張同樣框；視覺層級較弱|視覺|toc-390.png、toc-1440.png|原始順序不變，使用縮排、字重與稀疏分隔|
|Dialog390／1440|搜尋後焦點到結果使sticky表單重疊部分結果；雙捲動容器|操作|dialog-390.png、dialog-1440.png|單一dialog捲動；關閉控制sticky，表單不蓋結果|

內容邊界：本輪不改原文、起訖頁、公式、文號或覆核狀態；函釋start-only與書表人工覆核仍待後續處理。

初次baseline suite為127/132：trace顯示本機簡易HTTP服務的ERR_CONNECTION_RESET／ERR_SOCKET_NOT_CONNECTED，及腳本因此未載入；不是查詢結果差異。測試伺服器改用HTTP/1.1與64連線backlog後重測132/132通過；不刪測試、不放寬斷言。原FAQ-open首屏未拍到答案，已從基準commit另補相同題目的完整元件圖，不能把原首屏當成答案驗收。
