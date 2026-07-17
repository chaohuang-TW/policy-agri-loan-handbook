#!/usr/bin/env python3
"""Prove that display reflow changes whitespace only, including built text pages."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from display_text import non_whitespace_characters, normalize_display_text

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    pages = json.loads((ROOT / "data/114/pages.json").read_text(encoding="utf-8"))
    errors = []
    rendered = 0
    for page in pages:
        raw = page["rawText"]
        display = "".join(normalize_display_text(raw))
        if non_whitespace_characters(display) != non_whitespace_characters(raw):
            errors.append(f"non-whitespace mismatch in PDF page {page['pdfPage']}")
        if page["renderMode"] != "text":
            continue
        rendered += 1
        path = ROOT / "site/versions/114/pages" / f"page-{page['pdfPage']:03d}.html"
        document = path.read_text(encoding="utf-8")
        match = re.search(r'<div class="display-text">(.*?)</div>', document, re.S)
        if not match:
            errors.append(f"display-text missing in {path.relative_to(ROOT)}")
            continue
        visible = re.sub(r"<[^>]+>", "", match.group(1))
        if non_whitespace_characters(html.unescape(visible)) != non_whitespace_characters(raw):
            errors.append(f"built display mismatch in PDF page {page['pdfPage']}")
    if errors:
        print("DISPLAY TEXT VALIDATION FAILED")
        for error in errors:
            print("- " + error)
        return 1
    print("DISPLAY TEXT VALIDATION PASSED")
    print(f"- Source pages checked: {len(pages)}")
    print(f"- Built reflowed pages checked: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
