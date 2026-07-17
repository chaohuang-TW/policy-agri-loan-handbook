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
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    return re.sub(r"\s+", " ", text).strip()


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
    return "\n".join(line.rstrip() for line in lines)


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


def section_for(printed: int | None) -> tuple[str, str]:
    if printed is None:
        return ("front-matter", "目錄")
    for slug, title, start, end in SECTIONS:
        if start <= printed <= end:
            return slug, title
    return ("unassigned", "待人工覆核")


def extract_interpretations(pages: list[dict]) -> list[dict]:
    records: list[dict] = []
    seen: set[tuple[str, int]] = set()
    document_pattern = re.compile(r"(?:農(?:授金|金|輔|糧|牧|漁|企|業|字)?字)第?\s*[A-Z0-9０-９\s]+號")
    date_pattern = re.compile(r"中華民國\s*[一二三四五六七八九十百零〇○0-9０-９年月日\s]+")
    for loan_title, start, end in INTERPRETATION_RANGES:
        for printed in range(start, end + 1):
            page = pages[printed + 1]
            text = page["rawText"]
            subject_lines = [line.strip() for line in text.splitlines() if "主旨" in line]
            docs = [re.sub(r"\s+", "", value) for value in document_pattern.findall(text)]
            for number in docs:
                key = (number, printed)
                if key in seen:
                    continue
                seen.add(key)
                date_match = date_pattern.search(text)
                title = subject_lines[0] if subject_lines else f"{loan_title}相關函釋"
                records.append({
                    "id": f"interpretation-{len(records)+1:03d}",
                    "title": normalize_search(title)[:180],
                    "documentNumber": number,
                    "date": normalize_search(date_match.group(0)) if date_match else None,
                    "loanProgram": loan_title,
                    "printedPage": printed,
                    "pdfPage": printed + 2,
                    "originalUrl": f"../../downloads/policy-agri-loan-handbook-114.pdf#page={printed+2}",
                    "verificationStatus": "source-indexed" if date_match and subject_lines else "needs-review",
                })
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
    anchors = {3: 1, 32: 30, 96: 94, 211: 209, 272: 270, 302: 300, 335: 333, 350: 348, 359: 357}
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

    toc = {
        "version": VERSION,
        "title": "114年度政策性農業專案貸款業務手冊",
        "groups": [
            {"id": "part-1", "title": "壹、政策性農業專案貸款", "items": [
                {"id": "policy-loan-regulations", "title": "一、辦理政策性農業專案貸款辦法", "printedPage": 1, "pdfPage": 3},
                {"id": "agricultural-development-fund-rules", "title": "二、農業發展基金貸款相關規定及函釋", "printedPage": 30, "pdfPage": 32},
                {"id": "loan-programs", "title": "（二）各項貸款規定", "printedPage": 94, "pdfPage": 96,
                 "children": [{"id": item[0], "title": f"{index}. {item[1]}", "printedPage": item[3], "pdfPage": item[3]+2,
                               "hasInterpretations": item[5]} for index, item in enumerate(LOANS[:19], 1)]},
                {"id": "natural-disaster-low-interest-loan", "title": "（三）農業天然災害救助辦法及低利貸款相關函釋", "printedPage": 270, "pdfPage": 272,
                 "hasInterpretations": True},
            ]},
            {"id": "part-2", "title": "貳、全國農業金庫貸款", "items": [
                {"id": item[0], "title": item[1], "printedPage": item[3], "pdfPage": item[3]+2}
                for item in LOANS[20:]
            ]},
            {"id": "appendices", "title": "附錄、FAQ與附件", "items": [
                {"id": slug, "title": title, "printedPage": start, "pdfPage": start+2, "kind": kind}
                for slug, title, start, _end, kind in APPENDICES
            ]},
        ],
    }
    faq = [{"id": slug, "title": title, "printedPageStart": start, "printedPageEnd": end,
            "pdfPageStart": start+2, "pdfPageEnd": end+2,
            "originalUrl": f"../downloads/policy-agri-loan-handbook-114.pdf#page={start+2}",
            "verificationStatus": "source-indexed"} for slug, title, start, end in FAQ]
    appendices = [{"id": slug, "title": title, "kind": kind, "printedPageStart": start,
                   "printedPageEnd": end, "pdfPageStart": start+2, "pdfPageEnd": end+2,
                   "verificationStatus": "source-indexed"} for slug, title, start, end, kind in APPENDICES]
    forms = extract_forms(pages)
    interpretations = extract_interpretations(pages)

    manual = {
        "id": VERSION, "displayName": "114年度", "sourceTitle": "114年度政策性農業專案貸款業務手冊",
        "pdfPages": EXPECTED_PAGES, "digitalRevision": "114.0.0", "sha256": SHA256,
        "printedPageMapping": {"strategy": "continuous-offset-after-two-page-toc", "offset": 2,
                               "verifiedPdfPages": sorted(anchors), "status": "manually-sampled"},
        "counts": {"loanPrograms": len(loan_programs), "interpretations": len(interpretations),
                   "faq": len(faq), "forms": len(forms), "appendices": len(appendices)},
    }
    review = {
        "version": VERSION,
        "sections": [
            {"id": "page-mapping", "status": "manually-reviewed", "reviewedPages": sorted(anchors),
             "pendingPages": [], "notes": "以目錄、連續印刷頁碼及九個代表錨點確認 PDF 頁碼與印刷頁碼差 2。"},
            {"id": "text-extraction", "status": "automatically-extracted", "reviewedPages": [],
             "pendingPages": [p["pdfPage"] for p in pages], "notes": "保留 PDF 既有文字層，尚待逐頁人工校讀。"},
            {"id": "interpretations", "status": "needs-review", "reviewedPages": [],
             "pendingPages": sorted({r["pdfPage"] for r in interpretations}), "notes": "文號、日期與主旨由文字層索引，需人工覆核跨頁文件。"},
            {"id": "faq-and-forms", "status": "needs-review", "reviewedPages": [],
             "pendingPages": list(range(315, 360)), "notes": "FAQ、附件與書表維持原文入口，需人工內容抽查。"},
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
        "pdfPages": 359, "digitalRevision": "114.0.0", "status": "current",
        "sourceFile": "policy-agri-loan-handbook-114.pdf"}]})
    write_json(DATA / "manual.json", manual)
    write_json(DATA / "toc.json", toc)
    write_json(DATA / "pages.json", pages)
    write_json(DATA / "loan-programs.json", loan_programs)
    write_json(DATA / "interpretations.json", interpretations)
    write_json(DATA / "faq.json", faq)
    write_json(DATA / "forms.json", forms)
    write_json(DATA / "appendices.json", appendices)
    write_json(DATA / "page-rendering-rules.json", rendering_rules)
    write_json(DATA / "review-status.json", review)
    print(f"Extracted {len(pages)} pages; {sum(p['hasTextLayer'] for p in pages)} have text layers")
    print(f"Indexed {len(loan_programs)} loans, {len(interpretations)} interpretation records, {len(forms)} forms/attachments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
