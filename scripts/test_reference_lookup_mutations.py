#!/usr/bin/env python3
"""Mutation tests for FAQ and interpretation lookup provenance contracts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY_DIRS = ("assets", "curation", "data", "scripts", "site", "templates")
COPY_FILES = ("README.md", "CHANGELOG.md", "package.json", "package-lock.json")


def copy_fixture(destination: Path) -> None:
    destination.mkdir()
    for name in COPY_DIRS:
        shutil.copytree(ROOT / name, destination / name, copy_function=shutil.copy2)
    for name in COPY_FILES:
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


def main() -> None:
    cases = [
        ("duplicate FAQ ID", lambda root: mutate_json(root / "data/114/faq-items.json", lambda items: items[1].update(id=items[0]["id"]))),
        ("FAQ page out of range", lambda root: mutate_json(root / "data/114/faq-items.json", lambda items: items[0].update(pdfPageEnd=360))),
        ("fake FAQ group", lambda root: mutate_json(root / "data/114/faq-items.json", lambda items: items[0].update(faqGroupId="faq-fake"))),
        ("blank FAQ question", lambda root: mutate_json(root / "data/114/faq-items.json", lambda items: items[0].update(question=""))),
        ("invalid FAQ source page", lambda root: mutate_json(root / "data/114/faq-items.json", lambda items: items[0].update(sourcePages=[0]))),
        ("duplicate interpretation ID", lambda root: mutate_json(root / "data/114/interpretations.json", lambda items: items[1].update(id=items[0]["id"]))),
        ("broken interpretation document number", lambda root: replace(root / "site/interpretations/index.html", '<p class="lookup-doc-number">文號：農授金字第0955080181號</p>', '<p class="lookup-doc-number">文號：BROKEN</p>')),
        ("Evidence page becomes P.360", lambda root: replace(root / "site/faq/index.html", "../versions/114/pages/page-315.html", "../versions/114/pages/page-360.html")),
        ("FAQ Evidence anchor target is missing", lambda root: replace(root / "site/faq/index.html", "../versions/114/pages/page-315.html", "../versions/114/pages/page-999.html")),
        ("invalid FAQ filter option", lambda root: replace(root / "site/faq/index.html", 'data-lookup-group-filter="faq-114-10"', 'data-lookup-group-filter="faq-fake"')),
        ("lookup data script removed", lambda root: replace(root / "site/faq/index.html", '<script type="application/json" data-lookup-data>', '<script type="application/json">')),
        ("interpretation Evidence target is missing", lambda root: replace(root / "site/interpretations/index.html", "../versions/114/pages/page-047.html", "../versions/114/pages/page-999.html")),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="handbook-lookup-mutations-") as raw:
        base = Path(raw)
        for index, (name, mutation) in enumerate(cases, 1):
            fixture = base / f"case-{index:02d}"
            copy_fixture(fixture)
            mutation(fixture)
            command = [sys.executable, "scripts/validate_reference_lookup.py"]
            completed = subprocess.run(command, cwd=fixture, text=True, capture_output=True, timeout=120)
            if completed.returncode == 0:
                raise AssertionError(f"mutation not caught: {index}. {name}")
            results.append({"mutation": index, "name": name, "caught": True, "evidence": (completed.stdout + completed.stderr).strip().splitlines()[0][:160]})
            shutil.rmtree(fixture)
    print(json.dumps({"status": "REFERENCE LOOKUP MUTATIONS PASSED", "caught": f"{len(results)}/{len(cases)}", "uncaught": 0, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
