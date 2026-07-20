#!/usr/bin/env python3
"""Strict provenance and search regression checks for interpretation metadata."""

from __future__ import annotations

import json
from pathlib import Path

from extract_manual import parse_interpretation_header

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/114"
KNOWN = (
    "農授金字第0955080181號", "農授金字第0955080186號", "農授金字第0955013311號",
    "農授金字第0955014492號", "農授金字第0965080067號", "農授金字第1025080192號",
    "農授金字第1025015623號", "農授金字第1147426893號",
)
BAD = ("日農授金字第0955080181號", "日農授金字第0955080186號", "日農授金字第1025080192號")


def main() -> int:
    records = json.loads((DATA / "interpretations.json").read_text(encoding="utf-8"))
    search = json.loads((ROOT / "site/assets/data/search-index.json").read_text(encoding="utf-8"))
    errors, keys = [], set()
    for item in records:
        parsed = parse_interpretation_header(item.get("sourceHeader", ""))
        key = (item.get("canonicalDocumentNumber"), item.get("printedPageStart"))
        if not parsed or parsed["date"] != item.get("date") or parsed["documentNumber"] != item.get("documentNumber"):
            errors.append(f"strict reparse mismatch: {item.get('id')}")
        if item.get("verificationStatus") != "source-indexed" or not item.get("title") or not item.get("pdfPageStart"):
            errors.append(f"missing source-indexed field: {item.get('id')}")
        if item.get("printedPageEnd") is not None or item.get("pdfPageEnd") is not None or item.get("rangeStatus") != "start-only":
            errors.append(f"invalid start-only range: {item.get('id')}")
        if not item.get("originalUrl", "").endswith(f"#page={item.get('pdfPageStart')}"):
            errors.append(f"source URL page mismatch: {item.get('id')}")
        if key in keys:
            errors.append(f"duplicate canonical/page source: {item.get('id')}")
        keys.add(key)
    searchable = "\n".join(json.dumps(x, ensure_ascii=False) for x in search)
    for number in KNOWN:
        if not any(item.get("documentNumber") == number for item in records): errors.append(f"known source missing: {number}")
        if number not in searchable: errors.append(f"known search missing: {number}")
    for number in BAD:
        if number in searchable: errors.append(f"bad search result: {number}")
    if errors:
        print("INTERPRETATION METADATA VALIDATION FAILED\n" + "\n".join("- " + x for x in errors)); return 1
    print("INTERPRETATION METADATA VALIDATION PASSED")
    print(f"- Source-indexed records: {len(records)}; known searches: {len(KNOWN)}; bad searches: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
