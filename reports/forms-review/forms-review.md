# beta.3.3 Pre-commit Source Review

## 一、Git

- Base / HEAD: `3bd8ba14f7e309e565fcb3d3be16bd294025cfbd`；origin/main: `3bd8ba14f7e309e565fcb3d3be16bd294025cfbd`。
- Branch: `codex/forms-source-review`；working tree: 本輪修改尚未提交。
- Commit = 尚未；merge = 尚未；push = 尚未；CI / 正式站部署 = 尚未。

來源僅同一114年度PDF、frozen pages.json與Evidence。reviewedByModel=true；humanReviewed=false。待Luna唯讀獨立覆核，不宣稱發布完成。

## 二、28 Forms Review Table

verified / verified-with-correction 均為本輪模型來源核對狀態，不代表使用者人工覆核。

| Form | 標題 | PDF起–迄 | 印刷頁 | Source Pages | Scope | 狀態 | 人工需求 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| form-001 | 農業發展基金貸款利息差額補貼申請書 | 40–40 | 38–38 | [40] | null（共通書表） | verified | 否 |
| form-002 | 專案農貸額度控管期限延長申請書 | 43–43 | 41–41 | [43] | null（共通書表） | verified | 否 |
| form-003 | 專案農貸延期還款案件申請書(甲式) | 53–53 | 51–51 | [53] | null（共通書表） | verified-with-correction | 否 |
| form-004 | 專案農貸延期還款案件申請書(乙式) | 54–54 | 52–52 | [54] | null（共通書表） | verified-with-correction | 否 |
| form-005 | 專案農貸延期還款案件審核表 | 55–56 | 53–54 | [55, 56] | null（共通書表） | verified-with-correction | 否 |
| form-006 | 農機貸款申請書 | 99–99 | 97–97 | [99] | loan:farm-machinery-loan | verified | 否 |
| form-007 | 輔導農糧業經營貸款申請書 | 106–107 | 104–105 | [106, 107] | loan:agri-food-business-loan | verified-with-correction | 否 |
| form-008 | 輔導漁業經營貸款申請書 | 117–118 | 115–116 | [117, 118] | loan:fishery-business-loan | verified-with-correction | 否 |
| form-009 | 提升畜禽產業經營貸款(除污染防治類外)申請書 | 128–129 | 126–127 | [128, 129] | loan:livestock-poultry-loan | verified-with-correction | 否 |
| form-010 | 提升畜禽產業經營貸款申請書 | 131–131 | 129–129 | [131] | loan:livestock-poultry-loan | verified-with-correction | 否 |
| form-011 | 農民經營及產銷班貸款申請書 | 152–153 | 150–151 | [152, 153] | loan:farmer-production-group-loan | verified-with-correction | 否 |
| form-012 | 農業科技園區進駐業者優惠貸款申請書 | 163–164 | 161–162 | [163, 164] | loan:agri-tech-park-loan | verified-with-correction | 否 |
| form-013 | 農家綜合貸款申請書 | 174–174 | 172–172 | [174] | loan:farm-household-loan | verified | 否 |
| form-014 | 農漁會事業發展貸款申請書 | 183–183 | 181–181 | [183] | loan:association-development-loan | verified | 否 |
| form-015 | 造林貸款申請書 | 190–191 | 188–189 | [190, 191] | loan:afforestation-loan | verified-with-correction | 否 |
| form-016 | 造林貸款土地勘查申請書 | 193–193 | 191–191 | [193] | loan:afforestation-loan | verified | 否 |
| form-017 | 小地主大專業農貸款申請書 | 202–203 | 200–201 | [202, 203] | loan:small-landlord-professional-farmer-loan | verified-with-correction | 否 |
| form-018 | 農業節能減碳貸款申請書 | 207–208 | 205–206 | [207, 208] | loan:agri-energy-saving-loan | verified-with-correction | 否 |
| form-019 | 青壯年農民從農貸款申請書 | 215–217 | 213–215 | [215, 216, 217] | loan:young-farmer-loan | verified-with-correction | 否 |
| form-020 | 休閒農場貸款申請書 | 227–228 | 225–226 | [227, 228] | loan:leisure-farm-loan | verified-with-correction | 否 |
| form-021 | 農民組織及農企業產銷經營及研發創新貸款申請書 | 234–235 | 232–233 | [234, 235] | loan:agri-organization-enterprise-innovation-loan | verified-with-correction | 否 |
| form-022 | 農民組織及農企業天然災害復耕復建貸款申請書 | 247–248 | 245–246 | [247, 248] | loan:agri-organization-disaster-recovery-loan | verified-with-correction | 否 |
| form-023 | 農業天然災害受災證明書(申貸「農民組織及農企業天然災害復耕復建貸款」專用) | 251–252 | 249–250 | [251, 252] | loan:agri-organization-disaster-recovery-loan | verified-with-correction | 否 |
| form-024 | 農業保險貸款申請書 | 254–254 | 252–252 | [254] | loan:agricultural-insurance-loan | verified | 否 |
| form-025 | 農民紓困貸款申請書 | 258–258 | 256–256 | [258] | loan:farmer-relief-loan | verified | 否 |
| form-026 | 擴大家庭農場經營規模協助農民購買耕地貸款申請書 | 265–267 | 263–265 | [265, 266, 267] | loan:farmland-purchase-loan | verified-with-correction | 否 |
| form-027 | 農業天然災害受災證明書 | 292–293 | 290–291 | [292, 293] | loan:natural-disaster-low-interest-loan | verified-with-correction | 否 |
| form-028 | 額度動用申請書 | 305–305 | 303–303 | [305] | loan:agricultural-rooting-loan | verified-with-correction | 否 |

{"forms": 28, "reviews": 28, "sourcePages": 46, "multiPageForms": 16, "corrected": 20, "verified": 8, "humanReviewItems": 0, "routes": 399, "searchCount": 507, "changedSearchRecords": ["forms-form-003", "forms-form-004", "forms-form-009", "forms-form-023", "forms-form-027", "forms-form-028"], "startOnly": 0, "ambiguous": 0, "needsHumanReview": 0, "visuallyCheckedReferencePages": 78}

## 三、Corrections

### form-003: title

- Before: `"專案農貸延期還款案件申請書（甲式）"`
- After: `"專案農貸延期還款案件申請書(甲式)"`
- P2 METADATA ERROR；PDF P.53；[versions/114/pages/page-053.html#pdf-page-53](../../site/versions/114/pages/page-053.html#pdf-page-53)
- 改為來源可見題名；只移除抽取換行／空白，不變更標點或補貸款前綴。

### form-004: title

- Before: `"專案農貸延期還款案件申請書（乙式）"`
- After: `"專案農貸延期還款案件申請書(乙式)"`
- P2 METADATA ERROR；PDF P.54；[versions/114/pages/page-054.html#pdf-page-54](../../site/versions/114/pages/page-054.html#pdf-page-54)
- 改為來源可見題名；只移除抽取換行／空白，不變更標點或補貸款前綴。

### form-005: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 55, "printedPageEnd": 53, "sourcePages": [55]}`
- After: `{"pdfPageEnd": 56, "printedPageEnd": 54, "sourcePages": [55, 56]}`
- P1 RANGE ERROR；PDF P.56；[versions/114/pages/page-056.html#pdf-page-56](../../site/versions/114/pages/page-056.html#pdf-page-56)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-007: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 106, "printedPageEnd": 104, "sourcePages": [106]}`
- After: `{"pdfPageEnd": 107, "printedPageEnd": 105, "sourcePages": [106, 107]}`
- P1 RANGE ERROR；PDF P.107；[versions/114/pages/page-107.html#pdf-page-107](../../site/versions/114/pages/page-107.html#pdf-page-107)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-008: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 117, "printedPageEnd": 115, "sourcePages": [117]}`
- After: `{"pdfPageEnd": 118, "printedPageEnd": 116, "sourcePages": [117, 118]}`
- P1 RANGE ERROR；PDF P.118；[versions/114/pages/page-118.html#pdf-page-118](../../site/versions/114/pages/page-118.html#pdf-page-118)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-009: title

- Before: `"提升畜禽產業經營貸款（除污染防治類外）申請書"`
- After: `"提升畜禽產業經營貸款(除污染防治類外)申請書"`
- P2 METADATA ERROR；PDF P.128；[versions/114/pages/page-128.html#pdf-page-128](../../site/versions/114/pages/page-128.html#pdf-page-128)
- 改為來源可見題名；只移除抽取換行／空白，不變更標點或補貸款前綴。

### form-009: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 128, "printedPageEnd": 126, "sourcePages": [128]}`
- After: `{"pdfPageEnd": 129, "printedPageEnd": 127, "sourcePages": [128, 129]}`
- P1 RANGE ERROR；PDF P.129；[versions/114/pages/page-129.html#pdf-page-129](../../site/versions/114/pages/page-129.html#pdf-page-129)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-010: sourceSubtitle

- Before: `null`
- After: `"（畜牧污染防治類專用）"`
- P2 METADATA ERROR；PDF P.131；[versions/114/pages/page-131.html#pdf-page-131](../../site/versions/114/pages/page-131.html#pdf-page-131)
- 補上來源可見副題（不改寫主題名）。

### form-011: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 152, "printedPageEnd": 150, "sourcePages": [152]}`
- After: `{"pdfPageEnd": 153, "printedPageEnd": 151, "sourcePages": [152, 153]}`
- P1 RANGE ERROR；PDF P.153；[versions/114/pages/page-153.html#pdf-page-153](../../site/versions/114/pages/page-153.html#pdf-page-153)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-012: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 163, "printedPageEnd": 161, "sourcePages": [163]}`
- After: `{"pdfPageEnd": 164, "printedPageEnd": 162, "sourcePages": [163, 164]}`
- P1 RANGE ERROR；PDF P.164；[versions/114/pages/page-164.html#pdf-page-164](../../site/versions/114/pages/page-164.html#pdf-page-164)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-015: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 190, "printedPageEnd": 188, "sourcePages": [190]}`
- After: `{"pdfPageEnd": 191, "printedPageEnd": 189, "sourcePages": [190, 191]}`
- P1 RANGE ERROR；PDF P.191；[versions/114/pages/page-191.html#pdf-page-191](../../site/versions/114/pages/page-191.html#pdf-page-191)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-017: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 202, "printedPageEnd": 200, "sourcePages": [202]}`
- After: `{"pdfPageEnd": 203, "printedPageEnd": 201, "sourcePages": [202, 203]}`
- P1 RANGE ERROR；PDF P.203；[versions/114/pages/page-203.html#pdf-page-203](../../site/versions/114/pages/page-203.html#pdf-page-203)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-018: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 207, "printedPageEnd": 205, "sourcePages": [207]}`
- After: `{"pdfPageEnd": 208, "printedPageEnd": 206, "sourcePages": [207, 208]}`
- P1 RANGE ERROR；PDF P.208；[versions/114/pages/page-208.html#pdf-page-208](../../site/versions/114/pages/page-208.html#pdf-page-208)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-019: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 215, "printedPageEnd": 213, "sourcePages": [215]}`
- After: `{"pdfPageEnd": 217, "printedPageEnd": 215, "sourcePages": [215, 216, 217]}`
- P1 RANGE ERROR；PDF P.217；[versions/114/pages/page-217.html#pdf-page-217](../../site/versions/114/pages/page-217.html#pdf-page-217)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-020: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 227, "printedPageEnd": 225, "sourcePages": [227]}`
- After: `{"pdfPageEnd": 228, "printedPageEnd": 226, "sourcePages": [227, 228]}`
- P1 RANGE ERROR；PDF P.228；[versions/114/pages/page-228.html#pdf-page-228](../../site/versions/114/pages/page-228.html#pdf-page-228)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-021: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 234, "printedPageEnd": 232, "sourcePages": [234]}`
- After: `{"pdfPageEnd": 235, "printedPageEnd": 233, "sourcePages": [234, 235]}`
- P1 RANGE ERROR；PDF P.235；[versions/114/pages/page-235.html#pdf-page-235](../../site/versions/114/pages/page-235.html#pdf-page-235)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-022: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 247, "printedPageEnd": 245, "sourcePages": [247]}`
- After: `{"pdfPageEnd": 248, "printedPageEnd": 246, "sourcePages": [247, 248]}`
- P1 RANGE ERROR；PDF P.248；[versions/114/pages/page-248.html#pdf-page-248](../../site/versions/114/pages/page-248.html#pdf-page-248)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-023: title

- Before: `"農業天然災害受災證明書（復耕復建貸款用）"`
- After: `"農業天然災害受災證明書(申貸「農民組織及農企業天然災害復耕復建貸款」專用)"`
- P2 METADATA ERROR；PDF P.251；[versions/114/pages/page-251.html#pdf-page-251](../../site/versions/114/pages/page-251.html#pdf-page-251)
- 改為來源可見題名；只移除抽取換行／空白，不變更標點或補貸款前綴。

### form-023: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 251, "printedPageEnd": 249, "sourcePages": [251]}`
- After: `{"pdfPageEnd": 252, "printedPageEnd": 250, "sourcePages": [251, 252]}`
- P1 RANGE ERROR；PDF P.252；[versions/114/pages/page-252.html#pdf-page-252](../../site/versions/114/pages/page-252.html#pdf-page-252)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-023: scopeGroup

- Before: `null`
- After: `"loan:agri-organization-disaster-recovery-loan"`
- P1 RELATION ERROR；PDF P.251；[versions/114/pages/page-251.html#pdf-page-251](../../site/versions/114/pages/page-251.html#pdf-page-251)
- 本表題名直接寫出貸款專用名稱；末頁備註另有同名申貸交叉引用。

### form-026: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 265, "printedPageEnd": 263, "sourcePages": [265]}`
- After: `{"pdfPageEnd": 267, "printedPageEnd": 265, "sourcePages": [265, 266, 267]}`
- P1 RANGE ERROR；PDF P.267；[versions/114/pages/page-267.html#pdf-page-267](../../site/versions/114/pages/page-267.html#pdf-page-267)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-027: pdfPageEnd / printedPageEnd / sourcePages

- Before: `{"pdfPageEnd": 292, "printedPageEnd": 290, "sourcePages": [292]}`
- After: `{"pdfPageEnd": 293, "printedPageEnd": 291, "sourcePages": [292, 293]}`
- P1 RANGE ERROR；PDF P.293；[versions/114/pages/page-293.html#pdf-page-293](../../site/versions/114/pages/page-293.html#pdf-page-293)
- 逐頁看來源表格／欄位續接與結尾；下一頁為明確新題名，不依下一筆索引推算。

### form-027: scopeGroup

- Before: `null`
- After: `"loan:natural-disaster-low-interest-loan"`
- P1 RELATION ERROR；PDF P.292；[versions/114/pages/page-292.html#pdf-page-292](../../site/versions/114/pages/page-292.html#pdf-page-292)
- 本表題名直接寫出貸款專用名稱；末頁備註另有同名申貸交叉引用。

### form-027: sourceSubtitle

- Before: `null`
- After: `"(申貸「農業天然災害低利貸款」專用)"`
- P2 METADATA ERROR；PDF P.292；[versions/114/pages/page-292.html#pdf-page-292](../../site/versions/114/pages/page-292.html#pdf-page-292)
- 補上來源可見副題（不改寫主題名）。

### form-028: title

- Before: `"農業紮根貸款額度動用申請書"`
- After: `"額度動用申請書"`
- P2 METADATA ERROR；PDF P.305；[versions/114/pages/page-305.html#pdf-page-305](../../site/versions/114/pages/page-305.html#pdf-page-305)
- 改為來源可見題名；只移除抽取換行／空白，不變更標點或補貸款前綴。

## 四、form-023 Evidence Dossier

最終 scopeGroup: `loan:agri-organization-disaster-recovery-loan`。依表單自身專用題名／副題及末頁直接交叉引用判定，非依鄰近位置。

```json
{
  "formId": "form-023",
  "formalTitle": "農業天然災害受災證明書(申貸「農民組織及農企業天然災害復耕\n復建貸款」專用)",
  "pdfPage": 251,
  "printedPage": 249,
  "previousPage": {
    "pdfPage": 250,
    "evidenceUrl": "versions/114/pages/page-250.html#pdf-page-250",
    "headQuote": "農業天然災害復耕復建計畫書\n（農民組織及農企業天然災害復耕復建貸款專用）\n                                                                        105.3.22 修正版\n一、申請人基本資料\n名稱  統一編號\n負責人",
    "tailQuote": "    年  月/  年  月/  年  月\n年  月/  年  月/  年  月\n合          計\n申請人簽章：                                 申請日期：      年    月    日\n編號:16.1",
    "belongsToSameForm": false
  },
  "currentPage": {
    "pdfPage": 251,
    "printedPage": 249,
    "evidenceUrl": "versions/114/pages/page-251.html#pdf-page-251",
    "role": "title-and-start",
    "headQuote": "農業天然災害受災證明書(申貸「農民組織及農企業天然災害復耕\n復建貸款」專用)\n一、基本資料(請申請人填寫)\n災 害 名 稱  申 請 日 期     年   月   日\n名      稱  統一編號\n住      址  電      話",
    "tailQuote": "□大型定置網類(□全毀整組換新/重佈□半毀部分修復/\n重佈)□其他定置網類\n114.9.5 修正版\n(適用於 114.7.7 以後\n發生之天然災害"
  },
  "nextPage": {
    "pdfPage": 252,
    "printedPage": 250,
    "evidenceUrl": "versions/114/pages/page-252.html#pdf-page-252",
    "role": "continuation-and-ending",
    "headQuote": "【在漁港區域漁船】\n□全毀(新建漁船，含舢舨)□半毀(修復漁船，含舢舨)\n【在漁港區域漁筏】\n□全毀(新建漁筏)□半毀(修復漁筏)\n畜\n牧",
    "tailQuote": "或林業及自然保育署__________分署___________工作站(請蓋關防)\n備註：申請人申請「農民組織及農企業天然災害復耕復建貸款」 ，應於本證明書核發\n之翌日起30個工作日內 ， 檢具本證明書、農業天然災害復耕復建計畫書 、 農民\n組織或農企業登記證明文件、其代表人或負責人之身分證明文件及其他貸款\n應具備文件，向貸款經辦機構提出申請。",
    "continuesSameForm": true
  },
  "nextBoundary": {
    "nextPdfPage": 253,
    "nextEvidenceUrl": "versions/114/pages/page-253.html#pdf-page-253",
    "nextHeadingQuote": "農業保險貸款要點\n中華民國 106 年 6 月 5 日行政院農業委員會農金字第 1065084127A 號令訂定發布全文\n16 點；並自 106 年 6 月9 日生效\n中華民國 110 年 1 月 11 日行政院農業委員會農授金字第 1105084018B 號令修正第 11\n點；並自 110 年 1 月 11 日生效\n一、 行政院農業委員會(以下簡稱農委會)為提高農(漁)業者參加農業保險意願，以穩定",
    "closingQuote": "或林業及自然保育署__________分署___________工作站(請蓋關防)\n備註：申請人申請「農民組織及農企業天然災害復耕復建貸款」 ，應於本證明書核發\n之翌日起30個工作日內 ， 檢具本證明書、農業天然災害復耕復建計畫書 、 農民\n組織或農企業登記證明文件、其代表人或負責人之身分證明文件及其他貸款\n應具備文件，向貸款經辦機構提出申請。",
    "method": "visual-field-continuity-and-explicit-next-heading",
    "includedNextForm": false
  },
  "tocNode": {
    "id": "agri-organization-disaster-recovery-loan",
    "order": 34,
    "level": 4,
    "title": "16. 農民組織及農企業天然災害復耕復建貸款要點",
    "kind": "loan",
    "printedPage": 242,
    "pdfPage": 244,
    "sourceTocPdfPage": 1
  },
  "explicitLoanName": "農民組織及農企業天然災害復耕復建貸款",
  "explicitSectionName": "農民組織及農企業天然災害復耕復建貸款要點",
  "directCrossReference": {
    "pdfPage": 252,
    "quote": "或林業及自然保育署__________分署___________工作站(請蓋關防)\n備註：申請人申請「農民組織及農企業天然災害復耕復建貸款」 ，應於本證明書核發\n之翌日起30個工作日內 ， 檢具本證明書、農業天然災害復耕復建計畫書 、 農民\n組織或農企業登記證明文件、其代表人或負責人之身分證明文件及其他貸款\n應具備文件，向貸款經辦機構提出申請。"
  },
  "candidateScopeGroup": "loan:agri-organization-disaster-recovery-loan",
  "supportingEvidence": [
    "P.251題名直接寫出申貸「農民組織及農企業天然災害復耕復建貸款」專用。",
    "P.252備註再次指名申請同一貸款，並引用本證明書及計畫書。"
  ],
  "opposingEvidence": [
    "主題名「農業天然災害受災證明書」與form-027相同，不能僅靠短名或相鄰頁歸屬。"
  ],
  "finalStatus": "verified-with-correction",
  "decisionCriterion": "A-form-explicit-loan-name",
  "requiresHumanReview": false
}
```

## 五、form-027 Evidence Dossier

最終 scopeGroup: `loan:natural-disaster-low-interest-loan`。依表單自身專用題名／副題及末頁直接交叉引用判定，非依鄰近位置。

```json
{
  "formId": "form-027",
  "formalTitle": "農業天然災害受災證明書",
  "subtitle": "(申貸「農業天然災害低利貸款」專用)",
  "pdfPage": 292,
  "printedPage": 290,
  "previousPage": {
    "pdfPage": 291,
    "evidenceUrl": "versions/114/pages/page-291.html#pdf-page-291",
    "headQuote": "經營使用)\n(一)段木香菇與木耳 最高一百二十萬元/公頃 最長七年，本金寬緩期限最長二\n年。\n(二)臺灣金線連 最高三十七萬五千元/公頃 最長五年，本金寬緩期限最長二\n年。\n(三)森林蜂產品(涉及養蜂",
    "tailQuote": "筍之部分)\n最高三十七萬元/公頃 最長五年，本金寬緩期限最長二\n年。\n註：本表所列林業低利貸款項目、貸款額度及期限，適用於中華民國一百十四年一月一日以後\n發生之天然災害。",
    "belongsToSameForm": false
  },
  "currentPage": {
    "pdfPage": 292,
    "printedPage": 290,
    "evidenceUrl": "versions/114/pages/page-292.html#pdf-page-292",
    "role": "title-and-start",
    "headQuote": "114.9.2修正版\n(適用於114.7.7以後\n發生之天然災害)\n農業天然災害受災證明書\n(申貸「農業天然災害低利貸款」專用)\n一、基本資料(請申請人填寫)",
    "tailQuote": "【定置網漁網】\n□大型定置網類(□全毀整組換新/重佈□半毀部分\n修復/重佈)□其他定置網類\n【在漁港區域漁船】\n附件"
  },
  "nextPage": {
    "pdfPage": 293,
    "printedPage": 291,
    "evidenceUrl": "versions/114/pages/page-293.html#pdf-page-293",
    "role": "continuation-and-ending",
    "headQuote": "□全毀(新建漁船，含舢舨)□半毀(修復漁船，含舢\n舨)\n【在漁港區域漁筏】\n□全毀(新建漁筏)□半毀(修復漁筏)\n畜\n牧",
    "tailQuote": "__________________________鄉(鎮、市、區)公所(請蓋關防)\n或林業及自然保育署__________分署___________工作站(請蓋關防)\n備註：申請人申請「農業天然災害低利貸款」 ，應於本證明書核發之翌日起30個工作\n日內 ， 檢具本證明書 、 農業天然災害低利貸款申請暨計畫書 ， 向貸款經辦機構\n提出申請。",
    "continuesSameForm": true
  },
  "nextBoundary": {
    "nextPdfPage": 294,
    "nextEvidenceUrl": "versions/114/pages/page-294.html#pdf-page-294",
    "nextHeadingQuote": "編號:\n農業天然災害低利貸款申請暨計畫書\n  縣(市)   鄉(鎮、市、區)  災害名稱 (   年   月   日 )\n一、申請人基本資料：\n姓名 出生\n日期",
    "closingQuote": "__________________________鄉(鎮、市、區)公所(請蓋關防)\n或林業及自然保育署__________分署___________工作站(請蓋關防)\n備註：申請人申請「農業天然災害低利貸款」 ，應於本證明書核發之翌日起30個工作\n日內 ， 檢具本證明書 、 農業天然災害低利貸款申請暨計畫書 ， 向貸款經辦機構\n提出申請。",
    "method": "visual-field-continuity-and-explicit-next-heading",
    "includedNextForm": false
  },
  "tocNode": {
    "id": "natural-disaster-rules",
    "title": "（三）農業天然災害救助辦法",
    "printedPage": 270,
    "pdfPage": 272,
    "sourceTocPdfPage": 2
  },
  "explicitLoanName": "農業天然災害低利貸款",
  "explicitSectionName": "農業天然災害救助辦法",
  "directCrossReference": {
    "pdfPage": 293,
    "quote": "__________________________鄉(鎮、市、區)公所(請蓋關防)\n或林業及自然保育署__________分署___________工作站(請蓋關防)\n備註：申請人申請「農業天然災害低利貸款」 ，應於本證明書核發之翌日起30個工作\n日內 ， 檢具本證明書 、 農業天然災害低利貸款申請暨計畫書 ， 向貸款經辦機構\n提出申請。"
  },
  "candidateScopeGroup": "loan:natural-disaster-low-interest-loan",
  "supportingEvidence": [
    "P.292副題直接寫「申貸『農業天然災害低利貸款』專用」。",
    "P.293備註直接申貸同名貸款，並列所需申請暨計畫書。"
  ],
  "opposingEvidence": [
    "主題名與form-023相同，單憑主題名無法判定；本次採專用副題與末頁備註，未採鄰近位置。"
  ],
  "finalStatus": "verified-with-correction",
  "decisionCriterion": "A-form-explicit-loan-name",
  "requiresHumanReview": false
}
```

## 六、Ambiguous Cases

題名所指書表本體；獨立題名的審查表、計畫書、切結書不併入申請書。固定頁面決策來自逐頁視覺核對，不由起頁加N推算。

ambiguous=0；start-only=0；needs-human-review=0。此為Codex第一階段結果，並非Luna或使用者人工結論。

## 七、Search Impact

507 → 507；6筆forms metadata變化；非forms索引0變化。完整 before/after與100組query/scope比較：[search-impact.json](search-impact.json)。

100組比較中，18組結果有metadata相關變化；13組筆數變化。增減僅涉及form-023／027的直接貸款scope及form-028移除非來源題名前綴。

search-core.js、搜尋UI、concepts、intents未修改。intentOnly=0；scope leak=0。

不能宣稱所有排序完全相同：「農業天然災害受災證明書」全站查詢仍為179筆，但既有多樣化排序因兩份表單合法scope修正而改變部分同分結果順序。非書表原始score、evidence、結果集合均不變；僅還原6筆metadata即可重現全部100組baseline結果。

## 八、Source Integrity

{"pdfPages": 359, "pdfSha256": "0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54", "sourceDownloadBitIdentical": true, "frozenOriginalSourceChanged": 0, "presentationChanged": 0, "existingRoutesChanged": 0}

底本、原始文字及既有curation校驗：immutable [forms-baseline.json](forms-baseline.json)；由來源validator與design integrity實際比對。

來源頁影像參照：[page-reference-manifest.json](page-reference-manifest.json)，圖片留在忽略的tmp資料夾，不提交大量圖像。

## 九、Regression

| 項目 | 結果 |
| --- | --- |
| HTML / Sitemap / Canonical | 399 / 399 / 399；既有URL變更0 |
| 原文Evidence / Search index | 359 / 507 |
| Loans / Interpretations / Forms | 23 / 87 / 28 |
| FAQ questions / FAQ groups / Sections | 52 / 4 / 7 |
| Official updates / Coverage / verifiedThrough | 20 / partial / null |
| Disaster Gateway | 原農業金融署官方URL不變；mirror 0 |
| 書表頁實際路由 | 1個HTML上的28個既有fragment targets；未新建28個HTML |

## 十、Tests

| 實際command | 結果 | 日誌 |
| --- | --- | --- |
| `python scripts/build_all.py` | PASS | [log](logs/build-01.txt) |
| `python scripts/test_interpretation_parser.py` | PASS | [log](logs/validation-01.txt) |
| `python scripts/audit_content.py` | PASS | [log](logs/validation-02.txt) |
| `python scripts/validate_display_text.py` | PASS | [log](logs/validation-03.txt) |
| `python scripts/validate_interpretation_metadata.py` | PASS | [log](logs/validation-04.txt) |
| `python scripts/validate_interpretation_decisions.py` | PASS | [log](logs/validation-05.txt) |
| `python scripts/validate_index_quality.py` | PASS | [log](logs/validation-06.txt) |
| `python scripts/validate_navigation_targets.py` | PASS | [log](logs/validation-07.txt) |
| `python scripts/validate_page_rendering.py` | PASS | [log](logs/validation-08.txt) |
| `python scripts/validate_visual_theme.py` | PASS | [log](logs/validation-09.txt) |
| `python scripts/validate_search_experience.py` | PASS | [log](logs/validation-10.txt) |
| `python scripts/validate_ux_structure.py` | PASS | [log](logs/validation-11.txt) |
| `python scripts/validate_official_updates.py` | PASS | [log](logs/validation-12.txt) |
| `python scripts/validate_official_coverage.py` | PASS | [log](logs/validation-13.txt) |
| `python scripts/validate_revision_consistency.py` | PASS | [log](logs/validation-14.txt) |
| `python scripts/validate_disaster_official_gateway.py` | PASS | [log](logs/validation-15.txt) |
| `python scripts/validate_reading_navigation.py` | PASS | [log](logs/validation-16.txt) |
| `python scripts/validate_reference_lookup.py` | PASS | [log](logs/validation-17.txt) |
| `python scripts/validate_official_updates_lookup.py` | PASS | [log](logs/validation-18.txt) |
| `python scripts/validate_forms_source_review.py` | PASS | [log](logs/validation-19.txt) |
| `python scripts/audit_search_precision.py` | PASS | [log](logs/validation-20.txt) |
| `python scripts/audit_task_search_quality.py` | PASS | [log](logs/validation-21.txt) |
| `python scripts/report_source_review_plan.py` | PASS | [log](logs/validation-22.txt) |
| `python scripts/report_official_update_inventory.py` | PASS | [log](logs/validation-23.txt) |
| `python scripts/report_official_coverage.py` | PASS | [log](logs/validation-24.txt) |
| `python scripts/validate_site.py` | PASS | [log](logs/validation-25.txt) |
| `python scripts/validate_forms_source_review.py --write-design-manifest` | PASS | [log](logs/validation-26.txt) |
| `python scripts/design_integrity.py verify reports/forms-review/allowed-forms-design-manifest.json` | PASS | [log](logs/validation-27.txt) |
| `python scripts/audit_forms_source.py report` | PASS | [log](logs/validation-28.txt) |
| `node scripts/test_search_core.cjs` | PASS | [log](logs/validation-29.txt) |
| `node scripts/test_task_search_semantics.cjs` | PASS | [log](logs/validation-30.txt) |
| `node scripts/test_official_updates_lookup.cjs` | PASS | [log](logs/validation-31.txt) |
| `node scripts/benchmark_search_core.cjs` | PASS | [log](logs/validation-32.txt) |
| `node scripts/benchmark_official_updates_lookup.cjs` | PASS | [log](logs/validation-33.txt) |
| `git diff --check` | PASS | [log](logs/validation-34.txt) |
| `python scripts/test_validator_mutations.py` | PASS | [log](logs/mutation-01.txt) |
| `python scripts/test_reference_lookup_mutations.py` | PASS | [log](logs/mutation-02.txt) |
| `python scripts/test_official_updates_lookup_mutations.py` | PASS | [log](logs/mutation-03.txt) |
| `python scripts/test_forms_source_review_mutations.py` | PASS | [log](logs/mutation-04.txt) |
| `python scripts/test_build_reproducibility.py` | PASS | [log](logs/reproducibility-01.txt) |
| `npm ci` | PASS | [log](logs/browser-01.txt) |
| `npm exec -- playwright install chromium` | PASS | [log](logs/browser-02.txt) |
| `npm exec -- playwright test` | PASS | [log](logs/browser-03.txt) |

Mutation：既有70/70 + reference12/12 + official16/16 + forms24/24 = 122/122 caught。

Playwright：既有160項保留 + 新增12項 = 172/172 PASS。正式站驗收尚未執行（未部署）。

## 十一、Files Changed

- `.github/workflows/pages.yml`
- `CHANGELOG.md`
- `README.md`
- `curation/114/forms-source-review.json`
- `data/114/forms.json`
- `data/114/manual.json`
- `data/versions.json`
- `package-lock.json`
- `package.json`
- `scripts/audit_forms_regression.py`
- `scripts/audit_forms_source.py`
- `scripts/build_site.py`
- `scripts/content_model.py`
- `scripts/test_forms_source_review_mutations.py`
- `scripts/test_search_core.cjs`
- `scripts/test_validator_mutations.py`
- `scripts/validate_forms_source_review.py`
- `scripts/validate_official_updates_lookup.py`
- `scripts/validate_search_experience.py`
- `tests/browser/forms-source-review.spec.js`
- `tests/browser/handbook.spec.js`

- `reports/forms-review/`：immutable baseline、28筆報告、來源頁manifest、search impact、限定design manifest、測試結果與已去除私人路徑的日誌。
- `site/`：399個既有HTML版本同步、書表範圍／來源入口及相關貸款頁metadata、6筆搜尋metadata；未新增或刪除route。

### Known Limitations

- 模型來源交叉核對不是人工覆核；Luna獨立覆核仍待執行，未commit或部署。
- 本輪只核對既有28筆書表；不把獨立審查表／計畫書／切結書新增為索引筆數或併入申請書。
- 表格以既有Evidence／原始PDF查閱，不重建表格；未進行359頁全文人工校讀。

## STOP

等待Luna唯讀獨立覆核；未commit、未merge、未push、未開始下一內容覆核階段。
