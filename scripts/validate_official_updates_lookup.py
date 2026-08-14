#!/usr/bin/env python3
"""Validate the deterministic browser-side Official Updates lookup layer."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from content_model import sections

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "current"
SITE = ROOT / "site"
FIXTURE = ROOT / "tests" / "fixtures" / "official-updates-lookup.json"
GATEWAY = "https://www.afna.gov.tw/list.php?theme=natural_disaster&subtheme="
TYPE_LABELS = {
    "regulation": "法規", "administrative-rule": "行政規則", "interpretation": "函示",
    "announcement": "公告", "faq": "FAQ", "form": "表單／附件",
    "disaster-measure": "災害措施", "other-official": "其他官方資料",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value) -> str:
    return re.sub(r"[，。；：！？、（）「」『』【】《》〈〉／/%％﹪﹖?.,:;()\[\]{}]", "", re.sub(r"\s+", "", str(value or "").lower()))


def tokenize_query(value) -> list[str]:
    return [normalize_text(term) for term in re.split(r"\s+", str(value or "").strip()) if normalize_text(term)]


def normalize_document_number(value) -> str:
    return normalize_text(value).replace("字第", "").replace("號", "")


def event_date(record: dict) -> str:
    return record.get("publishedDate") or record.get("effectiveDate") or record.get("versionDate") or ""


def score(record: dict, query: str, loan_titles: dict[str, str], section_titles: dict[str, str]) -> int:
    raw_query = str(query or "")
    q = normalize_text(raw_query)
    terms = tokenize_query(raw_query)
    if not q or (q.isdigit() and len(q) < 6):
        return 0
    document = normalize_document_number(record.get("documentNumber"))
    document_query = normalize_document_number(raw_query)
    title = normalize_text(record.get("officialTitle"))
    programs = normalize_text(" ".join(loan_titles.get(value, "") for value in record.get("relatedLoanIds", [])))
    sections_text = normalize_text(" ".join(section_titles.get(value, "") for value in record.get("relatedSectionIds", [])))
    body = normalize_text(" ".join(str(value or "") for value in [
        record.get("officialTitle", ""), record.get("documentNumber", ""), record.get("officialAgency", ""),
        TYPE_LABELS.get(record.get("sourceType", ""), ""), record.get("publishedDate", ""),
        record.get("effectiveDate", ""), record.get("versionDate", ""), record.get("relationEvidence", ""),
        programs, sections_text,
    ]))
    if re.search(r"\d{6,}", document_query) and len(document_query) >= 6 and document_query == document:
        return 100000
    if q == title:
        return 90000
    if q in title:
        return 80000
    if q in programs:
        return 70000
    if q in sections_text:
        return 65000
    if q in body:
        return 50000
    return 30000 + len(terms) if len(terms) >= 2 and all(term in body for term in terms) else 0


def searchable_body(record: dict, loan_titles: dict[str, str], section_titles: dict[str, str]) -> str:
    programs = " ".join(loan_titles.get(value, "") for value in record.get("relatedLoanIds", []))
    sections_text = " ".join(section_titles.get(value, "") for value in record.get("relatedSectionIds", []))
    return normalize_text(" ".join(str(value or "") for value in [
        record.get("officialTitle", ""), record.get("documentNumber", ""), record.get("officialAgency", ""),
        TYPE_LABELS.get(record.get("sourceType", ""), ""), record.get("publishedDate", ""),
        record.get("effectiveDate", ""), record.get("versionDate", ""), record.get("relationEvidence", ""),
        programs, sections_text,
    ]))


def ranked(records: list[dict], query: str, loan_titles: dict[str, str], section_titles: dict[str, str]) -> list[dict]:
    results = [record for record in records if not query or score(record, query, loan_titles, section_titles) > 0]
    results = sorted(results, key=lambda record: record["id"])
    results = sorted(results, key=event_date, reverse=True)
    return sorted(results, key=lambda record: score(record, query, loan_titles, section_titles), reverse=True)


class LookupParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root_count = 0
        self.data_text = ""
        self.in_data = False
        self.cards: list[dict] = []
        self.card: dict | None = None
        self.selects: dict[str, set[str]] = {}
        self.select_name: str | None = None
        self.links: list[dict] = []
        self.body_text: list[str] = []
        self.disaster_classes: list[str] = []

    def handle_starttag(self, tag, attrs_list):
        attrs = {key: value or "" for key, value in attrs_list}
        self.body_text.append(attrs.get("aria-label", ""))
        if attrs.get("data-official-updates-lookup") is not None and tag == "section":
            self.root_count += 1
        if tag == "script" and attrs.get("data-official-updates-data") is not None:
            self.in_data = True
        if attrs.get("data-official-update-result") is not None:
            self.card = {"id": attrs.get("data-official-update-id", ""), "attrs": attrs, "text": [], "links": []}
            self.cards.append(self.card)
        if tag == "select" and attrs.get("name"):
            self.select_name = attrs["name"]
            self.selects.setdefault(self.select_name, set())
        if tag == "option" and self.select_name is not None:
            self.selects[self.select_name].add(attrs.get("value", ""))
        if tag == "a" and attrs.get("href"):
            link = {"href": attrs["href"], "target": attrs.get("target", ""), "rel": attrs.get("rel", ""), "card": self.card}
            self.links.append(link)
            if self.card is not None:
                self.card["links"].append(link)
        if "disaster-announcement" in attrs.get("class", "").split() or "data-disaster-filters" in attrs:
            self.disaster_classes.append(attrs.get("class", "") or "data-disaster-filters")

    def handle_data(self, data):
        self.body_text.append(data)
        if self.in_data:
            self.data_text += data
        if self.card is not None:
            self.card["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_data = False
        if tag == "select":
            self.select_name = None
        if tag == "li" and self.card is not None:
            self.card = None


def main() -> int:
    errors: list[str] = []
    updates = load(DATA / "official-updates.json")
    fixture = load(FIXTURE)
    loan_titles = {item["id"]: item["title"] for item in load(ROOT / "data/114/loan-programs.json")}
    section_titles = {item["id"]: item["title"] for item in sections()}
    ids = [item.get("id") for item in updates]
    if len(updates) != 20:
        errors.append(f"official update count is {len(updates)}, expected 20")
    if len(ids) != len(set(ids)):
        errors.append("duplicate official update ID")
    update_by_id = {item["id"]: item for item in updates}
    for item in updates:
        if item.get("sourceType") not in TYPE_LABELS:
            errors.append(f"invalid official update source type: {item.get('id')}")
        if not item.get("sourceUrl") or urlparse(item["sourceUrl"]).scheme != "https":
            errors.append(f"invalid official source URL: {item.get('id')}")
        if set(item.get("relatedLoanIds", [])) - set(loan_titles):
            errors.append(f"unknown related loan: {item.get('id')}")
        if set(item.get("relatedSectionIds", [])) - set(section_titles):
            errors.append(f"unknown related section: {item.get('id')}")

    path = SITE / "updates/index.html"
    parser = LookupParser()
    if not path.is_file():
        errors.append("missing generated /updates/ route")
    else:
        parser.feed(path.read_text(encoding="utf-8"))
    if parser.root_count != 1:
        errors.append("Official Updates lookup root missing or duplicated")
    if len(parser.cards) != len(updates):
        errors.append(f"rendered update card count is {len(parser.cards)}")
    if set(card["id"] for card in parser.cards) != set(ids):
        errors.append("rendered update IDs differ from official-updates.json")
    if not parser.data_text:
        errors.append("embedded official update lookup data missing")
    else:
        try:
            embedded = json.loads(parser.data_text)
            if {item.get("id") for item in embedded} != set(ids):
                errors.append("embedded lookup data IDs differ from source")
        except json.JSONDecodeError:
            errors.append("embedded official update lookup data is not JSON")
    expected_years = {event_date(item)[:4] for item in updates}
    expected_types = set(item["sourceType"] for item in updates)
    expected_programs = {loan_id for item in updates for loan_id in item.get("relatedLoanIds", [])}
    if parser.selects.get("year", set()) - {""} != expected_years:
        errors.append("year filter is not derived from official update dates")
    if parser.selects.get("type", set()) - {""} != expected_types:
        errors.append("type filter is not derived from official update data")
    if parser.selects.get("program", set()) - {""} != expected_programs:
        errors.append("program filter is not derived from relatedLoanIds")
    if not all("官方更新" in "".join(card["text"]) for card in parser.cards):
        errors.append("official update badge missing from a result card")
    for card in parser.cards:
        source_links = [link for link in card["links"] if urlparse(link["href"]).scheme == "https"]
        if not source_links:
            errors.append(f"official source link missing: {card['id']}")
        for link in source_links:
            if link["target"] != "_blank" or link["rel"] != "noopener noreferrer":
                errors.append(f"official source link attributes invalid: {card['id']}")
        item = update_by_id.get(card["id"], {})
        card_relations = set(card["attrs"].get("data-update-relations", "").split())
        if set(item.get("relatedLoanIds", [])) - card_relations:
            errors.append(f"rendered program relation missing: {card['id']}")
        for loan_id in item.get("relatedLoanIds", []):
            expected = f"loans/{loan_id}/index.html"
            if not any(expected in link["href"] for link in card["links"]):
                errors.append(f"handbook loan link missing: {card['id']} -> {loan_id}")

    for query in fixture["queries"]:
        results = ranked(updates, query["query"], loan_titles, section_titles)
        expected_ids = query.get("expectedIds")
        if expected_ids is not None and [item["id"] for item in results] != expected_ids:
            errors.append(f"fixture result mismatch: {query['name']}")
        if query.get("expectedTopId") and (not results or results[0]["id"] != query["expectedTopId"]):
            errors.append(f"fixture top result mismatch: {query['name']}")

    non_contiguous = [item for item in fixture["queries"] if item.get("nonContiguous")]
    if not non_contiguous:
        errors.append("missing non-contiguous multi-keyword fixture")
    for item in non_contiguous:
        target = update_by_id.get(item.get("targetId"))
        terms = tokenize_query(item.get("query"))
        body = searchable_body(target, loan_titles, section_titles) if target else ""
        concatenated = normalize_text(item.get("concatenatedPhrase", ""))
        if not target or len(terms) < 2 or not all(term in body for term in terms):
            errors.append(f"non-contiguous fixture tokens are not evidenced: {item['name']}")
        if concatenated and concatenated in body:
            errors.append(f"non-contiguous fixture phrase is unexpectedly contiguous: {item['name']}")
        if not any(record["id"] == item.get("targetId") for record in ranked(updates, item["query"], loan_titles, section_titles)):
            errors.append(f"non-contiguous fixture target did not match: {item['name']}")
    negative_and = [item for item in fixture["queries"] if item.get("name") == "negative-and" and item.get("expectedIds") == []]
    if not negative_and or any(len(tokenize_query(item["query"])) < 2 for item in negative_and):
        errors.append("missing negative multi-keyword AND fixture")
    whitespace = fixture.get("whitespaceVariants", [])
    if len(whitespace) >= 2:
        baseline = [record["id"] for record in ranked(updates, whitespace[0], loan_titles, section_titles)]
        for variant in whitespace[1:]:
            if [record["id"] for record in ranked(updates, variant, loan_titles, section_titles)] != baseline:
                errors.append(f"whitespace variant mismatch: {variant!r}")
    for item in fixture["filters"]:
        results = updates[:]
        if item.get("program"):
            results = [record for record in results if item["program"] in record.get("relatedLoanIds", [])]
        if item.get("type"):
            results = [record for record in results if item["type"] == record.get("sourceType")]
        if item.get("year"):
            results = [record for record in results if event_date(record).startswith(item["year"])]
        ordered = sorted(results, key=lambda record: record["id"])
        ordered = sorted(ordered, key=event_date, reverse=True)
        if [record["id"] for record in ordered] != item["expectedIds"]:
            errors.append(f"fixture filter mismatch: {item['name']}")

    search_index = load(SITE / "assets/data/search-index.json")
    if len(search_index) != 507:
        errors.append("handbook search index is not 507")
    if any(item["id"] in {record.get("id") for record in search_index} for item in updates):
        errors.append("official update leaked into handbook search index")
    coverage = load(DATA / "coverage.json")["officialUpdateReview"]
    if coverage.get("coverageStatus") != "partial" or coverage.get("verifiedThrough") is not None:
        errors.append("coverage changed from partial/null")
    js = (ROOT / "assets/js/official-updates-lookup.js").read_text(encoding="utf-8")
    for required in ("normalizeOfficialDocumentNumber", "tokenizeQuery", "replace(/字第/g", "replace(/號/g", "URLSearchParams", "popstate", "data-official-update"):
        if required not in js:
            errors.append(f"lookup JS missing required behavior: {required}")
    if "const rawQuery = String(query || \"\");" not in js or "const terms = tokenizeQuery(rawQuery);" not in js:
        errors.append("lookup JS does not tokenize from raw query boundaries")
    if "split(/\\s+/)" not in js:
        errors.append("lookup JS whitespace tokenization is incomplete")
    if "terms.length >= 2 && terms.every((term) => body.includes(term))" not in js:
        errors.append("lookup JS does not enforce multi-keyword AND matching")
    if re.search(r"const terms = q\.split", js):
        errors.append("lookup JS tokenizes the already-normalized query")
    py = (ROOT / "scripts/validate_official_updates_lookup.py").read_text(encoding="utf-8")
    if "raw_query = str(query or \"\")" not in py or "terms = tokenize_query(raw_query)" not in py:
        errors.append("Python reference does not tokenize from raw query boundaries")
    if 're.split(r"\\s+"' not in py:
        errors.append("Python reference whitespace tokenization is incomplete")
    if "len(terms) >= 2 and all(term in body for term in terms)" not in py:
        errors.append("Python reference does not enforce multi-keyword AND matching")
    if re.search(r"fetch\(|XMLHttpRequest|https?://", js):
        errors.append("lookup JS introduces network search")
    manual = load(ROOT / "data/114/manual.json")
    package = load(ROOT / "package.json")
    if manual.get("digitalRevision") != "114.0.0-beta.3.1.1" or package.get("version") != "114.0.0-beta.3.1.1":
        errors.append("version metadata is not beta.3.1.1")
    disaster = SITE / "updates/disasters/index.html"
    if disaster.is_file():
        disaster_text = disaster.read_text(encoding="utf-8")
        if GATEWAY not in disaster_text or "disaster-announcement" in disaster_text or "data-disaster-filters" in disaster_text:
            errors.append("disaster gateway policy changed")
    else:
        errors.append("missing disaster gateway route")

    print(json.dumps({
        "status": "OFFICIAL UPDATES LOOKUP VALIDATION PASSED" if not errors else "OFFICIAL UPDATES LOOKUP VALIDATION FAILED",
        "records": len(updates), "renderedCards": len(parser.cards), "fixtureQueries": len(fixture["queries"]),
        "fixtureFilters": len(fixture["filters"]), "searchIndex": len(search_index), "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
