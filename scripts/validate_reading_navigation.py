#!/usr/bin/env python3
"""Validate generated reading-navigation HTML, anchors, evidence and sequence links."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from reading_navigation import TASK_DEFINITIONS, task_mappings

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
LOANS = json.loads((ROOT / "data/114/loan-programs.json").read_text(encoding="utf-8"))
PAGES = json.loads((ROOT / "data/114/pages.json").read_text(encoding="utf-8"))
RELATIONSHIPS = json.loads((ROOT / "data/114/content-relationships.json").read_text(encoding="utf-8"))
SEARCH_INDEX = json.loads((SITE / "assets/data/search-index.json").read_text(encoding="utf-8"))


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.id_tags: dict[str, str] = {}
        self.links: list[dict] = []
        self.toc_links: list[dict] = []
        self.task_links: list[dict] = []
        self.prev_links: list[dict] = []
        self.next_links: list[dict] = []
        self.evidence_links: list[dict] = []
        self.stack: list[tuple[str, dict[str, str]]] = []

    def _in_class(self, class_name: str) -> bool:
        return any(class_name in attrs.get("class", "").split() for _, attrs in self.stack)

    def handle_starttag(self, tag: str, attrs_list) -> None:
        attrs = {key: value or "" for key, value in attrs_list}
        if "id" in attrs:
            self.ids.append(attrs["id"])
            self.id_tags.setdefault(attrs["id"], tag)
        if tag == "a" and "href" in attrs:
            source_block = next((item_attrs.get("id") for item_tag, item_attrs in reversed(self.stack) if item_attrs.get("id", "").startswith("source-page-")), None)
            link = {"href": attrs["href"], "attrs": attrs, "tag": tag, "sourceBlock": source_block}
            self.links.append(link)
            if self._in_class("page-toc"):
                self.toc_links.append(link)
            if "data-reading-task" in attrs:
                self.task_links.append(link)
            if "data-reading-prev" in attrs:
                self.prev_links.append(link)
            if "data-reading-next" in attrs:
                self.next_links.append(link)
            if "evidence-link" in attrs.get("class", "").split():
                self.evidence_links.append(link)
        self.stack.append((tag, attrs))

    def handle_startendtag(self, tag: str, attrs_list) -> None:
        self.handle_starttag(tag, attrs_list)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def parse(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def resolve_html_target(path: Path, href: str) -> tuple[Path | None, str]:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return None, parsed.fragment
    target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
    try:
        target.relative_to(SITE.resolve())
    except ValueError:
        return None, parsed.fragment
    return target if target.suffix == ".html" else None, parsed.fragment


def fragment(href: str) -> str:
    return urlsplit(href).fragment


def main() -> int:
    errors: list[str] = []
    html_files = sorted(SITE.rglob("*.html"))
    parsers = {path: parse(path) for path in html_files}
    id_sets = {path: set(parser.ids) for path, parser in parsers.items()}

    if len(html_files) != 399:
        errors.append(f"HTML page count changed: expected 399, got {len(html_files)}")

    total_hash_links = 0
    broken_hash_links = 0
    duplicate_ids = 0
    evidence_total = evidence_valid = evidence_invalid = 0
    prev_next_total = self_links = ordering_errors = 0
    task_nav_pages = 0
    task_nav_items = 0
    missing_task_targets = 0
    fake_task_mappings = 0
    section_toc_pages = 0
    section_toc_items = 0
    missing_toc_targets = 0
    section_order_errors = 0

    for path, parser in parsers.items():
        if len(parser.ids) != len(set(parser.ids)):
            duplicate_ids += len(parser.ids) - len(set(parser.ids))
            errors.append(f"duplicate id: {path.relative_to(SITE)}")
        for link in parser.links:
            target, target_fragment = resolve_html_target(path, link["href"])
            if not target_fragment or target is None:
                continue
            total_hash_links += 1
            if not target.is_file() or target_fragment not in id_sets.get(target, set()):
                broken_hash_links += 1
                errors.append(f"broken hash link: {path.relative_to(SITE)} -> {link['href']}")

        for link in parser.evidence_links:
            evidence_total += 1
            target, _ = resolve_html_target(path, link["href"])
            match = re.search(r"page-(\d{3})\.html$", urlsplit(link["href"]).path)
            page_number = int(match.group(1)) if match else 0
            if target is not None and target.is_file() and 1 <= page_number <= 359:
                evidence_valid += 1
            else:
                evidence_invalid += 1
                errors.append(f"invalid evidence link: {path.relative_to(SITE)} -> {link['href']}")

        if path.relative_to(SITE).as_posix().startswith("loans/") and path.name == "index.html" and path.parent.name != "loans":
            task_nav = [link for link in parser.task_links]
            task_nav_pages += 1
            task_nav_items += len(task_nav)
            loan_id = path.parent.name
            loan = next((item for item in LOANS if item["id"] == loan_id), None)
            if not loan:
                errors.append(f"unknown loan navigation page: {path.relative_to(SITE)}")
            else:
                expected = {mapping["taskKey"]: mapping for mapping in task_mappings(loan, PAGES)}
                actual = {}
                for link in task_nav:
                    key = link["attrs"].get("data-reading-task", "")
                    actual[key] = link
                    target_id = fragment(link["href"])
                    if not target_id or target_id not in parser.id_tags:
                        missing_task_targets += 1
                        errors.append(f"loan task target missing: {path.relative_to(SITE)} -> {link['href']}")
                    elif parser.id_tags[target_id] != "h3":
                        errors.append(f"loan task target is not a heading: {path.relative_to(SITE)} -> {link['href']}")
                if set(actual) != set(expected):
                    fake_task_mappings += len(set(actual) ^ set(expected))
                    errors.append(f"loan task mapping mismatch: {path.relative_to(SITE)} expected={sorted(expected)} actual={sorted(actual)}")

            source_blocks = [id_value for id_value in parser.ids if id_value.startswith("source-page-")]
            for index, link in enumerate(parser.prev_links):
                prev_next_total += 1
                target_id = fragment(link["href"])
                if target_id == "source-page-" + path.parent.name:
                    self_links += 1
                if target_id not in parser.id_tags:
                    errors.append(f"previous target missing: {path.relative_to(SITE)} -> {link['href']}")
                elif target_id not in source_blocks[: max(0, len(source_blocks) - 1)]:
                    ordering_errors += 1
                    errors.append(f"previous target out of source order: {path.relative_to(SITE)} -> {link['href']}")
            for link in parser.next_links:
                prev_next_total += 1
                target_id = fragment(link["href"])
                if target_id not in parser.id_tags:
                    errors.append(f"next target missing: {path.relative_to(SITE)} -> {link['href']}")
                elif target_id not in source_blocks[1:]:
                    ordering_errors += 1
                    errors.append(f"next target out of source order: {path.relative_to(SITE)} -> {link['href']}")
            expected_prev = max(0, len(source_blocks) - 1)
            expected_next = max(0, len(source_blocks) - 1)
            for link in parser.prev_links:
                target_id = fragment(link["href"])
                if link.get("sourceBlock") and target_id == link["sourceBlock"]:
                    self_links += 1
                    errors.append(f"previous self-link: {path.relative_to(SITE)} -> {link['href']}")
                if link.get("sourceBlock") in source_blocks:
                    current_index = source_blocks.index(link["sourceBlock"])
                    if current_index == 0 or target_id != source_blocks[current_index - 1]:
                        ordering_errors += 1
                        errors.append(f"previous sequence mismatch: {path.relative_to(SITE)} -> {link['href']}")
            for link in parser.next_links:
                target_id = fragment(link["href"])
                if link.get("sourceBlock") and target_id == link["sourceBlock"]:
                    self_links += 1
                    errors.append(f"next self-link: {path.relative_to(SITE)} -> {link['href']}")
                if link.get("sourceBlock") in source_blocks:
                    current_index = source_blocks.index(link["sourceBlock"])
                    if current_index + 1 >= len(source_blocks) or target_id != source_blocks[current_index + 1]:
                        ordering_errors += 1
                        errors.append(f"next sequence mismatch: {path.relative_to(SITE)} -> {link['href']}")
            if len(parser.prev_links) != expected_prev or len(parser.next_links) != expected_next:
                ordering_errors += 1
                errors.append(f"loan sequence cardinality mismatch: {path.relative_to(SITE)}")

        if path.relative_to(SITE).as_posix().startswith("versions/114/sections/") and path.name == "index.html":
            section_toc_pages += 1
            if not parser.toc_links:
                errors.append(f"section has no 本頁內容 TOC: {path.relative_to(SITE)}")
            section_toc_items += len(parser.toc_links)
            positions = [list(parser.id_tags).index(fragment(link["href"])) if fragment(link["href"]) in parser.id_tags else -1 for link in parser.toc_links]
            if any(position < 0 for position in positions):
                missing_toc_targets += sum(position < 0 for position in positions)
                errors.append(f"section TOC target missing: {path.relative_to(SITE)}")
            if positions != sorted(positions):
                section_order_errors += 1
                errors.append(f"section TOC order mismatch: {path.relative_to(SITE)}")

    expected_sections = {section["id"] for section in RELATIONSHIPS["sections"]}
    actual_sections = {path.parent.name for path in SITE.glob("versions/114/sections/*/index.html")}
    if actual_sections != expected_sections:
        errors.append(f"section pages mismatch: expected={sorted(expected_sections)} actual={sorted(actual_sections)}")
    if section_toc_pages != 7:
        errors.append(f"section TOC page count is {section_toc_pages}, expected 7")
    if task_nav_pages != 23:
        errors.append(f"loan task navigation page count is {task_nav_pages}, expected 23")

    # Search deep links are checked against the same deterministic mapping as
    # the renderer.  A source page with exactly one task mapping must resolve
    # to that loan page and task anchor; every other source result keeps its
    # evidence-page URL.
    page_by_pdf = {page["pdfPage"]: page for page in PAGES}
    for record in SEARCH_INDEX:
        if record.get("type") != "原文頁面":
            continue
        page = page_by_pdf.get(record.get("pdfPage"))
        if not page:
            errors.append(f"search page record missing source page: {record.get('id')}")
            continue
        owner = next((loan for loan in LOANS if page.get("printedPage") is not None and loan["sourceStartPage"] <= page["printedPage"] <= loan["sourceEndPage"]), None)
        expected_path = f"versions/114/pages/page-{page['pdfPage']:03d}.html#pdf-page-{page['pdfPage']}"
        if owner:
            mappings = [item for item in task_mappings(owner, PAGES) if item["pdfPage"] == page["pdfPage"]]
            if len(mappings) == 1:
                expected_path = f"{owner['detailUrl']}#{mappings[0]['anchor']}"
        if record.get("url") != expected_path:
            errors.append(f"search deep link mismatch: {record.get('id')} expected={expected_path} actual={record.get('url')}")

    result = {
        "status": "READING NAVIGATION VALIDATION PASSED" if not errors else "READING NAVIGATION VALIDATION FAILED",
        "loanPages": task_nav_pages,
        "taskNavItems": task_nav_items,
        "hiddenUnavailableTasks": len(LOANS) * len(TASK_DEFINITIONS) - task_nav_items,
        "taskMissingTargets": missing_task_targets,
        "fakeTaskMappings": fake_task_mappings,
        "sectionPages": section_toc_pages,
        "sectionTocItems": section_toc_items,
        "tocMissingTargets": missing_toc_targets,
        "sectionOrderErrors": section_order_errors,
        "totalHashLinks": total_hash_links,
        "brokenHashLinks": broken_hash_links,
        "duplicateIds": duplicate_ids,
        "totalEvidenceLinks": evidence_total,
        "validEvidenceLinks": evidence_valid,
        "invalidEvidenceLinks": evidence_invalid,
        "prevNextLinks": prev_next_total,
        "selfLinks": self_links,
        "orderingErrors": ordering_errors,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
