#!/usr/bin/env python3
"""Prove that 28 high-risk content, search, context and official-update mutations are rejected."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY_DIRS = ("assets", "curation", "data", "scripts", "site", "templates")
def copy_fixture(destination: Path) -> None:
    destination.mkdir()
    for name in COPY_DIRS:
        shutil.copytree(ROOT / name, destination / name, copy_function=os.link)


def safe_write(path: Path, value: str) -> None:
    path.unlink()
    path.write_text(value, encoding="utf-8")


def mutate_json(path: Path, callback) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    callback(value)
    safe_write(path, json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def replace(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"mutation target missing: {old} in {path}")
    safe_write(path, text.replace(old, new, count))


def search_index(root: Path) -> Path:
    return root / "site/assets/data/search-index.json"


def html_with(root: Path, needle: str) -> Path:
    for path in (root / "site").rglob("*.html"):
        if needle in path.read_text(encoding="utf-8"):
            return path
    raise AssertionError(f"HTML fixture missing {needle}")


def main() -> None:
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js is required for mutation tests")

    def remove_group(root: Path):
        mutate_json(search_index(root), lambda records: records[95].update(scopeGroup=None))

    def unknown_loan_page_group(root: Path):
        path = html_with(root, 'data-search-scope-group="loan:')
        text = path.read_text(encoding="utf-8")
        safe_write(path, text.replace('data-search-scope-group="loan:', 'data-search-scope-group="loan:missing-', 1))

    def invalid_section_scope(root: Path):
        path = root / "site/versions/114/sections/loan-programs/index.html"
        text = path.read_text(encoding="utf-8")
        safe_write(path, re_sub_scope(text, "section:not-present"))

    def missing_fragment(root: Path):
        mutate_json(search_index(root), lambda records: records[0].update(url=records[0]["url"].split("#")[0] + "#missing-id"))

    def bad_document_prefix(root: Path):
        def change(records):
            item = next(record for record in records if record.get("documentNumber"))
            item["documentNumber"] = "日" + item["documentNumber"]
        mutate_json(search_index(root), change)

    def missing_url(root: Path):
        mutate_json(search_index(root), lambda records: records[0].update(url="missing/index.html"))

    def unsafe_inner_html(root: Path):
        path = root / "assets/js/search.js"
        replace(path, '"use strict";', '"use strict"; results.innerHTML = "";')
        site_path = root / "site/assets/js/search.js"
        replace(site_path, '"use strict";', '"use strict"; results.innerHTML = "";')

    def wrong_theme(root: Path):
        replace(root / "templates/base.html", "#286b57", "#000000")

    def wrong_print_label(root: Path):
        path = root / "site/versions/114/pages/page-003.html"
        replace(path, 'data-print-label="列印本頁"', 'data-print-label="列印本章"')

    def remove_record(root: Path):
        mutate_json(search_index(root), lambda records: records.pop())

    def wrong_page_group(root: Path):
        def change(records):
            item = next(record for record in records if record.get("id") == "page-096")
            item["scopeGroup"] = "loan:young-farmer-loan"
        mutate_json(search_index(root), change)

    def source_site_mismatch(root: Path):
        path = root / "site/assets/js/search-core.js"
        safe_write(path, path.read_text(encoding="utf-8") + "\n// mismatch\n")

    def unicode_offset(root: Path):
        for path in (root / "assets/js/search-core.js", root / "site/assets/js/search-core.js"):
            replace(path, "startMap.push(start);", "startMap.push(Math.max(0, start - 1));")

    def oversized_snippet(root: Path):
        for path in (root / "assets/js/search-core.js", root / "site/assets/js/search-core.js"):
            replace(path, "const target = 240;", "const target = 1000;")

    def empty_section_scope(root: Path):
        path = root / "site/versions/114/sections/natural-disaster-rules/index.html"
        text = path.read_text(encoding="utf-8")
        safe_write(path, re_sub_scope(text, ""))

    def loan_inline_default_all(root: Path):
        path = html_with(root, "在本貸款中搜尋")
        replace(path, 'data-search-default-scope="context"', 'data-search-default-scope="all"')

    def section_inline_default_all(root: Path):
        path = root / "site/versions/114/sections/agricultural-development-fund-rules/index.html"
        replace(path, 'data-search-default-scope="context"', 'data-search-default-scope="all"')

    def global_dialog_default_context(root: Path):
        replace(
            root / "templates/base.html",
            'dialog-search-panel" data-search data-search-default-scope="all"',
            'dialog-search-panel" data-search data-search-default-scope="context"',
        )

    def loan_shortcut_without_context(root: Path):
        path = html_with(root, "在本貸款中搜尋")
        replace(path, 'data-search-scope="context"', 'data-search-scope="all"')

    def appendix_action_as_form(root: Path):
        replace(
            root / "assets/js/search.js",
            'record.type === "附錄附件" ? "查看附錄"',
            'record.type === "附錄附件" ? "查看書表"',
        )

    def update_untrusted_domain(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(sourceUrl="https://example.com/update"))

    def update_invalid_type(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(sourceType="summary"))

    def update_empty_relation_evidence(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(relationEvidence=""))

    def update_unknown_loan(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(relatedLoanIds=["unknown-loan"]))

    def update_missing_included_record(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items.pop())

    def update_bad_coverage_count(root: Path):
        mutate_json(root / "data/current/coverage.json", lambda value: value["officialUpdateReview"].update(included=999))

    def update_empty_candidate_decision(root: Path):
        mutate_json(root / "curation/current/official-update-decisions.json", lambda items: items[0].update(decision=""))

    def update_leaks_into_search(root: Path):
        def append_record(items):
            copy = dict(items[0])
            copy["id"] = "official-update-leak"
            items.append(copy)
        mutate_json(search_index(root), append_record)

    def update_http_url(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(sourceUrl="http://law.afna.gov.tw/view.php?id=50"))

    def update_invalid_calendar_date(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(publishedDate="2026-02-31"))

    def update_reverse_application_period(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(applicationPeriod={"start":"2026-12-31","end":"2026-01-01"}))

    def coverage_complete_agribank_partial(root: Path):
        mutate_json(root / "data/current/coverage.json", lambda value: value["officialUpdateReview"].update(coverageStatus="complete", verifiedThrough="2026-07-28"))

    def coverage_exceeds_source(root: Path):
        mutate_json(root / "curation/current/source-review-log.json", lambda items: items[0].update(status="complete", reviewedThrough="2026-01-01"))
        mutate_json(root / "data/current/coverage.json", lambda value: value["officialUpdateReview"].update(coverageStatus="complete", verifiedThrough="2026-07-28"))

    def disaster_missing_include(root: Path):
        mutate_json(root / "data/current/disaster-loan-announcements.json", lambda items: items.pop())

    def disaster_needs_review_in_data(root: Path):
        mutate_json(root / "curation/current/disaster-loan-announcement-decisions.json", lambda items: items[0].update(decision="needs-human-review"))

    def disaster_duplicate(root: Path):
        def change(items):
            copy = dict(items[0]); copy["id"] = "duplicate-disaster"; items.append(copy)
        mutate_json(root / "data/current/disaster-loan-announcements.json", change)

    def delete_disaster_page(root: Path):
        (root / "site/updates/disasters/index.html").unlink()

    def mix_disaster_into_system(root: Path):
        def change(items):
            copy = dict(items[0]); copy["id"] = "moa-bawi-typhoon-20260713"; items.append(copy)
        mutate_json(root / "data/current/official-updates.json", change)

    def update_unknown_section(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(relatedSectionIds=["not-a-section"]))

    def update_verified_on_null(root: Path):
        mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(verifiedOn=None))

    def disaster_verified_on_null(root: Path):
        mutate_json(root / "data/current/disaster-loan-announcements.json", lambda items: items[0].update(verifiedOn=None))

    def lineage_count_mismatch(root: Path):
        mutate_json(root / "curation/current/source-review-log.json", lambda items: items[0].update(candidateCount=999))

    def lineage_unknown_candidate(root: Path):
        mutate_json(root / "curation/current/source-review-log.json", lambda items: items[0].update(candidateIds=["unknown-candidate"], candidateCount=1))

    def lineage_orphan(root: Path):
        mutate_json(root / "curation/current/source-review-log.json", lambda items: items[0].update(candidateIds=items[0]["candidateIds"][1:], candidateCount=len(items[0]["candidateIds"][1:])))

    cases = [
        ("missing record scopeGroup", remove_group, "python"),
        ("unknown loan page scopeGroup", unknown_loan_page_group, "python"),
        ("invalid loan-programs section scope", invalid_section_scope, "python"),
        ("missing internal fragment", missing_fragment, "python"),
        ("document number bad date prefix", bad_document_prefix, "python"),
        ("search URL 404", missing_url, "python"),
        ("unsafe innerHTML rendering", unsafe_inner_html, "python"),
        ("wrong theme-color", wrong_theme, "python"),
        ("wrong single-page print label", wrong_print_label, "python"),
        ("506 search records", remove_record, "python"),
        ("source page wrong loan group", wrong_page_group, "python"),
        ("source/site search core mismatch", source_site_mismatch, "python"),
        ("Unicode mark offset", unicode_offset, "node"),
        ("1000-character snippet", oversized_snippet, "node"),
        ("section scope with no records", empty_section_scope, "python"),
        ("loan inline default scope changed to all", loan_inline_default_all, "ux"),
        ("section inline default scope changed to all", section_inline_default_all, "ux"),
        ("global dialog default scope changed to context", global_dialog_default_context, "ux"),
        ("loan shortcut context scope removed", loan_shortcut_without_context, "ux"),
        ("appendix action changed back to 查看書表", appendix_action_as_form, "ux"),
        ("official update uses untrusted domain", update_untrusted_domain, "official"),
        ("official update has invalid source type", update_invalid_type, "official"),
        ("official update relation evidence is empty", update_empty_relation_evidence, "official"),
        ("official update references unknown loan", update_unknown_loan, "official"),
        ("include decision has no update record", update_missing_included_record, "official"),
        ("official coverage included count is false", update_bad_coverage_count, "official"),
        ("candidate decision is empty", update_empty_candidate_decision, "official"),
        ("official update leaks into handbook search", update_leaks_into_search, "official"),
        ("official update uses http", update_http_url, "official"),
        ("official update invalid calendar date", update_invalid_calendar_date, "official"),
        ("official update reverse application period", update_reverse_application_period, "official"),
        ("coverage complete while Agribank partial", coverage_complete_agribank_partial, "coverage"),
        ("global coverage exceeds source review", coverage_exceeds_source, "coverage"),
        ("disaster include has no formal record", disaster_missing_include, "disaster"),
        ("disaster needs-review enters formal data", disaster_needs_review_in_data, "disaster"),
        ("duplicate disaster announcement", disaster_duplicate, "disaster"),
        ("disaster page deleted", delete_disaster_page, "python"),
        ("disaster announcement mixed into system track", mix_disaster_into_system, "official"),
        ("official update unknown related section", update_unknown_section, "official"),
        ("official update verifiedOn null", update_verified_on_null, "official"),
        ("disaster verifiedOn null", disaster_verified_on_null, "disaster"),
        ("source review candidate count mismatch", lineage_count_mismatch, "coverage"),
        ("source review unknown candidate", lineage_unknown_candidate, "coverage"),
        ("decision candidate has no source lineage", lineage_orphan, "coverage"),
    ]

    results = []
    with tempfile.TemporaryDirectory(prefix="handbook-mutations-") as raw:
        base = Path(raw)
        for index, (name, mutation, validator) in enumerate(cases, 1):
            fixture = base / f"case-{index:02d}"
            copy_fixture(fixture)
            mutation(fixture)
            if validator == "python":
                command = [sys.executable, "scripts/validate_search_experience.py", "--root", str(fixture)]
            elif validator == "official":
                command = [sys.executable, "scripts/validate_official_updates.py", "--root", str(fixture)]
            elif validator == "disaster":
                command = [sys.executable, "scripts/validate_disaster_loan_announcements.py", "--root", str(fixture)]
            elif validator == "coverage":
                command = [sys.executable, "scripts/validate_official_coverage.py", "--root", str(fixture)]
            elif validator == "ux":
                command = [sys.executable, "scripts/validate_ux_structure.py"]
            else:
                command = [node, "scripts/test_search_core.cjs"]
            completed = subprocess.run(
                command, cwd=fixture, text=True, capture_output=True, timeout=120
            )
            if completed.returncode == 0:
                raise AssertionError(f"mutation not caught: {index}. {name}")
            evidence = (completed.stdout + completed.stderr).strip().splitlines()
            results.append({
                "mutation": index,
                "name": name,
                "validator": (
                    "validate_search_experience.py" if validator == "python"
                    else "validate_official_updates.py" if validator == "official"
                    else "validate_disaster_loan_announcements.py" if validator == "disaster"
                    else "validate_official_coverage.py" if validator == "coverage"
                    else "validate_ux_structure.py" if validator == "ux"
                    else "test_search_core.cjs"
                ),
                "caught": True,
                "evidence": evidence[0][:160] if evidence else f"exit {completed.returncode}",
            })
            shutil.rmtree(fixture)
    print(json.dumps({
        "status": "VALIDATOR MUTATIONS PASSED",
        "caught": f"{len(results)}/{len(cases)}",
        "uncaught": 0,
        "results": results,
    }, ensure_ascii=False, indent=2))


def re_sub_scope(text: str, value: str) -> str:
    import re
    changed, count = re.subn(
        r'data-search-scopes="[^"]*"',
        f'data-search-scopes="{value}"',
        text,
        count=1,
    )
    if count != 1:
        raise AssertionError("section data-search-scopes attribute missing")
    return changed


if __name__ == "__main__":
    main()
