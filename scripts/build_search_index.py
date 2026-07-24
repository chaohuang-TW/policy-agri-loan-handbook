#!/usr/bin/env python3
"""Build the privacy-preserving browser search index."""
from __future__ import annotations

import json
from pathlib import Path

from content_model import (
    interpretation_group_slug,
    scope_for_page,
    scope_group_for_form,
    scope_group_for_interpretation,
    scope_group_for_page,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def build_search_index(output_dir: Path) -> list[dict]:
    output = Path(output_dir) / "assets" / "data" / "search-index.json"
    records: list[dict] = []
    loans = load("loan-programs.json")
    for page in load("pages.json"):
        search_text = page["searchText"].replace("日農授金字第", "日 農授金字第")
        printed_label = page["printedPage"] if page["printedPage"] is not None else "目錄"
        records.append({
            "id": f"page-{page['pdfPage']:03d}", "type": "原文頁面", "title": page["title"],
            "category": page["chapterId"], "version": "114年度", "printedPage": page["printedPage"],
            "pdfPage": page["pdfPage"],
            "text": f"{page['title']} {search_text} 手冊頁 {printed_label} PDF頁 {page['pdfPage']}",
            "headings": [page["title"]], "scope": scope_for_page(page),
            "scopeGroup": scope_group_for_page(page),
            "url": f"versions/114/pages/page-{page['pdfPage']:03d}.html#pdf-page-{page['pdfPage']}",
            "breadcrumb": ["114年度", page["title"]],
        })
    for loan in loans:
        records.append({
            "id": f"loan-{loan['id']}", "type": "貸款索引", "title": loan["title"],
            "category": loan["category"], "version": "114年度", "printedPage": loan["sourceStartPage"],
            "pdfPage": loan["pdfStartPage"],
            "text": f"{loan['title']} {loan['category']} 函釋 原文 手冊頁 {loan['sourceStartPage']}",
            "headings": [loan["title"]], "scope": f"loan:{loan['id']}", "scopeGroup": f"loan:{loan['id']}",
            "url": loan["detailUrl"], "breadcrumb": ["貸款索引", loan["title"]],
        })
    sources = (
        ("interpretations.json", "函釋", "interpretations"),
        ("faq.json", "常見問答", "faq"),
        ("forms.json", "書表附件", "forms"),
        ("appendices.json", "附錄附件", "forms"),
    )
    for name, label, folder in sources:
        for item in load(name):
            pdf_page = item.get("pdfPage", item.get("pdfPageStart"))
            printed = item.get("printedPage", item.get("printedPageStart"))
            if label == "附錄附件":
                scope, scope_group = "appendix", None
            elif label == "函釋":
                scope = f"interpretation-group:{interpretation_group_slug(item['loanProgram'])}"
                scope_group = scope_group_for_interpretation(item)
            elif label == "常見問答":
                scope, scope_group = f"faq:{item['id']}", None
            else:
                scope_group = scope_group_for_form(item)
                scope = scope_group or "form:common"
            records.append({
                "id": f"{folder}-{item['id']}", "type": label, "title": item["title"], "category": label,
                "version": "114年度", "printedPage": printed, "pdfPage": pdf_page,
                "text": " ".join(str(v) for v in (
                    item["title"], item.get("documentNumber", ""), item.get("date", ""),
                    item.get("loanProgram", ""), label, printed, pdf_page,
                )),
                "headings": [item["title"]], "scope": scope, "scopeGroup": scope_group,
                "documentNumber": item.get("documentNumber"), "date": item.get("date"),
                "loanProgram": item.get("loanProgram"),
                "url": f"{folder}/index.html#item-{item['id']}",
                "breadcrumb": [label, item["title"]],
            })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Built {len(records)} search records")
    return records


def main() -> None:
    site = ROOT / "site"
    if not site.is_dir():
        raise SystemExit("site/ does not exist; run python scripts/build_all.py first")
    build_search_index(site)


if __name__ == "__main__":
    main()
