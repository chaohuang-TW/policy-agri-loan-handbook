#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-extract 20 representative source locations and compare stored text."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader

from extract_manual import display_text

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "source" / "policy-agri-loan-handbook-114.pdf"
PAGES = json.loads((ROOT / "data/114/pages.json").read_text(encoding="utf-8"))
SAMPLES = [1, 3, 32, 47, 96, 112, 122, 148, 160, 187, 211, 224, 244, 272, 299, 302, 335, 350, 355, 359]


def main() -> int:
    reader = PdfReader(str(PDF))
    failures = []
    for pdf_page in SAMPLES:
        printed = pdf_page - 2 if pdf_page >= 3 else None
        extracted = display_text(reader.pages[pdf_page - 1].extract_text() or "", printed)
        stored = PAGES[pdf_page - 1]
        if stored["pdfPage"] != pdf_page or stored["printedPage"] != printed or stored["rawText"] != extracted:
            failures.append(pdf_page)
    if failures:
        print("CONTENT AUDIT FAILED: " + ", ".join(map(str, failures)))
        return 1
    print("CONTENT AUDIT PASSED: 20 representative PDF locations")
    print("PDF pages: " + ", ".join(map(str, SAMPLES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
