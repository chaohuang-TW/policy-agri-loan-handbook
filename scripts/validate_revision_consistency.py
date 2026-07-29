#!/usr/bin/env python3
"""Ensure every published 114 digital revision uses manual.json as its source."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD = "114.0.0-beta.2.7.1.1.1"

def load(path): return json.loads(path.read_text(encoding="utf-8"))

def main():
    revision = load(ROOT / "data/114/manual.json")["digitalRevision"]
    errors = []
    if load(ROOT / "data/versions.json")["versions"][0]["digitalRevision"] != revision: errors.append("data/versions.json")
    if load(ROOT / "package.json")["version"] != revision: errors.append("package.json")
    if load(ROOT / "package-lock.json")["version"] != revision: errors.append("package-lock.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if f"數位版本：{revision}" not in readme: errors.append("README.md")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(r"^## " + re.escape(revision) + r"$", changelog, re.M): errors.append("CHANGELOG.md")
    html = list((ROOT / "site").rglob("*.html"))
    if len(html) != 399: errors.append("generated HTML count")
    if any(revision not in path.read_text(encoding="utf-8") for path in html): errors.append("generated HTML revision")
    beta_values = set(re.findall(r"114\.0\.0-beta\.[0-9.]+", "\n".join(path.read_text(encoding="utf-8") for path in html)))
    if beta_values != {revision}: errors.append(f"generated beta strings: {sorted(beta_values)}")
    for path in (ROOT / "README.md", ROOT / "package.json", ROOT / "package-lock.json", ROOT / "data/114/manual.json", ROOT / "data/versions.json"):
        if BAD in path.read_text(encoding="utf-8"): errors.append(f"known bad revision in {path.name}")
    if errors:
        print("REVISION CONSISTENCY VALIDATION FAILED"); print(*("- " + e for e in errors), sep="\n"); return 1
    print(f"REVISION CONSISTENCY VALIDATION PASSED: {revision}; HTML={len(html)}")

if __name__ == "__main__": raise SystemExit(main() or 0)
