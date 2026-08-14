# Changelog

## 114.0.0-beta.3.1.1

### Fixed

- 修正 Official Updates 多關鍵詞查詢在正規化時提前移除空白，造成查詢詞邊界消失的問題。
- 多關鍵詞查詢改為保留原始 query 邊界後分詞，再逐詞正規化並採 AND matching。
- 修正 JavaScript lookup 與 Python validator reference implementation 的相同邏輯。

### Added

- 新增非連續多關鍵詞、空白變體與負面 AND matching regression tests。
- 新增多關鍵詞 token boundary mutation tests。

### Preserved

- 20筆 Official Updates、507筆114年度手冊搜尋索引、beta.3.1 文號搜尋與篩選排序。
- partial Coverage、`verifiedThrough = null`、天然災害農業金融署官方Gateway、399個既有HTML routes與359頁Evidence。

## 114.0.0-beta.3.1

### Added

- 新增 browser-side Official Updates 查閱工具，支援關鍵字、文號、貸款類別、更新類型及年份篩選。
- 新增完整文號與去除格式後核心文號查詢，以及可分享、可重新載入的 URL state。
- 新增官方來源入口、114年手冊原貸款入口、lookup Validator、fixtures、Mutation與瀏覽器測試。

### Preserved

- 保留114年度手冊507筆搜尋索引，Official Updates 不混入 handbook evidence layer。
- 保留20筆正式官方更新、partial Coverage、`verifiedThrough = null` 與天然災害官方Gateway政策。

### Limitations

- 本頁僅查詢已完成來源核對的20筆制度／業務更新，不宣稱完整現行法規Coverage。
- 天然災害個別地區／品項公告不建立本站資料集，仍請直接查閱農業金融署官方專區。

## 114.0.0-beta.3.0

### Added

- 新增FAQ實務查閱工具：以固定來源規則建立可追溯逐題資料，支援關鍵字與四組FAQ來源篩選。
- 新增函釋文號／主旨查閱工具，支援完整文號、純數字文號、主旨關鍵字、貸款類別及年份篩選。
- 新增可分享、可重新載入、可使用瀏覽器前進／返回的查詢URL state。
- 每筆查閱結果提供既有Evidence頁與原始PDF起始頁入口。
- 新增FAQ來源結構稽核、查閱資料Validator、Mutation與Playwright回歸測試。

### Preserved

- 507筆114年度手冊全文搜尋索引、beta.2.9閱讀導覽與 `search-core.js`。
- 87筆函釋、4組FAQ來源、399個既有HTML頁面、359頁原始手冊Evidence。
- 20筆官方更新、partial Coverage、官方天然災害Gateway；官方更新不混入本輪查閱結果。

### Limitations

- FAQ逐題資料只在來源文字具固定問題／答案標記時建立；非問題式諮詢專線與書表說明保留於來源頁級查閱。
- 函釋結束頁仍維持既有 `start-only` 狀態，未因查閱工具推算或補寫。

## 114.0.0-beta.2.9

### Added

- 新增貸款頁「本頁快速導覽」，只連至既有原文中可由固定來源標記明確定位的申請資格、用途、額度、期限、利率、應備文件及貸放後管理內容。
- 新增Section頁「本頁內容」，桌機保留側欄、手機使用原生可收合介面。
- 新增可分享、可重新載入且具固定頁首安全間距的頁內Anchor。
- 新增貸款原文頁內上一項／下一項連續閱讀。
- 強化每個貸款原文頁的手冊頁碼與既有Evidence頁入口。
- 新增閱讀導覽完整性Validator、Mutation與瀏覽器回歸測試。

### Changed

- 搜尋結果只在單一來源頁具有唯一、確定的任務對應時加入頁內Anchor；其他結果維持原頁層級URL。
- 版本更新為 `114.0.0-beta.2.9`「章節連續閱讀與條文導覽版」。

### Preserved

- 保留507筆114年度手冊搜尋索引與 beta.2.8 retrieval evidence、Intent、Ranking語意。
- 保留399個既有HTML頁面、359頁原始手冊Evidence、20筆官方更新與天然災害官方Gateway。
- 不修改原始PDF、114年度核心資料、原始業務文字或正式官方資料內容。

## 114.0.0-beta.2.8

### Fixed

- 修正搜尋 Intent 可將沒有直接或相關文字命中的紀錄帶入結果。
- 修正概念命中可能被錯標為直接命中，以及短詞誤觸發完整任務概念。
- 修正 snippet 以未出現在正文的擴展詞定位。

### Changed

- Intent 僅在已有直接、相關或結構化檢索證據後調整排序。
- 搜尋結果以精確文號、直接命中、相關詞命中呈現實際證據。

### Added

- 新增搜尋精準度稽核與 retrieval-evidence synthetic regression。

### Preserved

- 保留507筆114年度手冊搜尋索引、399個HTML URL、359頁原始手冊證據頁、20筆制度與業務官方更新及天然災害公告官方gateway。

## 114.0.0-beta.2.7.2

### Changed

- 天然災害低利貸款之地區、品項及申請期間公告改為直接導向農業金融署官方專區。
- 本站不再逐筆複製、追蹤或統計地方型天然災害低利貸款公告。
- 天然災害貸款頁及相關章節改為提供官方最新公告入口。
- 官方更新資料範圍收斂為制度、規範、函示、FAQ、表單及特殊措施。
- Source review log可記錄因產品政策排除之高頻公告hit。

### Removed

- 移除3筆本地天然災害低利貸款公告資料。
- 移除災害公告decision inventory、validator、online audit與本機篩選程式。
- 移除首頁及各頁面的災害公告本地筆數。

### Fixed

- 修正README數位版本誤寫為114.0.0-beta.2.7.1.1.1。
- 新增數位版本跨檔案一致性驗證。

### Preserved

- 20筆制度與業務官方更新。
- 114年度359頁手冊底本。
- 507筆114手冊搜尋索引。
- 天然災害制度修正、表單、免息及特殊措施資料。

## 114.0.0-beta.2.7.1.1

### Fixed

- 修正樺加沙颱風免息措施漏列「農民組織及農企業天然災害復耕復建貸款」關聯。
- 修正天然災害公告索引在Coverage尚未完整時缺乏明確資料範圍提示。
- 修正官方更新日期metadata重複顯示生效日期。
- 修正部分受理期間以西元日期顯示，未與全站民國年格式一致。
- 修正official-update validator未驗證relatedSectionIds。
- 修正verifiedOn可被null繞過日期驗證。

### Changed

- Source review log明確區分discovery hit與正式candidate。
- Candidate lineage現在可由source review追溯至decision inventory。
- 原discover_official_candidates工具改名為report_source_review_plan，避免誤導為自動Discovery工具。

### Added

- 新增candidate lineage validator規則。
- 新增天然災害公告partial coverage提示。
- 新增relatedSectionIds及verifiedOn mutation regression。

## 114.0.0-beta.2.7.1

### Fixed

- 修正官方來源檢核日期可能超過實際系統性盤點範圍。
- 補強官方更新Candidate discovery，不再以已納入URL驗證取代Coverage驗證。
- 修正文件版本日期可能被誤作發布日期。
- 補強官方URL、日期、受理期間與重複紀錄驗證。

### Added

- 新增天然災害低利貸款公告獨立資料層。
- 新增天然災害低利貸款公告頁。
- 新增四類官方來源逐來源review log。
- 新增Coverage completeness validator。
- 新增disaster announcement validator與online source audit。
- 補列手冊出版後遺漏之正式制度更新。

### Changed

- 首頁分開顯示制度／業務更新與天然災害低利貸款公告數量。
- verifiedThrough改依各指定官方來源實際盤點狀態決定。
- 官方更新主列表不再混入大量地方型天然災害公告。

## 114.0.0-beta.2.7

### Added

- 新增「手冊出版後官方更新」資料層。
- 新增官方更新候選決策與人工核對流程。
- 新增官方更新專頁及類型、年份、貸款篩選。
- 新增114手冊底本與官方更新檢核日期。
- Loan頁新增手冊出版後官方更新入口。
- 共同規定及天然災害Section新增官方更新入口。
- 新增官方來源metadata validator。
- 新增官方來源online audit。
- 新增官方更新維護文件。

### Changed

- 首頁明確區分114年度手冊底本與出版後官方更新。
- FAQ、函釋及書表頁明確標示其114手冊資料範圍。
- 全站搜尋明確標示目前搜尋範圍為114年度手冊。
- 原書完整目錄明確標示不因後續官方更新重新編排。

### Preserved

- 114年度359頁PDF與所有原始內容完全不變。
- 507筆搜尋索引本輪不加入官方更新。
- 23項貸款、87筆函釋、28份書表及4組FAQ原始資料不變。

## 114.0.0-beta.2.6.1

### Fixed

- 修正貸款頁「在本貸款中搜尋」實際預設仍搜尋全手冊。
- 修正Section頁「在本章查規定」實際預設仍搜尋全手冊。
- 修正貸款及章節任務快捷未自動套用目前情境搜尋範圍。
- 修正快捷搜尋完成後鍵盤焦點未移至結果。
- 修正附錄搜尋結果錯誤顯示「查看書表」。
- 統一證據頁「原書完整目錄」用語。

### Changed

- 任務型搜尋加入經來源語料驗證的使用者語言與手冊正式用語映射。
- Loan inline search預設本貸款。
- Section inline search預設本章。
- Global search dialog仍預設全手冊。
- 任務快捷搜尋改為驗證語意相關性，而非只驗證有結果。
- 「貸後管理」依來源實際用語調整為「貸放後管理」。

### Added

- 新增Task Search Semantics來源詞彙文件。
- 新增Task搜尋品質audit。
- 新增Context search與Task semantics瀏覽器回歸測試。

## 114.0.0-beta.2.6

### Changed

- 首頁由PDF導向改為搜尋與使用者任務導向。
- 手機導覽改為精簡Header與可展開選單。
- 「快速索引」顯示名稱改為「依需求找資料」。
- Section頁面由統一page dump改為依資料類型呈現的語意型Hub。
- 貸款頁改為貸款原文、相關函釋、相關書表與來源證據的工作頁。
- 搜尋結果重新以所屬貸款／章節、命中原文及出處為資訊優先級。
- 359個page頁保留為證據層，不再作為主要導航。
- 列印功能移至內容工具列，不再永久浮動。
- 手機僅保留必要的回到頂端浮動操作。

### Added

- 新增「常用查詢」即時搜尋。
- 新增「我想查……」任務型搜尋捷徑。
- 新增navigation-shortcuts.json。
- 新增搜尋結果contextTitle。
- 新增Mobile menu。
- 新增Section與Loan上下文搜尋捷徑。
- 新增搜尋資料載入失敗的瀏覽器回歸測試。
- 新增UX／資訊架構設計文件。

### Fixed

- 修正常用關鍵字按鈕點擊無反應。
- 修正搜尋資料載入失敗時「查看完整目錄」指向不存在路徑。
- 修正手機Header過度占據閱讀空間。
- 修正浮動搜尋與列印工具遮擋手機正文。
- 修正Section頁以大量頁碼作為主要導航。
- 移除測試程式中的本機絕對Node路徑。

## 114.0.0-beta.2.5

### Added

- 新增單一內容歸屬模型，集中管理貸款、原文、函釋、書表及section關係。
- 新增原子化單一建置入口與建置可重現測試。
- 新增預先正規化搜尋資料及搜尋效能benchmark。
- 新增真正DOM與四視口Playwright整合測試。
- 新增15項驗證器突變測試。

### Changed

- Section搜尋改由實際頁面集合推導多scope範圍。
- 搜尋改為先限制scope及type，再進行評分與分散排序。
- 精確標題、標題片語及精確文號使用符合名稱的判定方式。
- Unicode位置映射改為UTF-16及grapheme安全模型。
- 搜尋片段改採固定長度最佳命中視窗。
- FAQ改用正確搜尋scope。
- 正式建置統一改用scripts/build_all.py。

### Fixed

- 修正loan-programs及natural-disaster-rules本章搜尋0筆。
- 修正emoji及代理對後方命中標記錯位。
- 修正搜尋片段可能延伸至整頁全文。
- 修正搜尋索引出現「手冊頁 None」。
- 修正builder執行順序會遺失搜尋索引。
- 修正搜尋效能可能達數秒以上。
- 修正驗證器無法攔截部分scope、fragment、列印及Unicode錯誤。

## 114.0.0-beta.2.3

### Changed

- 全站改為明亮、清新、專業的青綠／薄荷／湖水藍視覺系統。
- 保留搜尋、目錄、索引、頁面路徑與既有內容；本版僅為 Visual refresh only。
- 改善首頁搜尋焦點、閱讀頁留白、導覽可讀性、卡片層級、列印與響應式樣式。

## 114.0.0-beta.2.2

### Changed

- 逐筆比對8筆未決函釋候選的來源頁面，新增持久化判定資料。
- 函釋候選分類擴充為引用、續頁、變體、誤判及未決；函釋頁改為依共同規定及貸款方案分組。
- 完整目錄與貸款詳情頁改用函釋分組深層連結；導覽「FAQ」統一為「常見問答」。
- 首頁書表狀態改為「未分類候選」及「逐頁覆核」分列。

### Fixed

- 修正「農業天然災害救助辦法」完整目錄項目無法點擊。
- 修正函釋入口只能開啟函釋總表與候選決策無法在重新擷取後保存。

## 114.0.0-beta.2.1

### Fixed

- 修正函釋文號誤將日期尾字「日」納入機關字號。
- 修正已知有日期之函釋解析與公開搜尋文號。
- 修正函釋來源索引與候選庫重複計數，區分 promoted、duplicate 與真正 pending。
- 修正書表候選庫被誤稱為全部待覆核，改為來源索引、排除與待覆核分類。
- 補齊 359 頁頁碼映射與 42 個已檢查錨點狀態。

### Added

- 新增嚴格函釋標頭回歸測試與來源中繼資料驗證。
- 首頁、版本說明與來源索引明示 source-indexed、candidate inventory 與人工覆核界線。

## 114.0.0-beta.2

- 忠實重建 PDF 第 1–2 頁原書目錄，另立讀者快速索引。
- 將函釋與書表分為確認索引、待覆核候選與書表排除紀錄。
- 新增 42 個印刷頁碼抽查錨點及第一輪內容稽核紀錄。
- 套用只變更空白的確定性顯示文字整理，新增顯示完整性與索引品質驗證。
- 公開頁面標示 Beta，分開函釋與 FAQ 導覽，建置前清除舊站輸出。

## Unreleased

### Added

- 建立114年度政策性農業專案貸款業務手冊數位閱讀版
- 納入359頁原始PDF與SHA-256驗證
- 建立完整目錄與逐頁閱讀
- 建立瀏覽器端全文搜尋
- 建立23項貸款索引
- 建立函釋、FAQ、附件與表單索引
- 建立GitHub Pages自動部署
- 建立版本與人工覆核機制
## 114.0.0-beta.2.4

### Added

- 新增全站「搜尋手冊」原生對話視窗、Ctrl+K／Command+K、類型篩選與本章／全手冊範圍切換。
- 新增瀏覽器端搜尋概念詞彙、意圖排序、載入更多與安全命中標示。
- 新增浮動搜尋、列印本章及回到頂端工具。
- 新增搜尋體驗驗證器與技術文件；首頁快速入口新增農業天然災害低利貸款。

### Changed

- 搜尋改為確定性多詞加權排序，首頁與搜尋視窗共用同一核心。
- 搜尋索引維持507筆並補充 headings、scope 與結果 metadata。
- 瀏覽器 theme-color 同步為 `#286b57`。

### Fixed

- 修正原文結果可能淹沒貸款、函釋及書表結果的排序問題。
- 修正搜尋片段安全標示與長頁快速回頂端、章節列印入口。
## 114.0.0-beta.2.4.1

### 搜尋範圍與片段精準度校正

- 為搜尋索引補充直接 `scope` 與業務群組 `scopeGroup`，讓本貸款搜尋涵蓋貸款索引、原文、函釋及書表。
- 抽離可由瀏覽器與 Node 共用的搜尋核心，加入正規化位置映射與安全片段標記。
- 改善確定性分散排序、本章無結果時改查全手冊、列印按鈕名稱及650px回頂端門檻。
- 新增搜尋核心 Node 回歸測試與 scope／位置映射驗證。
