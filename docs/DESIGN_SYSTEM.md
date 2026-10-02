# 編輯式專業知識網站設計系統

定位：田野的格線 × 手冊的書頁 × 清楚的資料索引。以專業金融實務查閱者為對象，不是政府官方系統，不提供業務判斷。

沿用原生靜態HTML／CSS／JavaScript，無新框架、外部字型、裝飾點陣圖、runtime CDN、追蹤或查詢上傳。design-taste-frontend用於audit-first、階層與狀態檢核；使用者要求的輕量、亮色、系統繁中字型與來源凍結優先於該技能的通用框架、雙主題與圖片建議。

## 設計尺度

DESIGN_VARIANCE=4：有編輯式非對稱Hero，但實務工具保持可預期。MOTION_INTENSITY=2：只用120–200ms操作回饋。VISUAL_DENSITY=5：查閱和長文的資訊密度，不做行銷型空白。全站單一亮色主題。

## 字體與格線

系統字型：macOS/iOS PingFang TC、Windows Microsoft JhengHei及系統fallback，無外部請求。桌機正文18px、手機17px、line-height1.85–1.9。控制16px、來源15–16px。H1桌機最高54px，手機30–32px；長標題自然換行，不截斷，text-wrap:balance避免單字孤行。

外框1248px；閱讀內容760px含必要padding，實際正文約696px，18px約38.7個全形字。索引較寬，來源與FAQ答案仍限制閱讀欄。桌機側欄216px；1024以下轉原生收合導覽。Header1199以下切手機控制，避免兩行硬擠。

間距4/8/12/16/20/24/32/40/48/64/80px；圓角4/6/8px僅控件／表單／dialog，正文、索引與來源頁用細分隔，不卡片包卡片。

## 色彩與角色

|角色|值|使用|
|---|---|---|
|背景|#F7FAF8|全站框架|
|閱讀表面|#FFFFFF|書頁／表單|
|正文|#213C32|主文字|
|次要文字|#52675E|可讀來源metadata|
|操作|#286B57|主按鈕與selected|
|深操作|#1F5848|hover、link|
|薄荷／湖水|#EAF4EE／#EDF6F7|小面積範圍提示|
|分隔|#D9E5DE|非必要裝飾邊界|
|控制邊界|#7C9186|input/select與次按鈕識別|
|focus／target|#8B621F|3px outline／非純色彩左邊線|

保留舊token相容alias。對比實際在瀏覽器computed style驗證，不只檢查hex。default/hover/selected/focus/visited保持可辨識，disabled不得模仿selected。

## 元件與內容語意

主表單一層白底、查詢+主要操作、次篩選。結果主題先、文號／日期其次、來源操作最後；不改結果數量或排序。FAQ保留native details；函釋start-only保留文字，出版後官方更新獨立，Coverage仍partial。

首頁先搜尋與8常用字，再7任務與四入口，後置範圍／近期官方資料／覆核說明。四入口主連結是一整個可操作内容塊，次連結独立，无nested link。原創field-mark是小型CSS書頁邊線／田區幾何，aria-hidden，非數據圖示，手機不占位。

貸款附加官方更新原生收合，標題始終可見；全文與來源mapping完整保存。TOC與相容anchor不变。單一dialog捲動表面，sticky關閉標題不蓋搜尋結果；不再sticky表單。

## 互動、響應式與列印

主要button/input至少44px；input16px；focus-visible3px；link是link，button是button。390及375手機可即刻操作主查詢。320–1920用bounding box／scrollWidth驗證；不以全頁overflow:hidden掩蓋問題。

所有原文預設可見，不依賴進場動畫。reduced-motion取消transition/smooth-scroll，核心功能不变。Beforeprint展開FAQ回答與文字層、afterprint還原。Print來源正文不裁切，導航與工具不印；圖像width100%、heightauto完整保留。原生作業系統預覽與真機／讀屏驗收不冒稱完成。
