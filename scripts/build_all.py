#!/usr/bin/env python3
"""Atomically build the complete deterministic Pages artifact."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from build_search_index import build_search_index
from build_site import build_site

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
STAGING = ROOT / "site.__building__"
PREVIOUS = ROOT / "site.__previous__"


def verify_staging(path: Path) -> None:
    required = (
        "index.html",
        "sitemap.xml",
        "assets/css/site.css",
        "assets/js/search-core.js",
        "assets/js/search.js",
        "assets/js/site-tools.js",
        "assets/data/search-index.json",
        "assets/data/search-concepts.json",
        "assets/data/search-intents.json",
        "assets/data/official-updates.json",
        "assets/data/current-coverage.json",
        "downloads/policy-agri-loan-handbook-114.pdf",
    )
    missing = [name for name in required if not (path / name).is_file()]
    html_count = len(list(path.rglob("*.html")))
    if missing or html_count != 398:
        raise RuntimeError(f"incomplete staged site: missing={missing}, html={html_count}")


def build_all(target: Path = SITE) -> None:
    target = Path(target)
    staging = target.with_name(target.name + ".__building__")
    previous = target.with_name(target.name + ".__previous__")
    shutil.rmtree(staging, ignore_errors=True)
    shutil.rmtree(previous, ignore_errors=True)
    try:
        build_site(staging)
        build_search_index(staging)
        verify_staging(staging)
        if target.exists():
            os.replace(target, previous)
        try:
            os.replace(staging, target)
        except BaseException:
            if previous.exists() and not target.exists():
                os.replace(previous, target)
            raise
        shutil.rmtree(previous, ignore_errors=True)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        if previous.exists() and target.exists():
            shutil.rmtree(previous, ignore_errors=True)


def main() -> None:
    build_all()
    print("Atomic site build complete")


if __name__ == "__main__":
    main()
