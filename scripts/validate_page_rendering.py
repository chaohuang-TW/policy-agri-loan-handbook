#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate text, preview, and hybrid modes for all 359 source pages."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageStat
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PDF = ROOT / "source/policy-agri-loan-handbook-114.pdf"
EXPECTED_SHA = "0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    errors = []
    pages = json.loads((ROOT / "data/114/pages.json").read_text(encoding="utf-8"))
    rules = json.loads((ROOT / "data/114/page-rendering-rules.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "assets/page-previews/114/manifest.json").read_text(encoding="utf-8"))
    configured = {item["pdfPage"]: item for item in rules["pages"]}
    preview_manifest = {item["pdfPage"]: item for item in manifest}
    if len(PdfReader(str(PDF)).pages) != 359:
        errors.append("source PDF page count is not 359")
    if digest(PDF) != EXPECTED_SHA:
        errors.append("source PDF SHA-256 mismatch")
    if len(pages) != 359 or [p["pdfPage"] for p in pages] != list(range(1, 360)):
        errors.append("pages.json is not a complete ordered 359-page map")
    if rules.get("defaultMode") != "text" or rules.get("preview") != {"format": "webp", "width": 1400, "quality": 80}:
        errors.append("rendering defaults or preview settings are invalid")
    allowed = {"text", "preview", "hybrid"}
    modes = {mode: [p["pdfPage"] for p in pages if p["renderMode"] == mode] for mode in allowed}
    if any(p["renderMode"] not in allowed for p in pages):
        errors.append("illegal renderMode")
    expected_previews = sorted(modes["preview"] + modes["hybrid"])
    if sorted(preview_manifest) != expected_previews or len(preview_manifest) != len(expected_previews):
        errors.append("preview manifest does not exactly match preview/hybrid pages")
    source_doc = pdfium.PdfDocument(PDF)
    for number in expected_previews:
        item = preview_manifest.get(number)
        if not item:
            continue
        expected_name = f"pdf-page-{number:03d}.webp"
        if item.get("file") != expected_name or item.get("renderMode") != pages[number - 1]["renderMode"]:
            errors.append(f"preview metadata mismatch: {number}")
            continue
        source_image = ROOT / "assets/page-previews/114" / expected_name
        site_image = SITE / "assets/page-previews/114" / expected_name
        if not source_image.is_file() or not site_image.is_file() or source_image.read_bytes() != site_image.read_bytes():
            errors.append(f"missing or differing preview: {number}")
            continue
        try:
            with Image.open(source_image) as image:
                width, height = image.size
                pdf_width, pdf_height = source_doc[number - 1].get_size()
                if image.format != "WEBP" or width != 1400 or height <= 0:
                    errors.append(f"invalid WebP dimensions: {number}")
                if abs((width / height) - (pdf_width / pdf_height)) / (pdf_width / pdf_height) >= 0.005:
                    errors.append(f"preview aspect ratio mismatch: {number}")
                stats = ImageStat.Stat(image.convert("L"))
                low, high = stats.extrema[0]
                if low == high or stats.stddev[0] < 1:
                    errors.append(f"blank preview image: {number}")
        except OSError as exc:
            errors.append(f"invalid preview {number}: {exc}")
        if digest(source_image) != item.get("sha256") or item.get("sourcePdfSha256") != EXPECTED_SHA:
            errors.append(f"preview SHA metadata mismatch: {number}")
    for page in pages:
        number = page["pdfPage"]
        html_path = SITE / f"versions/114/pages/page-{number:03d}.html"
        if not html_path.is_file():
            errors.append(f"missing page HTML: {number}")
            continue
        document = html_path.read_text(encoding="utf-8")
        marker = f'id="pdf-page-{number}"'
        if marker not in document:
            errors.append(f"page-card id missing: {number}")
        mode = page["renderMode"]
        if mode == "text" and ('class="display-text"' not in document or 'class="raw-text-details"' not in document):
            errors.append(f"text page body incomplete: {number}")
        if mode == "hybrid" and ('class="source-preview-image"' not in document or 'class="extracted-text-details"' not in document or f"#page={number}" not in document):
            errors.append(f"hybrid page body incomplete: {number}")
        if mode == "preview" and ("未使用OCR重建內容" not in document or f"#page={number}" not in document):
            errors.append(f"preview page body incomplete: {number}")
    search = json.loads((SITE / "assets/data/search-index.json").read_text(encoding="utf-8"))
    indexed_pages = {item["pdfPage"] for item in search if item.get("type") == "原文頁面"}
    if indexed_pages != set(range(1, 360)):
        errors.append("not all 359 pages are reachable through search")
    if errors:
        print("PAGE RENDERING VALIDATION FAILED")
        for error in errors:
            print("- " + error)
        return 1
    print("PAGE RENDERING VALIDATION PASSED")
    print(f"- Text pages: {len(modes['text'])}")
    print(f"- Preview pages: {len(modes['preview'])}")
    print(f"- Hybrid pages: {len(modes['hybrid'])}")
    print(f"- Pages without text layer: {sum(not p['hasTextLayer'] for p in pages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
