#!/usr/bin/env python3
"""Mutation tests for Official Updates lookup separation and provenance contracts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import argparse
from pathlib import Path
from audit_forms_regression import (retained_workspace, copy_retained_tree,
    mutation_command, positive_control, causal_failure)

ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(destination: Path) -> None:
    destination.mkdir()
    for name in ("assets", "curation", "data", "scripts", "site", "templates", "tests"):
        copy_retained_tree(ROOT / name, destination / name)
    for name in ("README.md", "CHANGELOG.md", "package.json", "package-lock.json"):
        shutil.copyfile(ROOT / name, destination / name)


def write(path: Path, value: str) -> None:
    if ROOT / 'tmp/release-gates' not in path.absolute().parents or path.is_symlink():
        raise ValueError('Mutation writes must stay in retained fixtures')
    path.write_text(value, encoding="utf-8")


def mutate_json(path: Path, callback) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    callback(value)
    write(path, json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"mutation target missing: {old}")
    write(path, text.replace(old, new, 1))


def replace_all(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"mutation target missing: {old}")
    write(path, text.replace(old, new))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument('--retain-workspace', action='store_true'); parser.parse_args()
    cases = [
        ("delete official update", lambda root: mutate_json(root / "data/current/official-updates.json", lambda items: items.pop())),
        ("duplicate official update ID", lambda root: mutate_json(root / "data/current/official-updates.json", lambda items: items[1].update(id=items[0]["id"]))),
        ("fixture expected ID missing", lambda root: mutate_json(root / "tests/fixtures/official-updates-lookup.json", lambda value: value["queries"][0].update(expectedTopId="missing-update"))),
        ("document number normalization broken", lambda root: replace(root / "assets/js/official-updates-lookup.js", "replace(/字第/g, \"\")", "replace(/文號/g, \"\")")),
        ("program relation omitted from card", lambda root: replace(root / "site/updates/index.html", "data-update-relations=\"natural-disaster-low-interest-loan natural-disaster-rules\"", "data-update-relations=\"natural-disaster-rules\"")),
        ("year filter option is wrong", lambda root: replace(root / "site/updates/index.html", 'option value="2025"', 'option value="2099"')),
        ("official update leaks into 507 search", lambda root: mutate_json(root / "site/assets/data/search-index.json", lambda items: items.append({"id": "afna-leaked-update"}))),
        ("disaster announcement becomes lookup data", lambda root: mutate_json(root / "data/current/official-updates.json", lambda items: items[0].update(sourceType="local-disaster-announcement"))),
        ("official source link removed", lambda root: replace(root / "site/updates/index.html", 'href="https://law.afna.gov.tw/view.php?id=50"', 'href=""')),
        ("URL state handler removed", lambda root: replace_all(root / "assets/js/official-updates-lookup.js", "URLSearchParams", "BrokenSearchParams")),
        ("coverage changed to complete", lambda root: mutate_json(root / "data/current/coverage.json", lambda value: value["officialUpdateReview"].update(coverageStatus="complete", verifiedThrough="2026-07-28"))),
        ("version mismatch", lambda root: mutate_json(root / "data/114/manual.json", lambda value: value.update(digitalRevision="114.0.0-beta.3.0"))),
        ("tokenization uses normalized query", lambda root: replace(root / "assets/js/official-updates-lookup.js", "const terms = tokenizeQuery(rawQuery);", "const terms = q.split(/\\s+/).filter(Boolean);")),
        ("multi-keyword AND changed to OR", lambda root: replace(root / "assets/js/official-updates-lookup.js", "terms.length >= 2 && terms.every((term) => body.includes(term))", "terms.length >= 2 && terms.some((term) => body.includes(term))")),
        ("only first multi-keyword token checked", lambda root: replace(root / "assets/js/official-updates-lookup.js", "terms.length >= 2 && terms.every((term) => body.includes(term))", "terms.length >= 2 && terms.slice(0, 1).every((term) => body.includes(term))")),
        ("full-width whitespace tokenization removed", lambda root: replace(root / "assets/js/official-updates-lookup.js", "split(/\\s+/)", "split(/[ \\t]+/)")),
    ]
    expected = ['official update count is', 'duplicate official update ID', 'fixture top result mismatch:',
                'lookup JS missing required behavior: replace(/字第/g', 'rendered program relation missing:',
                'year filter is not derived from official update dates', 'handbook search index is not 507',
                'invalid official update source type:', 'official source link missing:',
                'lookup JS missing required behavior: URLSearchParams', 'coverage changed from partial/null',
                'version metadata is not beta.3.3', 'lookup JS does not tokenize from raw query boundaries',
                'lookup JS does not enforce multi-keyword AND matching',
                'lookup JS does not enforce multi-keyword AND matching', 'lookup JS whitespace tokenization is incomplete']
    size = sum(p.stat().st_size for folder in ('assets', 'curation', 'data', 'scripts', 'site', 'templates', 'tests') for p in (ROOT / folder).rglob('*') if p.is_file())
    results = []; base = retained_workspace('official-mutations', required_bytes=size * (len(cases) + 1))
    control = base / 'positive-control'; copy_fixture(control)
    command = [sys.executable, 'scripts/validate_official_updates_lookup.py']
    baseline = positive_control(command, control)
    for index, (name, mutation) in enumerate(cases, 1):
        fixture = base / f"case-{index:02d}"
        copy_fixture(fixture)
        mutation(fixture)
        completed = mutation_command(command, fixture)
        evidence = causal_failure(completed, expected[index - 1], name)
        results.append({"mutation": index, "name": name, "caught": True, "evidence": evidence})
    print(json.dumps({"status": "OFFICIAL UPDATES LOOKUP MUTATIONS PASSED", "caught": f"{len(results)}/{len(cases)}", "uncaught": 0, "positiveControl": baseline, "retainedWorkspace": str(base.relative_to(ROOT)), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
