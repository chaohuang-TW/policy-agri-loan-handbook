#!/usr/bin/env python3
"""High-confidence static validation for the built browser search experience."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

EXPECTED_TYPES = {
    "原文頁面": 359,
    "貸款索引": 23,
    "函釋": 87,
    "常見問答": 4,
    "書表附件": 28,
    "附錄附件": 6,
}
EXPECTED_GROUPED = {"原文頁面": 215, "函釋": 56, "書表附件": 21}
UNSAFE = (
    "results.innerHTML", "innerHTML =", "insertAdjacentHTML", "document.write",
    "eval(", "new Function", "Function(", "localStorage", "sessionStorage",
    "document.cookie",
)
FORBIDDEN_TEXT = ("手冊頁 None", "undefined", "[object Object]", "nan")


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.h1 = 0
        self.attrs: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.attrs.append((tag, data))
        if data.get("id"):
            self.ids.append(str(data["id"]))
        if tag == "h1":
            self.h1 += 1


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(root: Path) -> list[str]:
    root = root.resolve()
    data = root / "data" / "114"
    site = root / "site"
    errors: list[str] = []
    records = load(site / "assets/data/search-index.json")
    concepts = load(data / "search-concepts.json")
    intents = load(data / "search-intents.json")
    loans = load(data / "loan-programs.json")
    pages = load(data / "pages.json")
    relationships = load(data / "content-relationships.json")
    revision = load(data / "manual.json")["digitalRevision"]

    if len(records) != 507:
        fail(errors, f"expected 507 records, got {len(records)}")
    counts = Counter(record.get("type") for record in records)
    if {key: counts[key] for key in EXPECTED_TYPES} != EXPECTED_TYPES:
        fail(errors, f"type counts changed: {dict(counts)}")
    if len({(record.get("id"), record.get("url")) for record in records}) != len(records):
        fail(errors, "duplicate search id/url")
    if any(not record.get("id") or not record.get("scope") or not record.get("url") or not record.get("contextTitle") for record in records):
        fail(errors, "record missing id, scope, contextTitle or URL")
    for record in records:
        text = str(record.get("text", ""))
        for token in FORBIDDEN_TEXT:
            pattern = rf"\b{re.escape(token)}\b" if token == "nan" else re.escape(token)
            if re.search(pattern, text, re.I):
                fail(errors, f"forbidden search text {token}: {record.get('id')}")
        if "日農授金字第" in str(record.get("documentNumber") or ""):
            fail(errors, f"invalid document number prefix: {record.get('id')}")
        if record.get("type") == "常見問答" and str(record.get("scope", "")).startswith("form:"):
            fail(errors, f"FAQ has form scope: {record.get('id')}")
        if record.get("type") == "常見問答" and record.get("scopeGroup") is not None:
            fail(errors, f"FAQ has false loan scopeGroup: {record.get('id')}")
        if record.get("type") == "附錄附件":
            if record.get("scope") != "appendix" or record.get("scopeGroup") is not None:
                fail(errors, f"appendix scope invalid: {record.get('id')}")

    for record_type, expected in EXPECTED_GROUPED.items():
        actual = sum(
            bool(record.get("type") == record_type and record.get("scopeGroup"))
            for record in records
        )
        if actual != expected:
            fail(errors, f"{record_type} grouped count {actual}, expected {expected}")

    loan_by_id = {loan["id"]: loan for loan in loans}
    valid_groups = {f"loan:{loan_id}" for loan_id in loan_by_id}
    for record in records:
        group = record.get("scopeGroup")
        if group and group not in valid_groups:
            fail(errors, f"unknown scopeGroup {group}: {record.get('id')}")
        if group and record.get("type") not in {"原文頁面", "貸款索引", "函釋", "書表附件"}:
            fail(errors, f"non-loan content has loan scopeGroup: {record.get('id')}")
    page_records = {
        record["pdfPage"]: record for record in records if record.get("type") == "原文頁面"
    }
    for page in pages:
        expected_loan = next((
            loan for loan in loans
            if page.get("printedPage") is not None
            and loan["sourceStartPage"] <= page["printedPage"] <= loan["sourceEndPage"]
        ), None)
        expected_group = f"loan:{expected_loan['id']}" if expected_loan else None
        actual = page_records[page["pdfPage"]].get("scopeGroup")
        if actual != expected_group:
            fail(errors, f"page-{page['pdfPage']:03d} scopeGroup {actual}, expected {expected_group}")

    html_files = sorted(site.rglob("*.html"))
    if len(html_files) != 397:
        fail(errors, f"expected 397 HTML pages, got {len(html_files)}")
    html_docs: dict[Path, tuple[str, Document]] = {}
    known_scopes = {record["scope"] for record in records}
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        parser = Document()
        parser.feed(text)
        html_docs[path] = (text, parser)
        if parser.h1 != 1:
            fail(errors, f"H1 count {parser.h1}: {path.relative_to(site)}")
        if len(parser.ids) != len(set(parser.ids)):
            fail(errors, f"duplicate IDs: {path.relative_to(site)}")
        if revision not in text:
            fail(errors, f"revision missing: {path.relative_to(site)}")
        for token in UNSAFE:
            if token in text:
                fail(errors, f"unsafe token {token}: {path.relative_to(site)}")
        body = next((attrs for tag, attrs in parser.attrs if tag == "body"), {})
        group = body.get("data-search-scope-group")
        if group and group not in valid_groups:
            fail(errors, f"page scopeGroup unknown: {path.relative_to(site)}")
        scopes = str(body.get("data-search-scopes") or "").split(",")
        for scope in filter(None, map(str.strip, scopes)):
            if scope != "all" and scope not in known_scopes:
                fail(errors, f"page references unknown search scope {scope}: {path.relative_to(site)}")
        printable = body.get("data-printable") == "true"
        print_label = body.get("data-print-label")
        relative = path.relative_to(site).as_posix()
        if printable:
            expected_label = (
                "列印本頁" if "/pages/" in relative
                else "列印本貸款" if relative.startswith("loans/") and relative != "loans/index.html"
                else "列印本章"
            )
            if print_label != expected_label:
                fail(errors, f"wrong print label {print_label}, expected {expected_label}: {relative}")

    for section in relationships["sections"]:
        path = site / "versions" / "114" / "sections" / section["id"] / "index.html"
        text, parser = html_docs[path]
        body = next(attrs for tag, attrs in parser.attrs if tag == "body")
        actual_scopes = set(filter(None, str(body.get("data-search-scopes") or "").split(",")))
        section_pages = [
            page for page in pages
            if page.get("printedPage") is not None
            and section["printedPageStart"] <= page["printedPage"] <= section["printedPageEnd"]
        ]
        expected_scopes = {f"section:{page['chapterId']}" for page in section_pages}
        if actual_scopes != expected_scopes:
            fail(errors, f"section {section['id']} scopes {sorted(actual_scopes)}, expected {sorted(expected_scopes)}")
        matching = [
            record for record in records
            if record.get("type") == "原文頁面" and record.get("scope") in actual_scopes
        ]
        if not matching:
            fail(errors, f"section {section['id']} has no source search records")
        if any(record["scope"] not in expected_scopes for record in matching):
            fail(errors, f"section {section['id']} leaks source records")

    for record in records:
        parsed = urlsplit(record["url"])
        target = site / unquote(parsed.path)
        if not target.is_file():
            fail(errors, f"search URL target missing: {record['url']}")
            continue
        if parsed.fragment and f'id="{parsed.fragment}"' not in target.read_text(encoding="utf-8"):
            fail(errors, f"search fragment missing: {record['url']}")

    js = (root / "assets/js/search.js").read_text(encoding="utf-8")
    core = (root / "assets/js/search-core.js").read_text(encoding="utf-8")
    for token in UNSAFE:
        if token in js or token in core:
            fail(errors, f"unsafe search implementation: {token}")
    for name in ("search-core.js", "search.js", "site-tools.js"):
        if (site / "assets/js" / name).read_bytes() != (root / "assets/js" / name).read_bytes():
            fail(errors, f"source and site JavaScript differ: {name}")
    base = (root / "templates/base.html").read_text(encoding="utf-8")
    if '#286b57' not in base:
        fail(errors, "theme-color mismatch")
    if base.find("search-core.js") > base.find("search.js"):
        fail(errors, "search-core must load before search.js")
    if "maxlength=\"256\"" not in base or "maxlength=\"256\"" not in (root / "scripts/build_site.py").read_text():
        fail(errors, "search maxlength missing")
    if len(concepts) != 15 or len({item["id"] for item in concepts}) != 15:
        fail(errors, "search concepts are not 15 unique records")
    if len(intents) != 5 or any(
        not set(item.get("preferredTypes", [])).issubset(EXPECTED_TYPES)
        for item in intents
    ):
        fail(errors, "search intents invalid")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        print("SEARCH EXPERIENCE VALIDATION FAILED")
        for error in errors:
            print("- " + error)
        return 1
    print("SEARCH EXPERIENCE VALIDATION PASSED: 507 records, 397 HTML pages, 7 sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
