#!/usr/bin/env python3
"""Extract the 114 handbook text layer and source indexes without OCR."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "source" / "policy-agri-loan-handbook-114.pdf"
DATA = ROOT / "data" / "114"
CURATION = ROOT / "curation" / "114" / "interpretation-candidate-decisions.json"
EXPECTED_PAGES = 359
VERSION = "114"
SHA256 = "0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54"
FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def normalize_search(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"日\s+(?=農授金字)", "日§", text)
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    return re.sub(r"\s+", " ", text).replace("§", " ").strip()


def display_text(raw: str, printed: int | None) -> str:
    lines = raw.replace("\r", "\n").splitlines()
    if printed is not None:
        for index in range(len(lines) - 1, max(-1, len(lines) - 7), -1):
            value = unicodedata.normalize("NFKC", lines[index]).translate(FULLWIDTH_DIGITS)
            if re.sub(r"\s+", "", value) == str(printed):
                del lines[index]
                break
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    # Separate a date from the following document number for faithful readable
    # layout; this does not alter either token or the source PDF.
    return re.sub(r"日(?=農授金字)", "日 ", "\n".join(line.rstrip() for line in lines))


LOANS = [
    ("farm-machinery-loan", "農機貸款", "政策性農業專案貸款", 94, 99, True),
    ("agri-food-business-loan", "輔導農糧業經營貸款", "政策性農業專案貸款", 100, 109, True),
    ("fishery-business-loan", "輔導漁業經營貸款", "政策性農業專案貸款", 110, 119, True),
    ("livestock-poultry-loan", "提升畜禽產業經營貸款", "政策性農業專案貸款", 120, 145, True),
    ("farmer-production-group-loan", "農民經營及產銷班貸款", "政策性農業專案貸款", 146, 157, True),
    ("agri-tech-park-loan", "農業科技園區進駐業者優惠貸款", "政策性農業專案貸款", 158, 164, True),
    ("hillside-conservation-loan", "山坡地保育利用貸款", "政策性農業專案貸款", 165, 169, False),
    ("farm-household-loan", "農家綜合貸款", "政策性農業專案貸款", 170, 177, True),
    ("association-development-loan", "農漁會事業發展貸款", "政策性農業專案貸款", 178, 184, True),
    ("afforestation-loan", "造林貸款", "政策性農業專案貸款", 185, 196, True),
    ("small-landlord-professional-farmer-loan", "小地主大專業農貸款", "政策性農業專案貸款", 197, 202, False),
    ("agri-energy-saving-loan", "農業節能減碳貸款", "政策性農業專案貸款", 203, 208, True),
    ("young-farmer-loan", "青壯年農民從農貸款", "政策性農業專案貸款", 209, 221, True),
    ("leisure-farm-loan", "休閒農場貸款", "政策性農業專案貸款", 222, 227, False),
    ("agri-organization-enterprise-innovation-loan", "農民組織及農企業產銷經營及研發創新貸款", "政策性農業專案貸款", 228, 241, True),
    ("agri-organization-disaster-recovery-loan", "農民組織及農企業天然災害復耕復建貸款", "政策性農業專案貸款", 242, 250, False),
    ("agricultural-insurance-loan", "農業保險貸款", "政策性農業專案貸款", 251, 253, False),
    ("farmer-relief-loan", "農民紓困貸款", "政策性農業專案貸款", 254, 258, False),
    ("farmland-purchase-loan", "擴大家庭農場經營規模協助農民購買耕地貸款", "政策性農業專案貸款", 259, 269, True),
    ("natural-disaster-low-interest-loan", "農業天然災害低利貸款", "政策性農業專案貸款", 270, 299, True),
    ("agricultural-rooting-loan", "農業紮根貸款", "全國農業金庫貸款", 300, 305, False),
    ("rice-purchase-working-capital-loan", "稻穀收購產銷調節週轉金貸款", "全國農業金庫貸款", 306, 307, False),
    ("brackish-water-fishery-loan", "輔導鹹水漁業改善經營貸款", "全國農業金庫貸款", 308, 308, False),
]

SECTIONS = [
    ("policy-loan-regulations", "辦理政策性農業專案貸款辦法", 1, 29),
    ("agricultural-development-fund-rules", "農業發展基金貸款作業規範及相關函釋", 30, 93),
    *[(slug, title, start, end) for slug, title, _category, start, end, _has in LOANS],
    ("bank-operating-rules-appendices", "全國農業金庫作業規範附錄", 309, 312),
    ("amendment-faq", "政策性農業專案貸款增修正規定常見問題", 313, 347),
    ("attachments", "附件", 348, 357),
]

INTERPRETATION_RANGES = [
    ("農業發展基金貸款共同規定", 45, 93),
    ("農機貸款", 99, 99), ("輔導農糧業經營貸款", 107, 109),
    ("輔導漁業經營貸款", 119, 119), ("提升畜禽產業經營貸款", 142, 145),
    ("農民經營及產銷班貸款", 156, 157), ("農業科技園區進駐業者優惠貸款", 164, 164),
    ("農家綜合貸款", 175, 177), ("農漁會事業發展貸款", 183, 184),
    ("造林貸款", 196, 196), ("農業節能減碳貸款", 208, 208),
    ("青壯年農民從農貸款", 219, 221),
    ("農民組織及農企業產銷經營及研發創新貸款", 240, 241),
    ("擴大家庭農場經營規模協助農民購買耕地貸款", 267, 269),
    ("農業天然災害低利貸款", 297, 299),
]

FAQ = [
    ("faq-112-12", "112年12月專案農貸增修規定（自113年1月1日施行）常見問答", 313, 323),
    ("faq-113-08", "113年8月專案農貸增修規定（自113年8月20日施行）常見問題", 324, 332),
    ("faq-114-10", "114年10月專案農貸增修規定（自114年10月10日施行）常見問答", 333, 337),
    ("faq-young-farmer-114-10", "青壯年農民從農貸款增修規定（114年10月更新）常見問答", 338, 347),
]

APPENDICES = [
    ("appendix-1", "全國農業金庫辦理農會漁會信用部資金融通作業規範", 309, 310, "附錄"),
    ("appendix-2", "全國農業金庫辦理農會漁會信用部一般性或季節性週轉資金融通注意事項", 311, 312, "附錄"),
    ("appendix-3", "政策性農業專案貸款增修正規定常見問題（QA）", 313, 347, "附錄"),
    ("attachment-1", "休閒農業輔導管理辦法", 348, 351, "附件"),
    ("attachment-2", "中小企業認定標準", 352, 352, "附件"),
    ("attachment-3", "雞蛋友善生產系統定義及指南", 353, 357, "附件"),
]

# Faithful transcription of the two printed TOC pages.  The hierarchy and wording
# intentionally follow the source; the reader-oriented shortcuts live separately
# in quick-index.json.
TOC_ROWS = [
    (1, "part-1", "壹、政策性農業專案貸款", None, "part"),
    (2, "policy-loan-regulations", "一、辦理政策性農業專案貸款辦法", 1, "section"),
    (2, "fund-rules", "二、農業發展基金貸款相關規定及函釋", None, "section"),
    (3, "fund-operating-rules", "（一）農業發展基金貸款作業規範", 30, "rule"),
    (4, "fund-operating-rules-interpretations", "◎相關函釋", 45, "interpretation"),
    (3, "loan-program-rules", "（二）各項貸款規定", None, "section"),
    (4, "farm-machinery-loan", "1. 農機貸款要點", 94, "loan"),
    (4, "farm-machinery-loan-interpretations", "◎農機貸款相關函釋", 99, "interpretation"),
    (4, "agri-food-business-loan", "2. 輔導農糧業經營貸款要點", 100, "loan"),
    (4, "agri-food-business-loan-interpretations", "◎輔導農糧業經營貸款相關函釋", 107, "interpretation"),
    (4, "fishery-business-loan", "3. 輔導漁業經營貸款要點", 110, "loan"),
    (4, "fishery-business-loan-interpretations", "◎輔導漁業經營貸款相關函釋", 119, "interpretation"),
    (4, "livestock-poultry-loan", "4. 提升畜禽產業經營貸款要點", 120, "loan"),
    (4, "livestock-poultry-loan-interpretations", "◎提升畜禽產業經營貸款相關函釋", 142, "interpretation"),
    (4, "farmer-production-group-loan", "5. 農民經營及產銷班貸款要點", 146, "loan"),
    (4, "farmer-production-group-loan-interpretations", "◎農民經營及產銷班貸款相關函釋", 156, "interpretation"),
    (4, "agri-tech-park-loan", "6. 農業科技園區進駐業者優惠貸款要點", 158, "loan"),
    (4, "agri-tech-park-loan-interpretations", "◎農業科技園區進駐業者優惠貸款相關函釋", 164, "interpretation"),
    (4, "hillside-conservation-loan", "7. 山坡地保育利用貸款要點", 165, "loan"),
    (4, "farm-household-loan", "8. 農家綜合貸款要點", 170, "loan"),
    (4, "farm-household-loan-interpretations", "◎農家綜合貸款相關函釋", 175, "interpretation"),
    (4, "association-development-loan", "9. 農漁會事業發展貸款要點", 178, "loan"),
    (4, "association-development-loan-interpretations", "◎農漁會事業發展貸款相關函釋", 183, "interpretation"),
    (4, "afforestation-loan", "10. 造林貸款要點", 185, "loan"),
    (4, "afforestation-loan-interpretations", "◎造林貸款相關函釋", 196, "interpretation"),
    (4, "small-landlord-professional-farmer-loan", "11. 小地主大專業農貸款要點", 197, "loan"),
    (4, "agri-energy-saving-loan", "12. 農業節能減碳貸款要點", 203, "loan"),
    (4, "agri-energy-saving-loan-interpretations", "◎農業節能減碳貸款相關函釋", 208, "interpretation"),
    (4, "young-farmer-loan", "13. 青壯年農民從農貸款要點", 209, "loan"),
    (4, "young-farmer-loan-interpretations", "◎青壯年農民從農貸款相關函釋", 219, "interpretation"),
    (4, "leisure-farm-loan", "14. 休閒農場貸款要點", 222, "loan"),
    (4, "agri-organization-enterprise-innovation-loan", "15. 農民組織及農企業產銷經營及研發創新貸款要點", 228, "loan"),
    (4, "agri-organization-enterprise-innovation-loan-interpretations", "◎農民組織及農企業產銷經營及研發創新貸款相關函釋", 240, "interpretation"),
    (4, "agri-organization-disaster-recovery-loan", "16. 農民組織及農企業天然災害復耕復建貸款要點", 242, "loan"),
    (4, "agricultural-insurance-loan", "17. 農業保險貸款要點", 251, "loan"),
    (4, "farmer-relief-loan", "18. 農民紓困貸款要點", 254, "loan"),
    (4, "farmland-purchase-loan", "19. 擴大家庭農場經營規模協助農民購買耕地貸款辦法", 259, "loan"),
    (4, "farmland-purchase-loan-interpretations", "◎擴大家庭農場經營規模協助農民購買耕地貸款相關函釋", 267, "interpretation"),
    (3, "natural-disaster-rules", "（三）農業天然災害救助辦法", 270, "rule"),
    (4, "natural-disaster-low-interest-loan-interpretations", "◎農業天然災害救助低利貸款相關函釋", 297, "interpretation"),
    (1, "part-2", "貳、全國農業金庫貸款", None, "part"),
    (2, "agricultural-rooting-loan", "一、農業紮根貸款作業要點", 300, "loan"),
    (2, "rice-purchase-working-capital-loan", "二、稻穀收購產銷調節週轉金貸款作業要點", 306, "loan"),
    (2, "brackish-water-fishery-loan", "三、輔導鹹水漁業改善經營貸款作業要點", 308, "loan"),
    (1, "appendix-1", "附錄一、全國農業金庫辦理農會漁會信用部資金融通作業規範", 309, "appendix"),
    (1, "appendix-2", "附錄二、全國農業金庫辦理農會漁會信用部一般性或季節性週轉資金融通注意事項", 311, "appendix"),
    (1, "appendix-3", "附錄三、政策性農業專案貸款增修正規定常見問題（QA）", None, "appendix"),
    (2, "faq-112-12", "112年12月專案農貸增修規定（自113年1月1日施行）常見問答", 313, "faq"),
    (2, "faq-113-08", "113年8月專案農貸增修規定（自113年8月20日施行）常見問題", 324, "faq"),
    (2, "faq-114-10", "114年10月專案農貸增修規定（自114年10月10日施行）常見問答", 333, "faq"),
    (2, "faq-young-farmer-114-10", "「青壯年農民從農貸款」增修規定（114年10月更新）常見問答", 338, "faq"),
    (1, "attachment-1", "附件一、休閒農業輔導管理辦法", 348, "attachment"),
    (1, "attachment-2", "附件二、中小企業認定標準", 352, "attachment"),
    (1, "attachment-3", "附件三、雞蛋友善生產系統定義及指南", 353, "attachment"),
]

FORM_WHITELIST = {
    38: "農業發展基金貸款利息差額補貼申請書",
    41: "專案農貸額度控管期限延長申請書",
    51: "專案農貸延期還款案件申請書（甲式）",
    52: "專案農貸延期還款案件申請書（乙式）",
    53: "專案農貸延期還款案件審核表",
    97: "農機貸款申請書",
    104: "輔導農糧業經營貸款申請書",
    115: "輔導漁業經營貸款申請書",
    126: "提升畜禽產業經營貸款（除污染防治類外）申請書",
    129: "提升畜禽產業經營貸款申請書",
    150: "農民經營及產銷班貸款申請書",
    161: "農業科技園區進駐業者優惠貸款申請書",
    172: "農家綜合貸款申請書",
    181: "農漁會事業發展貸款申請書",
    188: "造林貸款申請書",
    191: "造林貸款土地勘查申請書",
    200: "小地主大專業農貸款申請書",
    205: "農業節能減碳貸款申請書",
    213: "青壯年農民從農貸款申請書",
    225: "休閒農場貸款申請書",
    232: "農民組織及農企業產銷經營及研發創新貸款申請書",
    245: "農民組織及農企業天然災害復耕復建貸款申請書",
    249: "農業天然災害受災證明書（復耕復建貸款用）",
    252: "農業保險貸款申請書",
    256: "農民紓困貸款申請書",
    263: "擴大家庭農場經營規模協助農民購買耕地貸款申請書",
    290: "農業天然災害受災證明書",
    303: "農業紮根貸款額度動用申請書",
}


def build_toc() -> dict:
    items = []
    for order, (level, item_id, title, printed, kind) in enumerate(TOC_ROWS, 1):
        items.append({
            "id": item_id, "order": order, "level": level, "title": title,
            "kind": kind, "printedPage": printed,
            "pdfPage": printed + 2 if printed is not None else None,
        })
    return {
        "version": VERSION, "title": "114年度政策性農業專案貸款業務手冊",
        "sourcePdfPages": [1, 2], "structure": "faithful-flat-hierarchy", "items": items,
    }


def build_quick_index(loan_programs: list[dict]) -> dict:
    return {
        "version": VERSION, "title": "快速索引", "purpose": "依讀者常用入口重新整理，不取代原書目錄。",
        "groups": [
            {"id": "core-rules", "title": "共同規定", "items": [
                {"id": "policy-loan-regulations", "title": "辦理政策性農業專案貸款辦法", "printedPage": 1},
                {"id": "fund-operating-rules", "title": "農業發展基金貸款作業規範", "printedPage": 30},
            ]},
            {"id": "loan-programs", "title": "貸款方案", "items": [
                {"id": item["id"], "title": item["title"], "printedPage": item["sourceStartPage"]}
                for item in loan_programs
            ]},
            {"id": "reference", "title": "函釋、FAQ 與附件", "items": [
                {"id": "interpretations", "title": "函釋索引", "printedPage": 45},
                {"id": "faq", "title": "常見問題", "printedPage": 313},
                {"id": "forms", "title": "書表索引", "printedPage": 38},
                {"id": "appendices", "title": "附錄與附件", "printedPage": 309},
            ]},
        ],
    }


HEADER_DATE = re.compile(r"(?:中華民國)?\s*(?P<year>[0-9０-９]+)\s*年\s*(?P<month>[0-9０-９]+)\s*月\s*(?P<day>[0-9０-９]+)\s*日")
STRICT_DOCUMENT_NUMBER = re.compile(r"(?P<number>[\u3400-\u9fffA-Za-z]+字第[A-Za-z0-9]+號)")
# Candidate detection deliberately starts at a document-number agency prefix,
# never at the preceding date's final 「日」.
DOCUMENT_REFERENCE = re.compile(r"(?:農授(?:林務)?|農金(?:三)?|農牧)字第?\s*[A-Za-z0-9０-９\s]+號")
HEADER_ISSUER = re.compile(r"^(?:行政院農業委員會(?:農業金融局)?|農業部)")


def canonicalize_document_number(value: str) -> str:
    """Normalize layout only; never infer or repair an agency document number."""
    normalized = unicodedata.normalize("NFKC", value)
    normalized = re.sub(r"\s+", "", normalized)
    return re.sub(r"(?:函|公告)$", "", normalized)


def parse_interpretation_header(header_text: str) -> dict | None:
    """Strictly parse an entire source header and reject invalid leading text."""
    compact = re.sub(r"\s+", "", unicodedata.normalize("NFKC", header_text))
    if compact.startswith("【") and compact.endswith("】"):
        compact = compact[1:-1]
    date_match = HEADER_DATE.search(compact)
    if not date_match:
        return None
    date = f"{int(date_match.group('year'))}年{int(date_match.group('month'))}月{int(date_match.group('day'))}日"
    remainder = compact[:date_match.start()] + compact[date_match.end():]
    remainder = re.sub(r"(?:函|公告)$", "", remainder)
    # The issuing authority is header context, not part of the agency document number.
    remainder = HEADER_ISSUER.sub("", remainder)
    number_match = STRICT_DOCUMENT_NUMBER.fullmatch(remainder)
    if not number_match:
        return None
    document_number = canonicalize_document_number(number_match.group("number"))
    invalid = (not document_number.endswith("號") or "字第" not in document_number or document_number.startswith("日") or
               any(token in document_number for token in ("年", "月", "日", "中華民國", "(", ")", "（", "）")))
    if invalid:
        return None
    return {"sourceHeader": header_text, "date": date, "documentNumber": document_number,
            "canonicalDocumentNumber": canonicalize_document_number(document_number)}


def subject_from_block(body: str) -> str | None:
    match = re.search(r"主旨\s*[：:]\s*(.+?)(?=\n(?:說明|依據|公告事項)\s*[：:]|\n函令摘要|$)", body, re.S)
    return normalize_search(match.group(1))[:240] if match else None


def extract_source_indexed_interpretations(pages: list[dict]) -> list[dict]:
    records = []
    header_pattern = re.compile(r"【[^】]+】")
    for loan_title, start, end in INTERPRETATION_RANGES:
        for printed in range(start, end + 1):
            text = pages[printed + 1]["rawText"]
            matches = list(header_pattern.finditer(text))
            for index, match in enumerate(matches):
                parsed = parse_interpretation_header(match.group(0))
                block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                title = subject_from_block(text[match.end():block_end])
                if not parsed or not title:
                    continue
                records.append({
                    "id": f"interpretation-{len(records)+1:03d}", "title": title, **parsed,
                    "loanProgram": loan_title, "printedPageStart": printed, "printedPageEnd": None,
                    "pdfPageStart": printed + 2, "pdfPageEnd": None, "rangeStatus": "start-only",
                    "originalUrl": f"../../downloads/policy-agri-loan-handbook-114.pdf#page={printed+2}",
                    "verificationStatus": "source-indexed", "indexBasis": "strict-header-date-number-subject",
                })
    return records


def build_source_indexed_forms(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    forms, exclusions = [], []
    candidate_pages = {item["printedPage"] for item in candidates}
    for printed, title in FORM_WHITELIST.items():
        if printed not in candidate_pages:
            raise RuntimeError(f"whitelisted form page missing from candidates: {printed}")
        forms.append({
            "id": f"form-{len(forms)+1:03d}", "title": title,
            "printedPageStart": printed, "printedPageEnd": printed,
            "pdfPageStart": printed + 2, "pdfPageEnd": printed + 2,
            "kind": "form", "originalUrl": f"../../downloads/policy-agri-loan-handbook-114.pdf#page={printed+2}",
            "verificationStatus": "source-indexed", "indexBasis": "explicit-source-page-list",
        })
    source_by_page = {item["printedPageStart"]: item["id"] for item in forms}
    for item in candidates:
        if item["printedPage"] in source_by_page:
            item.update({"disposition": "promoted-to-source-index", "linkedFormId": source_by_page[item["printedPage"]], "exclusionId": None})
        else:
            exclusion_id = f"form-exclusion-{len(exclusions)+1:03d}"
            item.update({"disposition": "excluded", "linkedFormId": None, "exclusionId": exclusion_id})
            exclusions.append({
                "id": exclusion_id, "sourceCandidateId": item["id"], "title": item["title"],
                "printedPage": item["printedPage"], "pdfPage": item["pdfPage"], "originalUrl": item["originalUrl"],
                "verificationStatus": "excluded", "exclusionReason": "正文提及、標題殘缺或位於 FAQ，未能確認為獨立書表起始頁。",
            })
    return forms, exclusions


def section_for(printed: int | None) -> tuple[str, str]:
    if printed is None:
        return ("front-matter", "目錄")
    for slug, title, start, end in SECTIONS:
        if start <= printed <= end:
            return slug, title
    return ("unassigned", "待人工覆核")


def extract_interpretation_candidates(pages: list[dict], sources: list[dict]) -> list[dict]:
    """Retain automatic detections, while separating promoted, duplicate and pending records."""
    raw: list[dict] = []
    for source in sources:
        raw.append({
            "title": source["title"], "documentNumber": source["documentNumber"], "date": source["date"],
            "loanProgram": source["loanProgram"], "printedPage": source["printedPageStart"],
            "pdfPage": source["pdfPageStart"], "originalUrl": source["originalUrl"],
        })
    for loan_title, start, end in INTERPRETATION_RANGES:
        for printed in range(start, end + 1):
            text = pages[printed + 1]["rawText"]
            title = subject_from_block(text) or f"{loan_title}相關函釋"
            for value in DOCUMENT_REFERENCE.findall(text):
                raw.append({
                    "title": title, "documentNumber": canonicalize_document_number(value), "date": None,
                    "loanProgram": loan_title, "printedPage": printed, "pdfPage": printed + 2,
                    "originalUrl": f"../../downloads/policy-agri-loan-handbook-114.pdf#page={printed+2}",
                })
    source_lookup = {(item["canonicalDocumentNumber"], item["printedPageStart"]): item["id"] for item in sources}
    seen_keys: dict[tuple[str, int, str], str] = {}
    records = []
    for raw_item in raw:
        canonical = canonicalize_document_number(raw_item["documentNumber"])
        subject = normalize_search(raw_item["title"])
        key = (canonical, raw_item["printedPage"], subject)
        item = {
            "id": f"interpretation-candidate-{len(records)+1:03d}", **raw_item,
            "canonicalDocumentNumber": canonical,
            "candidateKey": "|".join((canonical, str(raw_item["printedPage"]), subject)),
            "linkedInterpretationId": None, "duplicateOf": None, "reviewReason": None,
            "verificationStatus": "automatically-detected",
        }
        if key in seen_keys:
            item.update({"disposition": "duplicate-detection", "duplicateOf": seen_keys[key],
                         "reviewReason": "同頁、同正規化文號及等價主旨的重複偵測。"})
        elif (canonical, raw_item["printedPage"]) in source_lookup:
            item.update({"disposition": "promoted-to-source-index",
                         "linkedInterpretationId": source_lookup[(canonical, raw_item["printedPage"])],
                         "reviewReason": "與嚴格標頭來源索引的文號及起始頁一致。"})
            seen_keys[key] = item["id"]
        else:
            item.update({"disposition": "pending-review",
                         "reviewReason": "無法安全判定為嚴格標頭來源索引或確定重複。"})
            seen_keys[key] = item["id"]
        records.append(item)
    decisions = json.loads(CURATION.read_text(encoding="utf-8"))
    by_key: dict[str, list[dict]] = {}
    for item in records:
        by_key.setdefault(item["candidateKey"], []).append(item)
    for decision in decisions:
        matches = by_key.get(decision["candidateKey"], [])
        if len(matches) != 1:
            raise RuntimeError(f"curation candidateKey must resolve exactly once: {decision['candidateKey']}")
        item = matches[0]
        if (item["documentNumber"], item["printedPage"], item["pdfPage"]) != (decision["documentNumber"], decision["printedPage"], decision["pdfPage"]):
            raise RuntimeError(f"curation metadata mismatch: {decision['candidateKey']}")
        item.update({"disposition": decision["decision"], "decision": decision["decision"],
                     "decisionBasis": decision["decisionBasis"], "evidencePages": decision["evidencePages"],
                     "linkedInterpretationId": decision.get("linkedInterpretationId"),
                     "linkedCandidateKey": decision.get("linkedCandidateKey"),
                     "reviewStatus": decision["reviewStatus"], "reviewReason": decision["notes"]})
    for item in records:
        item.setdefault("decision", item["disposition"])
        item.setdefault("decisionBasis", "automatic-candidate-classification")
        item.setdefault("evidencePages", [])
        item.setdefault("linkedCandidateKey", None)
        item.setdefault("reviewStatus", "automatically-detected")
    return records


def extract_forms(pages: list[dict]) -> list[dict]:
    forms: list[dict] = []
    keywords = ("申請書", "審核表", "查驗紀錄", "切結書", "檢核表", "證明書", "調查表")
    seen: set[tuple[str, int]] = set()
    for page in pages:
        printed = page["printedPage"]
        if printed is None:
            continue
        for line in page["rawText"].splitlines():
            title = normalize_search(line)
            if not (5 <= len(title) <= 60 and any(word in title for word in keywords)):
                continue
            title = re.sub(r"^[一二三四五六七八九十、.．()（）\d\s]+", "", title).strip()
            if any(token in title for token in ("應", "檢具", "提出", "已檢", "立切結", "確認簽章", "函令摘要", "主旨", "□")):
                continue
            if title.count("，") + title.count(",") + title.count("；") > 0:
                continue
            key = (title, printed)
            if len(title) < 5 or key in seen:
                continue
            seen.add(key)
            forms.append({
                "id": f"form-{len(forms)+1:03d}", "title": title,
                "printedPage": printed, "pdfPage": page["pdfPage"],
                "originalUrl": f"../../downloads/policy-agri-loan-handbook-114.pdf#page={page['pdfPage']}",
                "verificationStatus": "automatically-extracted",
            })
    return forms


def main() -> int:
    if not PDF.is_file():
        print(f"ERROR: missing source PDF: {PDF}", file=sys.stderr)
        return 1
    if digest(PDF) != SHA256:
        print("ERROR: unexpected source PDF SHA-256", file=sys.stderr)
        return 1
    reader = PdfReader(str(PDF))
    if len(reader.pages) != EXPECTED_PAGES:
        print(f"ERROR: expected {EXPECTED_PAGES} pages, found {len(reader.pages)}", file=sys.stderr)
        return 1
    raw_pages = [page.extract_text() or "" for page in reader.pages]
    anchor_pages = sorted(set([3, 359, *range(12, 359, 10), 32, 47, 96, 211, 272, 302, 335, 350]))
    anchors = {pdf_page: pdf_page - 2 for pdf_page in anchor_pages}
    failed = []
    for pdf_page, printed in anchors.items():
        tail = [normalize_search(line) for line in raw_pages[pdf_page - 1].splitlines()[-8:]]
        if str(printed) not in tail:
            failed.append((pdf_page, printed, tail))
    if failed:
        print(f"ERROR: printed-page anchor validation failed: {failed}", file=sys.stderr)
        return 1

    pages: list[dict] = []
    for pdf_page, raw in enumerate(raw_pages, 1):
        printed = pdf_page - 2 if pdf_page >= 3 else None
        cleaned = display_text(raw, printed)
        section_id, section_title = section_for(printed)
        has_text = bool(cleaned.strip())
        pages.append({
            "pdfPage": pdf_page, "printedPage": printed,
            "chapterId": section_id, "sectionId": section_id,
            "title": section_title if printed is not None else f"目錄第{pdf_page}頁",
            "rawText": cleaned, "searchText": normalize_search(cleaned),
            "hasTextLayer": has_text, "renderMode": "text" if has_text else "preview",
            "version": VERSION,
        })

    loan_programs = []
    for sequence, (slug, title, category, start, end, has_interpretations) in enumerate(LOANS, 1):
        loan_programs.append({
            "id": slug, "title": title, "sequence": sequence, "category": category,
            "sourceStartPage": start, "sourceEndPage": end,
            "pdfStartPage": start + 2, "pdfEndPage": end + 2,
            "hasInterpretations": has_interpretations,
            "detailUrl": f"loans/{slug}/index.html", "verificationStatus": "source-indexed",
        })

    toc = build_toc()
    quick_index = build_quick_index(loan_programs)
    faq = [{"id": slug, "title": title, "printedPageStart": start, "printedPageEnd": end,
            "pdfPageStart": start+2, "pdfPageEnd": end+2,
            "originalUrl": f"../downloads/policy-agri-loan-handbook-114.pdf#page={start+2}",
            "verificationStatus": "source-indexed"} for slug, title, start, end in FAQ]
    appendices = [{"id": slug, "title": title, "kind": kind, "printedPageStart": start,
                   "printedPageEnd": end, "pdfPageStart": start+2, "pdfPageEnd": end+2,
                   "verificationStatus": "source-indexed"} for slug, title, start, end, kind in APPENDICES]
    form_candidates = extract_forms(pages)
    forms, form_exclusions = build_source_indexed_forms(form_candidates)
    interpretations = extract_source_indexed_interpretations(pages)
    interpretation_candidates = extract_interpretation_candidates(pages, interpretations)
    disposition_count = lambda items, value: sum(item.get("disposition") == value for item in items)
    quick_index_entries = sum(len(group["items"]) for group in quick_index["groups"])
    manual = {
        "id": VERSION, "displayName": "114年度", "sourceTitle": "114年度政策性農業專案貸款業務手冊",
        "pdfPages": EXPECTED_PAGES, "digitalRevision": "114.0.0-beta.2.6", "releaseStatus": "Beta", "sha256": SHA256,
        "printedPageMapping": {"strategy": "continuous-offset-after-two-page-toc", "offset": 2,
                               "verifiedPdfPages": sorted(anchors), "status": "sampled-consistent"},
        "counts": {
            "loanPrograms": len(loan_programs),
            "interpretationsSourceIndexed": len(interpretations),
            "interpretationCandidateInventoryTotal": len(interpretation_candidates),
            "interpretationCandidatesPromoted": disposition_count(interpretation_candidates, "promoted-to-source-index"),
            "interpretationCandidatesDuplicate": disposition_count(interpretation_candidates, "duplicate-detection"),
            "interpretationCandidatesCited": disposition_count(interpretation_candidates, "cited-document"),
            "interpretationCandidatesContinuation": disposition_count(interpretation_candidates, "continuation-reference"),
            "interpretationCandidatesVariant": disposition_count(interpretation_candidates, "duplicate-variant"),
            "interpretationCandidatesFalsePositive": disposition_count(interpretation_candidates, "false-positive"),
            "interpretationCandidatesPending": disposition_count(interpretation_candidates, "pending-review"),
            "formsSourceIndexed": len(forms),
            "formCandidateInventoryTotal": len(form_candidates),
            "formCandidatesPromoted": disposition_count(form_candidates, "promoted-to-source-index"),
            "formCandidatesExcluded": disposition_count(form_candidates, "excluded"),
            "formCandidatesPending": disposition_count(form_candidates, "pending-review"),
            "faqGroups": len(faq), "appendicesAndAttachments": len(appendices),
            "tocEntries": len(toc["items"]), "quickIndexEntries": quick_index_entries,
        },
    }
    review = {
        "version": VERSION,
        "sections": [
            {"id": "page-mapping", "status": "sampled-consistent", "reviewedPages": sorted(anchors),
             "pendingPages": [], "notes": f"以目錄、連續印刷頁碼及 {len(anchors)} 個分散錨點確認 PDF 頁碼與印刷頁碼差 2。"},
            {"id": "text-extraction", "status": "automatically-extracted", "reviewedPages": [],
             "pendingPages": [p["pdfPage"] for p in pages], "notes": "保留 PDF 既有文字層，尚待逐頁人工校讀。"},
            {"id": "interpretations", "status": "source-indexed", "reviewedPages": sorted({r["pdfPageStart"] for r in interpretations}),
             "pendingPages": sorted({r["pdfPage"] for r in interpretation_candidates if r["disposition"] == "pending-review"}),
             "notes": "正式索引僅納入同頁可通過嚴格標頭、日期、完整文號及主旨起始規則的資料；候選庫另行保留判定結果。"},
            {"id": "faq-and-forms", "status": "source-indexed", "reviewedPages": sorted({r["pdfPageStart"] for r in forms}),
             "pendingPages": sorted({r["pdfPage"] for r in form_candidates if r["disposition"] == "pending-review"}),
             "notes": "FAQ 依原目錄；書表來源索引採明確來源頁清單，候選庫標示納入、排除或待覆核。"},
        ],
    }
    complex_patterns = (
        "貸款項目 貸款額度", "貸款項目 貸款用途", "申請書", "審核表",
        "查驗紀錄", "檢核表", "切結書", "常見問答", "常見問題",
    )
    forced_hybrid_printed = set(range(15, 30)) | set(range(309, 358))
    rendering_pages = []
    for page in pages:
        text = page["searchText"]
        is_complex = page["pdfPage"] in {1, 2} or page["printedPage"] in forced_hybrid_printed or any(
            pattern in text for pattern in complex_patterns
        )
        mode = "hybrid" if is_complex and page["hasTextLayer"] else ("preview" if not page["hasTextLayer"] else "text")
        page["renderMode"] = mode
        if mode != "text":
            rendering_pages.append({
                "pdfPage": page["pdfPage"], "printedPage": page["printedPage"], "renderMode": mode,
                "reason": "正式目錄、複雜表格、書表、FAQ或附件，保留原始版面並附文字層。" if mode == "hybrid"
                          else "本頁沒有可靠文字層，以原始頁面預覽呈現。",
                "reviewStatus": "needs-review",
            })
    rendering_rules = {
        "version": VERSION, "defaultMode": "text",
        "preview": {"format": "webp", "width": 1400, "quality": 80},
        "pages": rendering_pages,
    }
    write_json(ROOT / "data" / "versions.json", {"currentVersion": "114", "versions": [{
        "id": "114", "displayName": "114年度", "sourceTitle": "114年度政策性農業專案貸款業務手冊",
        "pdfPages": 359, "digitalRevision": "114.0.0-beta.2.6", "status": "Beta",
        "sourceFile": "policy-agri-loan-handbook-114.pdf"}]})
    write_json(DATA / "manual.json", manual)
    write_json(DATA / "toc.json", toc)
    write_json(DATA / "quick-index.json", quick_index)
    write_json(DATA / "pages.json", pages)
    write_json(DATA / "loan-programs.json", loan_programs)
    write_json(DATA / "interpretations.json", interpretations)
    write_json(DATA / "interpretation-candidates.json", interpretation_candidates)
    write_json(DATA / "faq.json", faq)
    write_json(DATA / "forms.json", forms)
    write_json(DATA / "form-candidates.json", form_candidates)
    write_json(DATA / "form-exclusions.json", form_exclusions)
    write_json(DATA / "appendices.json", appendices)
    write_json(DATA / "page-rendering-rules.json", rendering_rules)
    write_json(DATA / "review-status.json", review)
    write_json(DATA / "printed-page-map.json", {
        "version": VERSION, "status": "sampled-consistent", "offset": 2, "pageCount": EXPECTED_PAGES,
        "anchorCount": len(anchors),
        "pages": [{
            "pdfPage": pdf_page,
            "printedPage": pdf_page - 2 if pdf_page >= 3 else None,
            "mappingMethod": "front-matter" if pdf_page <= 2 else "continuous-offset-after-two-page-toc",
            "verificationStatus": "checked-anchor" if pdf_page in anchors else "not-individually-checked",
        } for pdf_page in range(1, EXPECTED_PAGES + 1)],
    })
    print(f"Extracted {len(pages)} pages; {sum(p['hasTextLayer'] for p in pages)} have text layers")
    print(f"Indexed {len(loan_programs)} loans, {len(interpretations)} interpretation records, {len(forms)} forms/attachments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
