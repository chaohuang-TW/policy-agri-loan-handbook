"""Single source of derived content ownership and public relationship slugs."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"


def _load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def relationships() -> dict:
    return _load("content-relationships.json")


@lru_cache(maxsize=1)
def loans() -> list[dict]:
    return _load("loan-programs.json")


@lru_cache(maxsize=1)
def pages() -> list[dict]:
    return _load("pages.json")


@lru_cache(maxsize=1)
def interpretations() -> list[dict]:
    return _load("interpretations.json")


@lru_cache(maxsize=1)
def forms() -> list[dict]:
    return _load("forms.json")


@lru_cache(maxsize=1)
def faqs() -> list[dict]:
    return _load("faq.json")


@lru_cache(maxsize=1)
def appendices() -> list[dict]:
    return _load("appendices.json")


def loan_by_id(loan_id: str) -> dict | None:
    return next((loan for loan in loans() if loan["id"] == loan_id), None)


def loan_by_title(title: str | None) -> dict | None:
    return next((loan for loan in loans() if loan["title"] == title), None)


def loan_for_printed_page(printed_page: int | None) -> dict | None:
    if printed_page is None:
        return None
    return next(
        (loan for loan in loans() if loan["sourceStartPage"] <= printed_page <= loan["sourceEndPage"]),
        None,
    )


def loan_for_pdf_page(pdf_page: int | None) -> dict | None:
    if pdf_page is None:
        return None
    return next(
        (loan for loan in loans() if loan["pdfStartPage"] <= pdf_page <= loan["pdfEndPage"]),
        None,
    )


def loan_for_interpretation(item: dict) -> dict | None:
    return loan_by_title(item.get("loanProgram"))


def loan_for_form(item: dict) -> dict | None:
    exceptions = relationships().get("formScopeGroupExceptions", {})
    if item.get("id") in exceptions:
        value = exceptions[item["id"]]
        return loan_by_id(value) if value else None
    return loan_for_printed_page(item.get("printedPageStart")) or loan_for_pdf_page(item.get("pdfPageStart"))


def scope_for_page(page: dict) -> str:
    return f"section:{page['chapterId']}"


def scope_group_for_page(page: dict) -> str | None:
    loan = loan_for_printed_page(page.get("printedPage")) or loan_for_pdf_page(page.get("pdfPage"))
    return f"loan:{loan['id']}" if loan else None


def scope_group_for_interpretation(item: dict) -> str | None:
    loan = loan_for_interpretation(item)
    return f"loan:{loan['id']}" if loan else None


def scope_group_for_form(item: dict) -> str | None:
    loan = loan_for_form(item)
    return f"loan:{loan['id']}" if loan else None


def sections() -> list[dict]:
    return relationships()["sections"]


def section_by_id(section_id: str) -> dict | None:
    return next((section for section in sections() if section["id"] == section_id), None)


def pages_for_section(section_id: str) -> list[dict]:
    section = section_by_id(section_id)
    if not section:
        return []
    return [
        page for page in pages()
        if page.get("printedPage") is not None
        and section["printedPageStart"] <= page["printedPage"] <= section["printedPageEnd"]
    ]


def section_scopes(section_id: str) -> list[str]:
    return sorted({scope_for_page(page) for page in pages_for_section(section_id)})


def interpretation_group_slug(loan_program: str) -> str:
    model = relationships()
    if loan_program == model["commonInterpretationProgram"]:
        return model["commonInterpretationSlug"]
    loan = loan_by_title(loan_program)
    if not loan:
        raise KeyError(f"unknown interpretation loan program: {loan_program}")
    return model.get("interpretationSlugOverrides", {}).get(loan["id"], loan["id"])


def toc_interpretation_group_slug(toc_base_id: str) -> str:
    alias = relationships().get("tocInterpretationAliases", {}).get(toc_base_id)
    if alias:
        return alias
    loan = loan_by_id(toc_base_id)
    if not loan:
        raise KeyError(f"unknown TOC interpretation group: {toc_base_id}")
    return interpretation_group_slug(loan["title"])


def interpretation_programs() -> list[str]:
    programs = {item["loanProgram"] for item in interpretations()}
    common = relationships()["commonInterpretationProgram"]
    return [common] + [loan["title"] for loan in loans() if loan["title"] in programs]
