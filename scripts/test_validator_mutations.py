#!/usr/bin/env python3
"""Prove that 15 high-risk mutations are rejected by real validators/tests."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY_DIRS = ("assets", "data", "scripts", "site", "templates")
NODE_FALLBACK = Path(
    "/Users/huanghsinchao/.cache/codex-runtimes/"
    "codex-primary-runtime/dependencies/node/bin/node"
)


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
    node = shutil.which("node") or (str(NODE_FALLBACK) if NODE_FALLBACK.is_file() else None)
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
    ]

    results = []
    with tempfile.TemporaryDirectory(prefix="handbook-mutations-") as raw:
        base = Path(raw)
        for index, (name, mutation, validator) in enumerate(cases, 1):
            fixture = base / f"case-{index:02d}"
            copy_fixture(fixture)
            mutation(fixture)
            command = (
                [sys.executable, "scripts/validate_search_experience.py", "--root", str(fixture)]
                if validator == "python"
                else [node, "scripts/test_search_core.cjs"]
            )
            completed = subprocess.run(
                command, cwd=fixture, text=True, capture_output=True, timeout=120
            )
            if completed.returncode == 0:
                raise AssertionError(f"mutation not caught: {index}. {name}")
            evidence = (completed.stdout + completed.stderr).strip().splitlines()
            results.append({
                "mutation": index,
                "name": name,
                "validator": "validate_search_experience.py" if validator == "python" else "test_search_core.cjs",
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
