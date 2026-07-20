#!/usr/bin/env python3
"""Validate source-indexed data, classified inventories, page mapping and search."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/114"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    errors = []
    manual, toc, quick = load("manual.json"), load("toc.json"), load("quick-index.json")
    interpretations, candidates = load("interpretations.json"), load("interpretation-candidates.json")
    forms, form_candidates, exclusions = load("forms.json"), load("form-candidates.json"), load("form-exclusions.json")
    page_map = load("printed-page-map.json")
    search = json.loads((ROOT / "site/assets/data/search-index.json").read_text(encoding="utf-8"))
    counts = manual["counts"]
    if toc.get("structure") != "faithful-flat-hierarchy" or len(toc.get("items", [])) != 54:
        errors.append("faithful TOC must contain 54 source entries")
    if len(quick.get("groups", [])) != 3:
        errors.append("quick index must contain three groups")
    if any(item.get("verificationStatus") != "source-indexed" for item in interpretations):
        errors.append("interpretations must be source-indexed")
    source_ids = {item["id"] for item in interpretations}
    for item in candidates:
        disposition = item.get("disposition")
        if disposition not in {"promoted-to-source-index", "duplicate-detection", "pending-review"}:
            errors.append(f"invalid interpretation disposition: {item.get('id')}")
        if disposition == "promoted-to-source-index" and item.get("linkedInterpretationId") not in source_ids:
            errors.append(f"unlinked promoted interpretation candidate: {item.get('id')}")
        if disposition == "duplicate-detection" and not item.get("duplicateOf"):
            errors.append(f"unlinked duplicate interpretation candidate: {item.get('id')}")
        if disposition == "pending-review" and item.get("linkedInterpretationId"):
            errors.append(f"pending interpretation candidate linked to source: {item.get('id')}")
    if any(item.get("verificationStatus") != "source-indexed" for item in forms):
        errors.append("forms must be source-indexed")
    form_ids, exclusion_ids = {item["id"] for item in forms}, {item["id"] for item in exclusions}
    for item in form_candidates:
        disposition = item.get("disposition")
        if disposition not in {"promoted-to-source-index", "excluded", "pending-review"}:
            errors.append(f"invalid form disposition: {item.get('id')}")
        if disposition == "promoted-to-source-index" and item.get("linkedFormId") not in form_ids:
            errors.append(f"unlinked promoted form candidate: {item.get('id')}")
        if disposition == "excluded" and item.get("exclusionId") not in exclusion_ids:
            errors.append(f"unlinked excluded form candidate: {item.get('id')}")
        if disposition == "pending-review" and item.get("linkedFormId"):
            errors.append(f"pending form candidate linked to source: {item.get('id')}")
    expected_counts = {
        "interpretationsSourceIndexed": len(interpretations), "interpretationCandidateInventoryTotal": len(candidates),
        "interpretationCandidatesPromoted": sum(x["disposition"] == "promoted-to-source-index" for x in candidates),
        "interpretationCandidatesDuplicate": sum(x["disposition"] == "duplicate-detection" for x in candidates),
        "interpretationCandidatesPending": sum(x["disposition"] == "pending-review" for x in candidates),
        "formsSourceIndexed": len(forms), "formCandidateInventoryTotal": len(form_candidates),
        "formCandidatesPromoted": sum(x["disposition"] == "promoted-to-source-index" for x in form_candidates),
        "formCandidatesExcluded": sum(x["disposition"] == "excluded" for x in form_candidates),
        "formCandidatesPending": sum(x["disposition"] == "pending-review" for x in form_candidates),
    }
    if any(counts[k] != v for k, v in expected_counts.items()):
        errors.append("manual counts do not match classified inventories")
    if counts["interpretationCandidateInventoryTotal"] != sum(counts[k] for k in ("interpretationCandidatesPromoted", "interpretationCandidatesDuplicate", "interpretationCandidatesPending")):
        errors.append("interpretation inventory equation is invalid")
    if counts["formCandidateInventoryTotal"] != sum(counts[k] for k in ("formCandidatesPromoted", "formCandidatesExcluded", "formCandidatesPending")):
        errors.append("form inventory equation is invalid")
    records = page_map.get("pages", [])
    if page_map.get("status") != "sampled-consistent" or len(records) != 359 or page_map.get("anchorCount") != 42:
        errors.append("printed page map must have 359 records and 42 checked anchors")
    elif any(r["printedPage"] != (None if r["pdfPage"] <= 2 else r["pdfPage"] - 2) for r in records):
        errors.append("printed page map offset is inconsistent")
    expected = 359 + 23 + len(interpretations) + 4 + len(forms) + 6
    if len(search) != expected:
        errors.append(f"search record count {len(search)} does not match source-indexed total {expected}")
    site_names = {path.name for path in (ROOT / "site").rglob("*.json")}
    if {"interpretation-candidates.json", "form-candidates.json", "form-exclusions.json"} & site_names:
        errors.append("review-only candidate data leaked into public site")
    if errors:
        print("INDEX QUALITY VALIDATION FAILED\n" + "\n".join("- " + x for x in errors)); return 1
    print("INDEX QUALITY VALIDATION PASSED")
    print(f"- Source interpretations: {len(interpretations)}; inventory: {len(candidates)}")
    print(f"- Source forms: {len(forms)}; inventory: {len(form_candidates)}")
    print(f"- Page-map records: {len(records)}; checked anchors: {page_map['anchorCount']}; search records: {len(search)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
