#!/usr/bin/env python3
"""Mutation tests for Official Updates lookup separation and provenance contracts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(destination: Path) -> None:
    destination.mkdir()
    for name in ("assets", "curation", "data", "scripts", "site", "templates", "tests"):
        shutil.copytree(ROOT / name, destination / name, copy_function=shutil.copy2)
    for name in ("README.md", "CHANGELOG.md", "package.json", "package-lock.json"):
        shutil.copy2(ROOT / name, destination / name)


def write(path: Path, value: str) -> None:
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
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="handbook-official-updates-mutations-") as raw:
        base = Path(raw)
        for index, (name, mutation) in enumerate(cases, 1):
            fixture = base / f"case-{index:02d}"
            copy_fixture(fixture)
            mutation(fixture)
            completed = subprocess.run(
                [sys.executable, "scripts/validate_official_updates_lookup.py"],
                cwd=fixture, text=True, capture_output=True, timeout=120,
            )
            if completed.returncode == 0:
                raise AssertionError(f"mutation not caught: {index}. {name}")
            evidence = (completed.stdout + completed.stderr).strip().splitlines()
            results.append({"mutation": index, "name": name, "caught": True, "evidence": evidence[0][:160] if evidence else f"exit {completed.returncode}"})
            shutil.rmtree(fixture)
    print(json.dumps({"status": "OFFICIAL UPDATES LOOKUP MUTATIONS PASSED", "caught": f"{len(results)}/{len(cases)}", "uncaught": 0, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
