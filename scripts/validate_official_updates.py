#!/usr/bin/env python3
"""Validate the offline official post-handbook update layer."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_HOSTS = {
    "law.afna.gov.tw", "afna.gov.tw", "www.afna.gov.tw",
    "moa.gov.tw", "www.moa.gov.tw", "wm.moa.gov.tw",
    "agribank.com.tw", "www.agribank.com.tw",
}
SOURCE_TYPES = {
    "regulation", "administrative-rule", "interpretation", "announcement",
    "faq", "form", "disaster-measure", "other-official",
}
RELATION_BASES = {
    "explicit-title", "explicit-subject", "explicit-body", "common-rule",
    "disaster-rule", "bank-product", "human-reviewed",
}
DECISIONS = {"include", "already-covered", "exclude-irrelevant", "needs-human-review"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    errors: list[str] = []
    coverage = load(root / "data/current/coverage.json")
    updates = load(root / "data/current/official-updates.json")
    decisions = load(root / "curation/current/official-update-decisions.json")
    loans = load(root / "data/114/loan-programs.json")
    loan_ids = {item["id"] for item in loans}
    section_ids = {
        "policy-loan-regulations", "agricultural-development-fund-rules",
        "loan-programs", "natural-disaster-rules", "amendment-faq",
        "attachments", "bank-operating-rules-appendices",
    }
    decision_ids = [item.get("id") for item in decisions]
    update_ids = [item.get("id") for item in updates]
    if len(decision_ids) != len(set(decision_ids)):
        errors.append("duplicate candidate decision id")
    if len(update_ids) != len(set(update_ids)):
        errors.append("duplicate official update id")
    included = {item["id"] for item in decisions if item.get("decision") == "include"}
    if included != set(update_ids):
        errors.append("include decisions and official-updates records do not match exactly")
    for item in decisions:
        if item.get("decision") not in DECISIONS:
            errors.append(f"invalid or empty decision: {item.get('id')}")
        if urlparse(item.get("sourceUrl", "")).hostname not in ALLOWED_HOSTS:
            errors.append(f"non-allowlisted candidate source: {item.get('id')}")
        if not item.get("reason") or not item.get("evidence"):
            errors.append(f"incomplete candidate decision evidence: {item.get('id')}")
    required = {
        "id", "officialTitle", "sourceType", "officialAgency", "documentNumber",
        "publishedDate", "effectiveDate", "applicationPeriod", "sourceUrl",
        "relatedLoanIds", "relatedSectionIds", "relationBasis",
        "relationEvidence", "verifiedOn",
    }
    for item in updates:
        missing = required - set(item)
        if missing:
            errors.append(f"missing fields {sorted(missing)}: {item.get('id')}")
            continue
        if not item["officialTitle"] or not item["officialAgency"] or not item["relationEvidence"]:
            errors.append(f"empty authoritative metadata: {item['id']}")
        if item["sourceType"] not in SOURCE_TYPES:
            errors.append(f"invalid sourceType: {item['id']}")
        if item["relationBasis"] not in RELATION_BASES:
            errors.append(f"invalid relationBasis: {item['id']}")
        if not DATE.fullmatch(item["publishedDate"]) or not DATE.fullmatch(item["verifiedOn"]):
            errors.append(f"invalid date: {item['id']}")
        if item["effectiveDate"] is not None and not DATE.fullmatch(item["effectiveDate"]):
            errors.append(f"invalid effectiveDate: {item['id']}")
        period = item["applicationPeriod"]
        if set(period) != {"start", "end"}:
            errors.append(f"invalid applicationPeriod: {item['id']}")
        if any(value is not None and not DATE.fullmatch(value) for value in period.values()):
            errors.append(f"invalid application period date: {item['id']}")
        if urlparse(item["sourceUrl"]).hostname not in ALLOWED_HOSTS:
            errors.append(f"non-allowlisted official source: {item['id']}")
        if set(item["relatedLoanIds"]) - loan_ids:
            errors.append(f"unknown related loan: {item['id']}")
        if set(item["relatedSectionIds"]) - section_ids:
            errors.append(f"unknown related section: {item['id']}")
    review = coverage["officialUpdateReview"]
    human_count = sum(item["decision"] == "needs-human-review" for item in decisions)
    if review["included"] != len(updates) or review["needsHumanReview"] != human_count:
        errors.append("coverage counts do not match data")
    if review["searchStartDate"] != "2025-10-01" or not DATE.fullmatch(review["verifiedThrough"]):
        errors.append("coverage review dates are invalid")
    if coverage["baseline"]["pdfPages"] != 359 or coverage["baseline"]["latestKnownIncludedOfficialDate"] != "2025-12-03":
        errors.append("baseline coverage evidence is invalid")
    site = root / "site"
    if site.exists():
        updates_page = site / "updates/index.html"
        if not updates_page.is_file():
            errors.append("updates/index.html missing")
        else:
            text = updates_page.read_text(encoding="utf-8")
            for token in ("手冊出版後官方更新", "data-update-filters", "待人工核對", "已檢核指定官方來源"):
                if token not in text:
                    errors.append(f"updates page marker missing: {token}")
        search_path = site / "assets/data/search-index.json"
        if search_path.is_file() and len(load(search_path)) != 507:
            errors.append("official updates leaked into the 507-record handbook search index")
    if errors:
        print("OFFICIAL UPDATE VALIDATION FAILED")
        for error in errors:
            print("- " + error)
        return 1
    print(f"OFFICIAL UPDATE VALIDATION PASSED: {len(updates)} included, {human_count} needs human review, {len(decisions)} candidates decided")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
