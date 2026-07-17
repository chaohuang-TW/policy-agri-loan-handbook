#!/usr/bin/env python3
"""Validate separation, provenance, completeness, and public-search index quality."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/114"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    errors = []
    toc = load("toc.json")
    quick = load("quick-index.json")
    interpretations = load("interpretations.json")
    interpretation_candidates = load("interpretation-candidates.json")
    forms = load("forms.json")
    form_candidates = load("form-candidates.json")
    exclusions = load("form-exclusions.json")
    page_map = load("printed-page-map.json")
    search = json.loads((ROOT / "site/assets/data/search-index.json").read_text(encoding="utf-8"))

    if toc.get("structure") != "faithful-flat-hierarchy" or len(toc.get("items", [])) != 54:
        errors.append("faithful TOC must contain the 54 source entries")
    if max((item.get("level", 0) for item in toc.get("items", [])), default=0) != 4:
        errors.append("faithful TOC must preserve four hierarchy levels")
    if len(quick.get("groups", [])) != 3:
        errors.append("quick index must contain three reader-oriented groups")
    if any(item.get("verificationStatus") != "confirmed" for item in interpretations):
        errors.append("public interpretation index contains unconfirmed records")
    if any(item.get("verificationStatus") != "needs-review" for item in interpretation_candidates):
        errors.append("interpretation candidates must all remain needs-review")
    candidate_keys = {(item.get("documentNumber"), item.get("printedPage")) for item in interpretation_candidates}
    confirmed_keys = {(item.get("documentNumber"), item.get("printedPageStart")) for item in interpretations}
    if not confirmed_keys <= candidate_keys:
        errors.append("one or more confirmed interpretations are missing from the candidate inventory")
    if any(item.get("verificationStatus") != "confirmed" for item in forms):
        errors.append("public form index contains unconfirmed records")
    if any(item.get("verificationStatus") != "needs-review" for item in form_candidates):
        errors.append("form candidates must all remain needs-review")
    excluded_pages = {item["printedPage"] for item in exclusions}
    confirmed_pages = {item["printedPageStart"] for item in forms}
    candidate_pages = {item["printedPage"] for item in form_candidates}
    if excluded_pages | confirmed_pages != candidate_pages or excluded_pages & confirmed_pages:
        errors.append("form candidates are not fully and exclusively classified")
    if any(not item.get("exclusionReason") for item in exclusions):
        errors.append("form exclusion is missing a reason")
    if page_map.get("status") != "sampled-and-consistent" or len(page_map.get("anchors", [])) < 36:
        errors.append("printed page map needs at least 36 sampled-and-consistent anchors")
    if any(anchor["pdfPage"] - anchor["printedPage"] != 2 for anchor in page_map.get("anchors", [])):
        errors.append("printed page map contains an inconsistent offset")

    expected = 359 + 23 + len(interpretations) + 4 + len(forms) + 6
    if len(search) != expected:
        errors.append(f"search record count {len(search)} does not match confirmed-only total {expected}")
    expected_types = {"原文頁面": 359, "貸款索引": 23, "函釋": len(interpretations), "常見問答": 4,
                      "書表附件": len(forms), "附錄附件": 6}
    for label, count in expected_types.items():
        actual = sum(item["type"] == label for item in search)
        if actual != count:
            errors.append(f"search type {label} has {actual}, expected {count}")
    site_names = {path.name for path in (ROOT / "site").rglob("*.json")}
    if {"interpretation-candidates.json", "form-candidates.json", "form-exclusions.json"} & site_names:
        errors.append("review-only candidate data leaked into the public site")

    if errors:
        print("INDEX QUALITY VALIDATION FAILED")
        for error in errors:
            print("- " + error)
        return 1
    print("INDEX QUALITY VALIDATION PASSED")
    print(f"- TOC entries: {len(toc['items'])}; hierarchy levels: 4; quick-index groups: {len(quick['groups'])}")
    print(f"- Confirmed interpretations: {len(interpretations)}; candidates retained: {len(interpretation_candidates)}")
    print(f"- Confirmed forms: {len(forms)}; candidates retained: {len(form_candidates)}; exclusions: {len(exclusions)}")
    print(f"- Printed-page anchors: {len(page_map['anchors'])}; search records: {len(search)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
