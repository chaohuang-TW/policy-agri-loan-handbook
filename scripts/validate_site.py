#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate repository data, built HTML, links, privacy, and Project Pages paths."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
EXPECTED_SHA = "0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54"
BASE = "https://chaohuang-tw.github.io/policy-agri-loan-handbook/"
IDENTITY = "本網站為公開資料數位閱讀與實務索引版"
FOOTER = "本網站提供資料閱讀、搜尋與索引"


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.h1 = 0
        self.canonical = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data:
            self.ids.append(data["id"])
        if tag == "h1":
            self.h1 += 1
        if tag in {"a", "link", "script", "img"}:
            value = data.get("href") or data.get("src")
            if value:
                self.links.append((tag, value, data))
        if tag == "link" and data.get("rel") == "canonical":
            self.canonical.append(data.get("href", ""))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_canonical(path: Path) -> str:
    relative = path.relative_to(SITE).as_posix()
    return BASE + (relative[:-10] if relative.endswith("index.html") else relative)


def main() -> int:
    errors = []
    source = ROOT / "source/policy-agri-loan-handbook-114.pdf"
    download = SITE / "downloads/policy-agri-loan-handbook-114.pdf"
    for path, label in ((source, "source"), (download, "download")):
        if not path.is_file():
            errors.append(f"missing {label} PDF")
        elif len(PdfReader(str(path)).pages) != 359:
            errors.append(f"{label} PDF is not 359 pages")
        elif digest(path) != EXPECTED_SHA:
            errors.append(f"{label} PDF SHA-256 mismatch")
    if source.is_file() and download.is_file() and source.read_bytes() != download.read_bytes():
        errors.append("source and download PDFs are not byte-identical")
    versions = json.loads((ROOT / "data/versions.json").read_text(encoding="utf-8"))
    pages = json.loads((ROOT / "data/114/pages.json").read_text(encoding="utf-8"))
    loans = json.loads((ROOT / "data/114/loan-programs.json").read_text(encoding="utf-8"))
    toc = json.loads((ROOT / "data/114/toc.json").read_text(encoding="utf-8"))
    search = json.loads((SITE / "assets/data/search-index.json").read_text(encoding="utf-8"))
    if versions.get("currentVersion") != "114" or versions["versions"][0].get("pdfPages") != 359:
        errors.append("versions.json current version or page count is invalid")
    if len(pages) != 359:
        errors.append("pages.json does not contain 359 pages")
    if len(loans) != 23 or len({item["id"] for item in loans}) != 23:
        errors.append("loan program index does not contain 23 unique items")
    if versions["versions"][0].get("digitalRevision") != "114.0.0-beta.2.4.1" or versions["versions"][0].get("status") != "Beta":
        errors.append("versions.json is not marked 114.0.0-beta.2.4.1 Beta")
    required_toc = ["辦理政策性農業專案貸款辦法", "農業發展基金貸款相關規定", "農業天然災害救助辦法", "全國農業金庫貸款", "政策性農業專案貸款增修正規定常見問題"]
    toc_text = json.dumps(toc, ensure_ascii=False)
    for value in required_toc:
        if value not in toc_text:
            errors.append(f"required TOC item missing: {value}")
    if not search:
        errors.append("search index is empty")
    html_files = sorted(SITE.rglob("*.html"))
    for path in html_files:
        document = path.read_text(encoding="utf-8")
        parser = Parser(); parser.feed(document)
        relative = path.relative_to(SITE).as_posix()
        if parser.h1 != 1:
            errors.append(f"H1 count {parser.h1}: {relative}")
        if len(parser.ids) != len(set(parser.ids)):
            errors.append(f"duplicate id: {relative}")
        if parser.canonical != [expected_canonical(path)]:
            errors.append(f"canonical mismatch: {relative}")
        if IDENTITY not in document or FOOTER not in document or "資料版本：114年度" not in document:
            errors.append(f"version or disclaimer missing: {relative}")
        if "114.0.0-beta.2.4.1" not in document or "Beta" not in document:
            errors.append(f"Beta revision label missing: {relative}")
        if re.search(r'''(?:href|src)=["']/''', document):
            errors.append(f"domain-root absolute path: {relative}")
        if re.search(r"google-analytics|googletagmanager|segment\.com|openai|anthropic|<form[^>]+action=", document, re.I):
            errors.append(f"analytics, AI API, or form endpoint: {relative}")
        for tag, url, attrs in parser.links:
            parsed = urlsplit(url)
            if parsed.scheme in {"http", "https"} and (tag == "script" or (tag == "link" and attrs.get("rel") == "stylesheet")):
                errors.append(f"external JavaScript or CSS: {relative}")
            if parsed.scheme in {"http", "https", "mailto"} or url.startswith("#"):
                continue
            if parsed.path.startswith("/"):
                errors.append(f"root-relative URL in {relative}: {url}")
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            try:
                target.relative_to(SITE.resolve())
            except ValueError:
                errors.append(f"link escapes site in {relative}: {url}")
                continue
            if not target.exists():
                errors.append(f"broken internal link in {relative}: {url}")
            if tag == "img" and not all(name in attrs for name in ("alt", "width", "height", "loading", "decoding")):
                errors.append(f"image attributes missing in {relative}: {url}")
    for record in search:
        parsed = urlsplit(record["url"])
        target = SITE / unquote(parsed.path)
        if not target.is_file():
            errors.append(f"search URL target missing: {record['url']}")
        elif parsed.fragment and record.get("type") == "原文頁面" and f'id="{parsed.fragment}"' not in target.read_text(encoding="utf-8"):
            errors.append(f"search anchor missing: {record['url']}")
    for required in ("index.html", "versions/114/index.html", "quick-index/index.html", "loans/index.html",
                     "interpretations/index.html", "faq/index.html", "forms/index.html", "versions/index.html"):
        if not (SITE / required).is_file():
            errors.append(f"required public page missing: {required}")
    keyword_results = {}
    for keyword in ("青壯年農民", "農機貸款", "電子商務", "寬緩期", "農業天然災害", "週轉金", "購買耕地", "函釋", "農業保險", "中小企業認定標準"):
        count = sum(keyword.casefold() in record["text"].casefold() for record in search)
        keyword_results[keyword] = count
        if count < 1:
            errors.append(f"no search result for required keyword: {keyword}")
    forbidden = [
        "農業信用保證" + "業務作業手冊", "acgf-guarantee-manual-" + "115" + "-04.pdf",
        "115" + "-04", "203" + "頁", "第一篇　" + "保證", "第二篇　" + "期中管理",
        "第三篇　" + "代位清償", "第四篇　" + "代位清償後之債權追索",
    ]
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".venv" in path.parts or path.suffix.lower() in {".pdf", ".webp", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in forbidden:
            if token in text:
                errors.append(f"template residue {token}: {path.relative_to(ROOT)}")
    if errors:
        print("SITE VALIDATION FAILED")
        for error in errors:
            print("- " + error)
        return 1
    print("SITE VALIDATION PASSED")
    print(f"- HTML pages: {len(html_files)}")
    print(f"- Search records: {len(search)}")
    print("- Required keyword results: " + ", ".join(f"{key}={value}" for key, value in keyword_results.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
