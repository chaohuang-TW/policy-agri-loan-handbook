#!/usr/bin/env python3
"""Validate the generated FAQ and interpretation reference lookup tools."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from faq_lookup import build_audit  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"
SITE = ROOT / "site"


class LookupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.lookup_kinds: list[str] = []
        self.cards: list[dict] = []
        self.all_hrefs: list[str] = []
        self.card_stack: list[dict] = []
        self.group_filters: list[str] = []
        self.selects: dict[str, set[str]] = {"program": set(), "year": set()}
        self.current_select: str | None = None
        self.text_stack: list[list[str]] = []
        self.source_group_count = 0
        self.lookup_data_found = False
        self.current_doc_card: dict | None = None

    def handle_starttag(self, tag, attrs_list):
        attrs = {key: value or "" for key, value in attrs_list}
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if attrs.get("data-reference-lookup"):
            self.lookup_kinds.append(attrs["data-reference-lookup"])
        if tag == "script" and attrs.get("data-lookup-data") is not None:
            self.lookup_data_found = True
        if attrs.get("data-lookup-result") is not None:
            card = {
                "id": attrs.get("data-lookup-id", ""),
                "key": attrs.get("data-lookup-key", attrs.get("data-lookup-id", "")),
                "attrs": attrs,
                "hrefs": [],
                "text": [],
                "doc_number": [],
            }
            self.cards.append(card)
            self.card_stack.append(card)
        if tag == "p" and "lookup-doc-number" in attrs.get("class", "").split() and self.card_stack:
            self.current_doc_card = self.card_stack[-1]
        if tag == "a" and attrs.get("href"):
            self.all_hrefs.append(attrs["href"])
            if self.card_stack:
                self.card_stack[-1]["hrefs"].append(attrs["href"])
        if attrs.get("data-lookup-group-filter") is not None:
            self.group_filters.append(attrs["data-lookup-group-filter"])
        if tag == "select" and attrs.get("data-lookup-program") is not None:
            self.current_select = "program"
        elif tag == "select" and attrs.get("data-lookup-year") is not None:
            self.current_select = "year"
        if tag == "option" and self.current_select is not None:
            self.selects[self.current_select].add(attrs.get("value", ""))
        if attrs.get("class", "").split() and "lookup-source-groups" in attrs.get("class", "").split():
            self.source_group_count += 1
        self.text_stack.append([])

    def handle_startendtag(self, tag, attrs_list):
        self.handle_starttag(tag, attrs_list)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if self.text_stack:
            self.text_stack[-1].append(data)
        if self.card_stack:
            self.card_stack[-1]["text"].append(data)
        if self.current_doc_card is not None:
            self.current_doc_card["doc_number"].append(data)

    def handle_endtag(self, tag):
        if tag == "select":
            self.current_select = None
        if tag == "p" and self.current_doc_card is not None:
            self.current_doc_card = None
        if tag == "article" and self.card_stack:
            self.card_stack.pop()
        if self.text_stack:
            self.text_stack.pop()


def parse(path: Path) -> LookupParser:
    parser = LookupParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def page_target(path: Path, href: str) -> tuple[Path | None, int | None]:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return None, None
    target = (path.parent / unquote(parsed.path)).resolve()
    try:
        target.relative_to(SITE.resolve())
    except ValueError:
        return None, None
    match = re.search(r"page-(\d{3})\.html$", parsed.path)
    return target, int(match.group(1)) if match else None


def main() -> int:
    errors: list[str] = []
    audit = build_audit()
    expected_faq = audit["records"]
    faq_items_path = DATA / "faq-items.json"
    if not faq_items_path.is_file():
        errors.append("missing data/114/faq-items.json")
        actual_faq = []
    else:
        actual_faq = json.loads(faq_items_path.read_text(encoding="utf-8"))
    if actual_faq != expected_faq:
        errors.append("faq-items.json differs from deterministic source parser output")

    faq_groups = json.loads((DATA / "faq.json").read_text(encoding="utf-8"))
    group_map = {group["id"]: group for group in faq_groups}
    faq_ids = [item.get("id") for item in actual_faq]
    if len(faq_ids) != len(set(faq_ids)):
        errors.append("duplicate FAQ question ID")
    for item in actual_faq:
        group = group_map.get(item.get("faqGroupId"))
        if not group:
            errors.append(f"unknown FAQ group: {item.get('id')}")
            continue
        if not item.get("question", "").strip():
            errors.append(f"blank FAQ question: {item.get('id')}")
        start, end = item.get("pdfPageStart"), item.get("pdfPageEnd")
        if not isinstance(start, int) or not isinstance(end, int) or not (1 <= start <= end <= 359):
            errors.append(f"invalid FAQ source pages: {item.get('id')}")
        source_pages = item.get("sourcePages")
        if not isinstance(source_pages, list) or not source_pages or any(not isinstance(page, int) or not (1 <= page <= 359) for page in source_pages):
            errors.append(f"invalid FAQ sourcePages: {item.get('id')}")
        elif source_pages != list(range(start, end + 1)):
            errors.append(f"FAQ sourcePages range mismatch: {item.get('id')}")
        if not (group["pdfPageStart"] <= start <= end <= group["pdfPageEnd"]):
            errors.append(f"FAQ crosses group boundary: {item.get('id')}")
        original = urlsplit(item.get("originalUrl", ""))
        if original.scheme or original.netloc or not re.fullmatch(r"\.\./downloads/policy-agri-loan-handbook-114\.pdf", original.path) or original.fragment != f"page={start}":
            errors.append(f"invalid FAQ originalUrl: {item.get('id')}")
        if item.get("verificationStatus") == "ambiguous" or item.get("rangeStatus") == "ambiguous":
            errors.append(f"ambiguous FAQ promoted as record: {item.get('id')}")
        if item.get("answerText"):
            source = "\n".join(
                page.get("rawText", "")
                for page in json.loads((DATA / "pages.json").read_text(encoding="utf-8"))
                if start <= page.get("pdfPage", 0) <= end
            )
            compact_answer = re.sub(r"\s+", "", item["answerText"])
            if compact_answer and compact_answer not in re.sub(r"\s+", "", source):
                errors.append(f"FAQ answer is not traceable: {item.get('id')}")

    faq_path = SITE / "faq/index.html"
    interpretation_path = SITE / "interpretations/index.html"
    if not faq_path.is_file() or not interpretation_path.is_file():
        errors.append("missing FAQ or interpretation route")
        faq_parser = LookupParser()
        interpretation_parser = LookupParser()
    else:
        faq_parser = parse(faq_path)
        interpretation_parser = parse(interpretation_path)
    if "faq" not in faq_parser.lookup_kinds:
        errors.append("FAQ lookup tool missing")
    if not faq_parser.lookup_data_found:
        errors.append("FAQ embedded lookup data missing")
    if "interpretations" not in interpretation_parser.lookup_kinds:
        errors.append("interpretation lookup tool missing")
    if not interpretation_parser.lookup_data_found:
        errors.append("interpretation embedded lookup data missing")
    if faq_parser.source_group_count != 1:
        errors.append("FAQ source group listing missing")
    if set(faq_parser.group_filters) != {"", *(group["id"] for group in faq_groups)}:
        errors.append("FAQ filter options do not match four source groups")
    if len(faq_parser.cards) != len(actual_faq):
        errors.append(f"FAQ rendered card count mismatch: {len(faq_parser.cards)}")
    expected_by_id = {item["id"]: item for item in actual_faq}
    if len({card["id"] for card in faq_parser.cards}) != len(faq_parser.cards):
        errors.append("duplicate rendered FAQ card ID")
    for card in faq_parser.cards:
        item = expected_by_id.get(card["id"])
        if not item:
            errors.append(f"rendered unknown FAQ card: {card['id']}")
            continue
        if card["attrs"].get("data-lookup-group") != item["faqGroupId"]:
            errors.append(f"FAQ card group mismatch: {card['id']}")
        for href in card["hrefs"]:
            if "page-" not in href:
                continue
            target, page_number = page_target(faq_path, href)
            if target is None or not target.is_file() or not page_number or not (1 <= page_number <= 359):
                errors.append(f"broken FAQ Evidence/PDF target: {card['id']} -> {href}")
    for href in faq_parser.all_hrefs:
        if "page-" not in href:
            continue
        target, page_number = page_target(faq_path, href)
        if target is None or not target.is_file() or not page_number or not (1 <= page_number <= 359):
            errors.append(f"broken FAQ route Evidence/PDF target: {href}")

    interpretations = json.loads((DATA / "interpretations.json").read_text(encoding="utf-8"))
    interpretation_ids = [item.get("id") for item in interpretations]
    if len(interpretations) != 87:
        errors.append(f"interpretation count changed: {len(interpretations)}")
    if len(interpretation_parser.cards) != len(interpretations):
        errors.append(f"rendered interpretation card count mismatch: {len(interpretation_parser.cards)}")
    source_id_occurrences: dict[str, int] = {}
    interpretation_by_key: dict[str, dict] = {}
    for item in interpretations:
        source_id_occurrences[item["id"]] = source_id_occurrences.get(item["id"], 0) + 1
        occurrence = source_id_occurrences[item["id"]]
        lookup_key = item["id"] if occurrence == 1 else f"{item['id']}-duplicate-{occurrence}"
        interpretation_by_key[lookup_key] = item
    rendered_keys = [card["key"] for card in interpretation_parser.cards]
    if len(set(rendered_keys)) != len(rendered_keys):
        errors.append("duplicate rendered interpretation lookup key")
    if set(rendered_keys) != set(interpretation_by_key):
        errors.append("rendered interpretation lookup keys differ from source order")
    for card in interpretation_parser.cards:
        item = interpretation_by_key.get(card["key"])
        if not item:
            errors.append(f"rendered unknown interpretation card: {card['key']}")
            continue
        card_text = "".join(card["text"])
        if item.get("documentNumber", "") not in "".join(card["doc_number"]):
            errors.append(f"document number missing from rendered card: {card['key']}")
        if item.get("loanProgram", "") not in card_text:
            errors.append(f"loan program missing from rendered card: {card['key']}")
        pdf_start = item.get("pdfPageStart")
        if not isinstance(pdf_start, int) or not (1 <= pdf_start <= 359):
            errors.append(f"invalid interpretation source page: {card['key']}")
        original = urlsplit(item.get("originalUrl", ""))
        if original.scheme or original.netloc or original.fragment != f"page={pdf_start}" or not original.path.endswith("policy-agri-loan-handbook-114.pdf"):
            errors.append(f"invalid interpretation originalUrl: {card['key']}")
        for href in card["hrefs"]:
            if "page-" not in href:
                continue
            target, page_number = page_target(interpretation_path, href)
            if target is None or not target.is_file() or not page_number or not (1 <= page_number <= 359):
                errors.append(f"broken interpretation Evidence/PDF target: {card['key']} -> {href}")
    for href in interpretation_parser.all_hrefs:
        if "page-" not in href:
            continue
        target, page_number = page_target(interpretation_path, href)
        if target is None or not target.is_file() or not page_number or not (1 <= page_number <= 359):
            errors.append(f"broken interpretation route Evidence/PDF target: {href}")
    expected_programs = {item["loanProgram"] for item in interpretations}
    expected_years = {match.group(1) for item in interpretations if (match := re.search(r"(\d+)年", item.get("date", "")))}
    rendered_program_values = interpretation_parser.selects["program"] - {""}
    rendered_year_values = interpretation_parser.selects["year"] - {""}
    rendered_program_labels = {item["attrs"].get("data-lookup-program") for item in interpretation_parser.cards}
    if len(rendered_program_values) != len(expected_programs):
        errors.append("interpretation program filter is not data-derived")
    if rendered_year_values != expected_years:
        errors.append("interpretation year filter is not data-derived")
    js = (ROOT / "assets/js/reference-lookup.js").read_text(encoding="utf-8")
    for required in ("URLSearchParams", "popstate", "canonicalDocumentNumber", "programSlug"):
        if required not in js:
            errors.append(f"lookup JS missing required deterministic behavior: {required}")
    if re.search(r"fetch\(|XMLHttpRequest|https?://", js):
        errors.append("lookup JS introduces network lookup")
    html_count = len(list(SITE.rglob("*.html")))
    if html_count != 399:
        errors.append(f"HTML route count changed: {html_count}")
    result = {
        "status": "REFERENCE LOOKUP VALIDATION PASSED" if not errors else "REFERENCE LOOKUP VALIDATION FAILED",
        "faqGroups": len(faq_groups),
        "faqQuestionRecords": len(actual_faq),
        "faqRenderedCards": len(faq_parser.cards),
        "interpretations": len(interpretations),
        "interpretationRenderedCards": len(interpretation_parser.cards),
        "faqDuplicateIds": len(faq_ids) - len(set(faq_ids)),
        "interpretationSourceDuplicateIds": len(interpretation_ids) - len(set(interpretation_ids)),
        "interpretationRenderedDuplicateKeys": len(rendered_keys) - len(set(rendered_keys)),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
