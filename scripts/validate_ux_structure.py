#!/usr/bin/env python3
"""Validate the beta.2.6 user journey and information architecture."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.h1 = 0
        self.canonicals = 0

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "link" and data.get("rel") == "canonical":
            self.canonicals += 1


def main() -> int:
    errors = []
    home = (SITE / "index.html").read_text(encoding="utf-8")
    base = (ROOT / "templates/base.html").read_text(encoding="utf-8")
    search_js = (ROOT / "assets/js/search.js").read_text(encoding="utf-8")
    shortcuts = json.loads((ROOT / "data/114/navigation-shortcuts.json").read_text(encoding="utf-8"))
    if home.count('class="entry"') != 4:
        errors.append("homepage does not contain exactly four primary entries")
    if home.count('class="entry"') == 8:
        errors.append("homepage still contains eight equal entries")
    if len([item for item in shortcuts if item["kind"] == "popular"]) != 8:
        errors.append("common-query shortcut count is not eight")
    if "data-keyword" not in home or "button[data-keyword], button[data-query]" not in search_js:
        errors.append("shortcut buttons do not have a real JavaScript handler")
    for token in ("data-menu-toggle", 'aria-controls="mobile-menu"', 'id="mobile-menu"', "data-open-search"):
        if token not in base:
            errors.append(f"mobile/header control missing: {token}")
    if '<nav id="mobile-menu"' not in base or "hidden" not in base.split('<nav id="mobile-menu"', 1)[1].split(">", 1)[0]:
        errors.append("mobile menu is not closed by default")
    if "floating-tools" in base or "data-print-section" in base:
        errors.append("legacy floating search or print tools remain")
    if "data-back-to-top" not in base:
        errors.append("back-to-top control missing")
    if "manual/index.html" in search_js:
        errors.append("invalid fallback manual/index.html remains")
    if "依需求找資料" not in home or "原書完整目錄" not in home:
        errors.append("new navigation names are missing")

    section_paths = sorted((SITE / "versions/114/sections").glob("*/index.html"))
    if len(section_paths) != 7:
        errors.append(f"section count is {len(section_paths)}, expected 7")
    for path in section_paths:
        text = path.read_text(encoding="utf-8")
        if "<h2>本篇頁面</h2>" in text or "<summary>本篇頁面</summary>" in text:
            errors.append(f"page dump remains primary: {path.parent.name}")
        if 'class="source-page-list"' not in text:
            errors.append(f"source details missing: {path.parent.name}")
    loan_programs = (SITE / "versions/114/sections/loan-programs/index.html").read_text(encoding="utf-8")
    if loan_programs.count("<article><h3>") != 19:
        errors.append("loan-programs does not contain 19 loan entries")
    if "faq-hub" not in (SITE / "versions/114/sections/amendment-faq/index.html").read_text(encoding="utf-8"):
        errors.append("FAQ section is not FAQ-led")

    loan_paths = sorted((SITE / "loans").glob("*/index.html"))
    if len(loan_paths) != 23:
        errors.append(f"loan detail count is {len(loan_paths)}, expected 23")
    for path in loan_paths:
        text = path.read_text(encoding="utf-8")
        for token in ("在本貸款中搜尋", "貸款原文", "相關函釋", "相關書表", 'class="source-page-list"'):
            if token not in text:
                errors.append(f"{token} missing: {path.parent.name}")

    html_files = sorted(SITE.rglob("*.html"))
    if len(html_files) != 397:
        errors.append(f"HTML count is {len(html_files)}, expected 397")
    for path in html_files:
        parser = Structure()
        parser.feed(path.read_text(encoding="utf-8"))
        if parser.h1 != 1:
            errors.append(f"H1 count {parser.h1}: {path.relative_to(SITE)}")
        if len(parser.ids) != len(set(parser.ids)):
            errors.append(f"duplicate IDs: {path.relative_to(SITE)}")
        if parser.canonicals != 1:
            errors.append(f"canonical count {parser.canonicals}: {path.relative_to(SITE)}")
    if len(list((SITE / "versions/114/pages").glob("page-*.html"))) != 359:
        errors.append("359 page URLs were not preserved")

    absolute_patterns = ("/" + "Users/", "/" + "private/", ".cache/" + "codex-runtimes")
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix in {".pdf", ".webp", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in absolute_patterns:
            if pattern in text:
                errors.append(f"local absolute path remains: {path.relative_to(ROOT)}")
    if errors:
        print("UX STRUCTURE VALIDATION FAILED")
        for error in errors:
            print("- " + error)
        return 1
    print("UX STRUCTURE VALIDATION PASSED: 4 primary entries, 7 semantic hubs, 23 loan work pages, 359 evidence pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
