# FAQ source structure audit

This report is generated from the four ranges declared by `data/114/faq.json` and the existing `data/114/pages.json` text layer. It does not rewrite source wording.

- Groups: 4
- Source pages: 35
- Deterministic question-level records: 52
- Page-level/start-only fallback records: 0
- Ambiguous cases: 0
- Duplicate IDs: 0
- Source boundary errors: 0

## Groups

| FAQ group | PDF pages | detected markers | question-level | fallback | ambiguous |
|---|---:|---:|---:|---:|---:|
| `faq-112-12` | 315–325 | 9 | 9 | 0 | 0 |

### 112年12月專案農貸增修規定（自113年1月1日施行）常見問答

- Printed pages: 313–323
- Question labels: 一, 二, 三, 四, 五, 六, 七, 八, 九
- Missing numeric labels among promoted candidates: none
- False-positive risk: numbered table rows and numbered non-question headings are excluded unless an explicit question or answer marker is present

| `faq-113-08` | 326–334 | 12 | 12 | 0 | 0 |

### 113年8月專案農貸增修規定（自113年8月20日施行）常見問題

- Printed pages: 324–332
- Question labels: 一, 二, 三, 四, 五, 六, 七, 八, 九, 十, 十一, 十二
- Missing numeric labels among promoted candidates: none
- False-positive risk: numbered table rows and numbered non-question headings are excluded unless an explicit question or answer marker is present

| `faq-114-10` | 335–339 | 7 | 7 | 0 | 0 |

### 114年10月專案農貸增修規定（自114年10月10日施行）常見問答

- Printed pages: 333–337
- Question labels: 一, 二, 三, 四, 五, 六, 七
- Missing numeric labels among promoted candidates: none
- False-positive risk: numbered table rows and numbered non-question headings are excluded unless an explicit question or answer marker is present

| `faq-young-farmer-114-10` | 340–349 | 24 | 24 | 0 | 0 |

### 青壯年農民從農貸款增修規定（114年10月更新）常見問答

- Printed pages: 338–347
- Question labels: 一, 二, 三, 四, 五, 六, 七, 八, 九, 十, 十一, 十二, 十三, 十四, 十五, 十六, 十七, 十八, 十九, 二十, 二十一, 二十二, 二十三, 二十四
- Missing numeric labels among promoted candidates: none
- False-positive risk: numbered table rows and numbered non-question headings are excluded unless an explicit question or answer marker is present

## Boundary rule

A numbered marker is promoted only when the source segment contains an explicit `答` marker or a question punctuation before the next numbered marker. Table rows and non-question headings therefore remain outside the question-level model. Answers are bounded by the next promoted question or an explicit FAQ section-break heading; no end page is inferred from a later document.
