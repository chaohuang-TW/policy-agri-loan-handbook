#!/usr/bin/env python3
"""Build the privacy-preserving browser search index."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"
OUTPUT = ROOT / "site" / "assets" / "data" / "search-index.json"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> None:
    records = []
    for page in load("pages.json"):
        # Keep date and document-number tokens distinct in search.  The source
        # text has no layout separator between 「日」 and 「農授金字」, which must
        # not manufacture the erroneous document number 「日農授金字…」.
        search_text = page["searchText"].replace("日農授金字第", "日 農授金字第")
        records.append({
            "id": f"page-{page['pdfPage']:03d}", "type": "原文頁面", "title": page["title"],
            "category": page["chapterId"], "version": "114年度", "printedPage": page["printedPage"],
            "pdfPage": page["pdfPage"], "text": f"{page['title']} {search_text} 手冊頁 {page['printedPage']} PDF頁 {page['pdfPage']}",
            "url": f"versions/114/pages/page-{page['pdfPage']:03d}.html#pdf-page-{page['pdfPage']}",
            "breadcrumb": ["114年度", page["title"]],
        })
    for loan in load("loan-programs.json"):
        records.append({
            "id": f"loan-{loan['id']}", "type": "貸款索引", "title": loan["title"],
            "category": loan["category"], "version": "114年度", "printedPage": loan["sourceStartPage"],
            "pdfPage": loan["pdfStartPage"], "text": f"{loan['title']} {loan['category']} 函釋 原文 手冊頁 {loan['sourceStartPage']}",
            "url": loan["detailUrl"], "breadcrumb": ["貸款索引", loan["title"]],
        })
    for name, label, folder in (("interpretations.json", "函釋", "interpretations"), ("faq.json", "常見問答", "faq"),
                                 ("forms.json", "書表附件", "forms"), ("appendices.json", "附錄附件", "forms")):
        for item in load(name):
            pdf_page = item.get("pdfPage", item.get("pdfPageStart"))
            printed = item.get("printedPage", item.get("printedPageStart"))
            records.append({
                "id": f"{folder}-{item['id']}", "type": label, "title": item["title"], "category": label,
                "version": "114年度", "printedPage": printed, "pdfPage": pdf_page,
                "text": " ".join(str(v) for v in (item["title"], item.get("documentNumber", ""), item.get("date", ""), item.get("loanProgram", ""), label, printed, pdf_page)),
                "url": f"{folder}/index.html#item-{item['id']}", "breadcrumb": [label, item["title"]],
            })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Built {len(records)} search records")


if __name__ == "__main__":
    main()
