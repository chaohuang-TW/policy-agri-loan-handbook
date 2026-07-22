#!/usr/bin/env python3
"""Build the privacy-preserving browser search index."""

from __future__ import annotations

import json
from pathlib import Path
from search_scope import scope_group_for_item, scope_group_for_page

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"
OUTPUT = ROOT / "site" / "assets" / "data" / "search-index.json"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def scope_for_page(page: dict) -> str:
    return f"section:{page['chapterId']}"


INTERPRETATION_GROUPS = {
    "農業發展基金貸款共同規定": "common-rules", "農機貸款": "farm-machinery-loan",
    "輔導農糧業經營貸款": "agri-food-business-loan", "輔導漁業經營貸款": "fishery-business-loan",
    "提升畜禽產業經營貸款": "livestock-poultry-loan", "農民經營及產銷班貸款": "farmer-production-group-loan",
    "農業科技園區進駐業者優惠貸款": "agri-tech-park-loan", "農家綜合貸款": "farm-household-loan",
    "農漁會事業發展貸款": "association-development-loan", "造林貸款": "afforestation-loan",
    "農業節能減碳貸款": "agri-energy-saving-loan", "青壯年農民從農貸款": "young-farmer-loan",
    "農民組織及農企業產銷經營及研發創新貸款": "agri-enterprise-innovation-loan",
    "擴大家庭農場經營規模協助農民購買耕地貸款": "farmland-purchase-loan",
    "農業天然災害低利貸款": "natural-disaster-loan",
}


def main() -> None:
    records = []
    loans = load("loan-programs.json")
    for page in load("pages.json"):
        # Keep date and document-number tokens distinct in search.  The source
        # text has no layout separator between 「日」 and 「農授金字」, which must
        # not manufacture the erroneous document number 「日農授金字…」.
        search_text = page["searchText"].replace("日農授金字第", "日 農授金字第")
        records.append({
            "id": f"page-{page['pdfPage']:03d}", "type": "原文頁面", "title": page["title"],
            "category": page["chapterId"], "version": "114年度", "printedPage": page["printedPage"],
            "pdfPage": page["pdfPage"], "text": f"{page['title']} {search_text} 手冊頁 {page['printedPage']} PDF頁 {page['pdfPage']}",
            "headings": [page["title"]], "scope": scope_for_page(page), "scopeGroup": scope_group_for_page(page, loans),
            "url": f"versions/114/pages/page-{page['pdfPage']:03d}.html#pdf-page-{page['pdfPage']}",
            "breadcrumb": ["114年度", page["title"]],
        })
    for loan in loans:
        records.append({
            "id": f"loan-{loan['id']}", "type": "貸款索引", "title": loan["title"],
            "category": loan["category"], "version": "114年度", "printedPage": loan["sourceStartPage"],
            "pdfPage": loan["pdfStartPage"], "text": f"{loan['title']} {loan['category']} 函釋 原文 手冊頁 {loan['sourceStartPage']}",
            "headings": [loan["title"]], "scope": f"loan:{loan['id']}", "scopeGroup": f"loan:{loan['id']}",
            "url": loan["detailUrl"], "breadcrumb": ["貸款索引", loan["title"]],
        })
    for name, label, folder in (("interpretations.json", "函釋", "interpretations"), ("faq.json", "常見問答", "faq"),
                                 ("forms.json", "書表附件", "forms"), ("appendices.json", "附錄附件", "forms")):
        for item in load(name):
            pdf_page = item.get("pdfPage", item.get("pdfPageStart"))
            printed = item.get("printedPage", item.get("printedPageStart"))
            if label == "附錄附件":
                scope = "appendix"
            elif label == "函釋":
                scope = f"interpretation-group:{INTERPRETATION_GROUPS.get(item.get('loanProgram'), 'common-rules')}"
            else:
                scope = f"form:{item.get('loanProgram') or 'common'}"
            records.append({
                "id": f"{folder}-{item['id']}", "type": label, "title": item["title"], "category": label,
                "version": "114年度", "printedPage": printed, "pdfPage": pdf_page,
                "text": " ".join(str(v) for v in (item["title"], item.get("documentNumber", ""), item.get("date", ""), item.get("loanProgram", ""), label, printed, pdf_page)),
                "headings": [item["title"]], "scope": scope, "scopeGroup": scope_group_for_item(item, loans, label),
                "documentNumber": item.get("documentNumber"), "date": item.get("date"), "loanProgram": item.get("loanProgram"),
                "url": f"{folder}/index.html#item-{item['id']}", "breadcrumb": [label, item["title"]],
            })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Built {len(records)} search records")


if __name__ == "__main__":
    main()
