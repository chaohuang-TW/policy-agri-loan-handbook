# 114.0.0-beta.3.2 視覺與使用體驗檢視

基準為 `7d9b75dd63a0a62b2437227d6ef3d7d73ec41192`／beta.3.1.1；來源、正式站及遠端均已先確認。唯一實作工作分支為 `codex/editorial-design-upgrade`。設計系統與參考來源分別見 `docs/DESIGN_SYSTEM.md`、`docs/DESIGN_REFERENCES.md`。

## 真實證據與覆蓋

2026-10-02，Playwright 1.61.1／Chromium 149、zh-TW、1x。主畫面固定390×844及1440×1000，before、round-1、round-2、round-3各28種頁型／状态，首頁另拍首屏與全頁。包括首頁、貸款索引、青壯年長貸款、Section、FAQ、FAQ展開、函釋、官方更新、更新篩選、dialog、原書目錄、text／hybrid Evidence、天然災害Gateway。

執行工作區證據在 `tmp/design-audit/`，不進site、不提交大量圖檔；這是本機QA檔案位置，**不是公開下載URL**。完整元件圖在 `details/`：以內容高度擴展拍攝視口，避免離屏合成造成來源按鈕缺漏；不能拿它冒稱390×844首屏。原固定視口圖仍保留。before的原始FAQ-open首屏沒有拍到答案，故不能用作長答案驗收；已從基準commit的HTML/CSS於独立暫存目錄補拍相同真實問題「屠宰場登記證書」的before／after答案與來源操作，不重置工作樹。

操作旅程另拍逐步截圖：首頁查詢「農機」→貸款結果→任務anchor→原始Evidence。列印QA包括青壯年貸款、FAQ原回答、hybrid Evidence三份Chromium A4輸出及渲染PNG；不修改359頁手冊PDF。不冒稱macOS原生列印預覽驗收。

## 三輪實際迭代

|輪次|看圖／實測發現|修正|複驗結果|
|---|---|---|---|
|第一輪|FAQ手機搜尋按鈕文字換行；更新頁Coverage仍壓在工具前；閱讀頁先出導覽後出頁題|縮小手機按鈕內距、維持nowrap；查閱先行，完整Coverage移到原生details；標題／來源移到閱讀格線之前|第二輪390／1440圖：三個問題消除，來源文字checksum不變|
|第二輪|200%文字令桌機nav溢位；固定500ms等待不足以證明長頁hash完成；noscript文字matcher排除元素；399頁批次超過30秒；獨立review另指出dialog失去卡頭、重複更新結果數及答案截圖缺口|原生flex重排及ResizeObserver更新CSS定位間距；改poll保留可視範圍assert；驗真正noscript子段落；批次120秒但399頁assert不減；焦點仍落首來源連結，以卡頭捲動保留上下文；保留legacy狀態hook但只顯示一份count；補拍答案|四項失敗先單獨4/4，再完整158/158；第三輪dialog卡頭、問題／回答及更新count實際可見|
|第三輪|實際列印PDF的lazy Evidence影像曾空白；完整元件截圖的離屏操作未合成；旅程曾截到「搜尋中」而非結果|beforeprint請求原圖，QA等待成功載入，print限制整張影像適配紙張而不裁切；擴展元件拍攝高度；等待實際貸款結果後拍旅程|影像重渲染確實含原始完整書頁；元件來源按鈕與全文可見；完整suite再次158/158|

## 八個設計面向

|面向|具體設計／觀察證據|
|---|---|
|排版|正文桌機18px／手機17px，行高1.85–1.9；閱讀區760px含padding，正文約696px／38.7全形字。round-3 text-evidence-1440與details/after-loan-source-1440保留完整原段落。|
|留白|1248px外框、216px側欄、48px閱讀欄距；移除結果卡片套卡片，細頁界維持掃描。updates-1440只留一份count，來源與操作分層。|
|層級|home首屏input底部約453px，390×844和375×667皆可操作；任務與四入口早於Coverage。FAQ結果早於四組來源清單，函釋類別導航保留但收合。|
|色彩|亮底、正文#213C32、次文#52675E、操作#286B57；computed style驗正文／metadata／空結果／hover／selected≥4.5或大字≥3，focus outline及input邊界≥3；active文字≥4.5。|
|動效|140–200ms只提供操作回饋，無進場等待／內容隱藏；reduced-motion取消transition／animation／smooth-scroll，功能仍通過。|
|微互動|原生details、44px主要操作、清楚focus；dialog單一捲動容器、Escape返回原控制，查詢後首卡context／title／evidence可見。|
|響應式|320／375／390／393／430／768／1024／1280／1440／1920各12頁型bounding-box與scrollWidth通過；200%文字、keyboard、mobile TOC和anchor reload通過，不使用overflow:hidden遮問題。|
|原創性|小型CSS書頁邊線／田區格線識別只在桌機Hero來源欄；aria-hidden、不冒充統計圖、不抄他站素材；手機移除装飾占位。|

## 查詢與來源保真

`design_integrity.py`真正解析HTML來源區塊，保護30個凍結來源／JS檔checksum（manual只排除允許的digitalRevision）、399 routes／canonical、sitemap、既有anchor、原始文字及預覽影像mapping。第三輪覆核另指出手機長結果的footer焦點可能在可视範圍外；結果原始標題改成同URL原生連結作首focus，原footer來源操作不變，bounding-box驗首focus與上下文同時可見。補拍baseline元件亦校準原頁首安全距，避免原較高sticky header擋住來源小標。

before與最終after `queries.json`位元相同：SHA-256 `5543f76754755339434ce0254f6440cdfe88a460b9e65a209c3ec2100a5cac92`。比較含六個手冊查詢的全量結果順序、score、matchKind、matched evidence；FAQ與函釋各六個fixture；官方更新文號、AND、負面、全形空白／Tab及program/type/year組合，含官方更新全量score。核心三個JS未改；`search.js`只新增同URL的原始標題連結及焦點／可視落點，不改篩選、數量、排序或URL state。

399 HTML／canonical／sitemap、359 Evidence、507手冊索引、23貸款、87函釋、28書表、52題FAQ／4組、7Section、20官方更新全部保留。Coverage仍partial，verifiedThrough仍null，地方災害資料仍0，官方Gateway不變。PDF維持359頁、來源／下載bit-identical，SHA-256 `0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54`。

閱讀validator：1100個hash有效，duplicate IDs／broken hash=0；215個Evidence入口有效；384個prev／next無self／ordering error；23貸款148個真實task導航、13個不可用task維持隱藏；7Section 28個TOC項。

## 實際測試與預期差異

- baseline原132項：HTTP/1.0低backlog導致連線reset，改原生HTTP/1.1／64backlog測試伺服器後132/132通過，不改產品資料或刪assert。
- 首次完整Chromium158/158＝132項保留＋26項設計回歸。部署後修復再追加2項七章全部anchor的click／reload回歸，最終160/160。三組Mutation70/70、12/12、16/16，uncaught=0。修復後再次完整執行25個Python validators／audits／inventory reports、三個Node suite、兩個benchmark、來源完整性、revision consistency、reproducibility與diff check，全部通過。
- 新設計已接入既有Playwright CI；source integrity與官方lookup純函式測試已明列CI。正式站的部署後驗收另行執行，本文件不是尚未發生的部署證明。
- 唯一既有可見狀態調整：手機Section TOC由open起始改為closed，測試由「已展開→收合→再開」改為「已收合→展開→收合」，同樣驗原生state、keyboard與overflow；沒有弱化目標存在、hash或內容assert。
- loan smooth scroll不再假設固定500ms完成，保留「target在header下且在viewport內」的完整條件並poll。399頁批次timeout由30到120秒，仍逐頁檢查全部399頁H1、ID、圖像和runtime。
- noscript matcher特例改驗瀏覽器實際解析的可見子段落；不是移除無JSfallback要求。

## 獨立覆核與限制

獨立唯讀reviewer確實看diff、before／after390／1440代表圖並核對來源保真，不與實作者同時改工作樹。第二輪FIX REQUIRED四項（dialog卡頭、FAQ答案證據、重複結果數、control/focus對比）及後續首focus可視問題均已修正，第三輪最終獨立覆核PASS，沒有剩餘FIX REQUIRED實作缺陷。沒有冒稱另一模型或官方獲獎認證。

WebKit26.5代表八頁型×390／1440smoke通過，最終build再測16/16（含可視原生title-link焦點），資料與runtime錯誤均0。Firefox1532在此macOS27環境即使sandbox外亦無法啟動（plugin-container權限／SWGL framebuffer），因此標示blocked而非PASS。200%測試是computed-font doubled文字放大模擬，不冒稱原生瀏覽器zoom。真機、讀屏、OS原生列印預覽、實際使用者Core Web Vitals未測；實驗室量測不能替代它們。原文人工校訂、函釋結束頁及書表覆核仍未完成。

## 部署後的真實finding與修復

首次提交 `d948529` 的CI與Pages均success，但獨立正式站覆核指出390px的TOC點選後reload可能還原展開TOC時的scroll位置；reload將TOC收合後，章節搜尋H2或來源summary被65px sticky header遮住。實際案例包括bank-operating-rules-appendices的搜尋heading top3.27px、source summary top37.17px。load／fonts.ready後再等3秒仍存在，不能當成DCL暫態。首版正式站結論因此保留FIX REQUIRED，不宣稱已完成。

修復只在手機reading-layout正常同頁hash導航前先原生收合section-nav details，使點選與reload之前的layout一致；不preventDefault、不計算offset、不window.scrollTo，modifier／新分頁仍保持原行為，桌機仍展開。資料、core與href皆未改。独立本機覆核56組click／reload、7組四步sequence、2組鍵盤Enter、Meta新分頁與後續Tab均PASS；28 target存在／DOM順序正確、duplicate0。最後的WebKit16/16同樣加强四個Section anchor逐一reload，runtime／external／badresponse0。

獨立正式站首輪另驗七章348個來源HTML皆HTTP200、來源排序及前後頁正確，保存完整FIX REQUIRED／focused replay／load replay證據；不以修後PASS覆蓋舊失敗紀錄。最後修復仍須重新部署，並在正式站完成獨立覆核，才算產品完成。

## 效能實測

CSS 37,153→33,567 bytes，gzip7,323→7,180；site-tools.js gzip1,607→2,257（最終6,775 bytes），search.js gzip3,961→4,128（最終14,561 bytes）。presentation JS增加817 gzip bytes、CSS減少143 gzip bytes，合計增加674 gzip bytes；三個查詢核心大小／hash不變。代表入口首次載入7個requests，沒有新增外部runtime。原本before未節流FCP20–64ms，首次after20–40ms，這些是單次本機navigation樣本，不推論真實使用者改善。

最後hash修復資產的Lighthouse13.5.0／Chrome149／Node24.19.0，在2026-10-02 04:58:21–05:00:49 UTC依序完成15/15。每次fresh Chrome/profile、預設storage reset、固定預設simulated throttling（mobile RTT150ms／CPU4×；desktop RTT40ms／CPU1×），不是手機真機。獨立QA代理保留完整設定、15份原始JSON及summary於repository外的私有暫存artifact，未提交含本機路徑的raw報告。十項HTML/CSS/JS SHA在量測前後一致；對前輪只有允許修改的site-tools.js改變，其source／generated SHA相同。首提交d948529的04:09:21–04:11:50量測原始報告另行保留，不冒稱其屬最終修復資產。

|頁型／三次中位數|Performance|Accessibility|Best Practices|SEO|FCP ms|LCP ms|TBT ms|CLS|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|首頁mobile|100|100|100|100|937.08|1088.63|0|0|
|FAQ mobile|100|100|100|100|1097.04|1249.07|0|0|
|函釋mobile|100|100|100|100|1107.12|1259.17|0|0|
|更新mobile|100|100|100|100|941.63|1093.45|0|0|
|首頁desktop|100|100|100|100|251.95|293.42|0|0|

desktop單輪CLS最大0.001386，中位數仍0；不隱去單輪變異。十五份完整configSettings逐輪與前輪一致，compression audit皆true。

QA採HTTP/1.1 gzip傳輸（`serve_test_site.py --gzip`），因正式Pages已實際確認gzip；不改部署資產、資料或benchmark門檻。早先未壓縮HTTP/1.0環境的FAQ P94、桌機A96及一次updates timeout仍保留原始紀錄，沒有刪除；aria-label缺group role的真實問題已修。舊／新build及傳輸環境不同，**不把它們當作gzip單一因素A/B改善證據**。以上不代表field Core Web Vitals、INP或WCAG認證。
