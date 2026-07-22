#!/usr/bin/env python3
"""Static and deterministic regression checks for the browser search experience."""
from __future__ import annotations
import json, re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"
SITE = ROOT / "site"
TYPES = {"原文頁面", "貸款索引", "函釋", "常見問答", "書表附件", "附錄附件"}

class Counter(HTMLParser):
    def __init__(self): super().__init__(); self.dialog = 0; self.openers = 0; self.top = 0; self.prints = 0; self.h1 = 0; self.ids = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs); self.ids.append(attrs.get("id")) if attrs.get("id") else None
        if tag == "dialog" and attrs.get("id") == "manual-search-dialog": self.dialog += 1
        if "data-open-search" in attrs: self.openers += 1
        if "data-back-to-top" in attrs: self.top += 1
        if "data-print-section" in attrs: self.prints += 1
        if tag == "h1": self.h1 += 1

def fail(message): raise SystemExit(f"SEARCH EXPERIENCE VALIDATION FAILED: {message}")

def main():
    records = json.loads((SITE / "assets/data/search-index.json").read_text())
    concepts = json.loads((DATA / "search-concepts.json").read_text())
    intents = json.loads((DATA / "search-intents.json").read_text())
    if len(records) != 507: fail(f"expected 507 records, got {len(records)}")
    if sum(sum(r.get("type") == t for r in records) for t in TYPES) != 507: fail("type totals do not equal 507")
    if len({c["id"] for c in concepts}) != len(concepts) or any(len(c.get("terms", [])) < 2 or any(not str(t).strip() for t in c["terms"]) for c in concepts): fail("invalid concepts")
    if any(not set(i.get("preferredTypes", [])).issubset(TYPES) for i in intents): fail("invalid intent type")
    if any(not r.get("scope") or not r.get("url") or not r.get("id") for r in records): fail("record missing scope/url/id")
    if len({(r["id"], r["url"]) for r in records}) != len(records): fail("duplicate id/url")
    html_files = list(SITE.rglob("*.html"))
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        c = Counter(); c.feed(text)
        if c.dialog != 1 or c.openers != 1 or c.top != 1: fail(f"tool topology {path}")
        if "results.innerHTML" in text or "innerHTML =" in text: fail(f"unsafe result rendering {path}")
        if len(c.ids) != len(set(c.ids)): fail(f"duplicate ids {path}")
    js = (ROOT / "assets/js/search.js").read_text()
    if "results.innerHTML" in js or "innerHTML =" in js or any(x in js for x in ("localStorage", "sessionStorage", "document.cookie")): fail("unsafe or persistent search implementation")
    if "fetch(" not in js or "Ctrl" not in (ROOT / "templates/base.html").read_text(): fail("missing local fetch or shortcut")
    if "#286b57" not in (ROOT / "templates/base.html").read_text(): fail("theme-color mismatch")
    expected = ["青農", "買農地", "寬限期", "農機申請書", "農授金字第0955080181號", "天災", "農企業", "電商", "復耕", "週轉金", "常見問題", "申請書"]
    corpus = "\n".join(r["title"] + " " + r["text"] for r in records)
    for query in expected:
        if query == "常見問題": ok = "常見問答" in corpus
        elif query == "青農": ok = "青壯年農民" in corpus
        elif query == "買農地": ok = "購買耕地" in corpus
        elif query == "寬限期": ok = "寬緩期" in corpus
        elif query == "電商": ok = "電子商務" in corpus
        else: ok = query in corpus or (query == "農機申請書" and "農機貸款" in corpus)
        if not ok: fail(f"fixed query unavailable: {query}")
    print(f"SEARCH EXPERIENCE VALIDATION PASSED: {len(records)} records, {len(html_files)} HTML pages, {len(concepts)} concepts, {len(intents)} intents")

if __name__ == "__main__": main()
