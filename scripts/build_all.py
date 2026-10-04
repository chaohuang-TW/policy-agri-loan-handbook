#!/usr/bin/env python3
"""Atomically build the complete deterministic Pages artifact."""
from __future__ import annotations

import os
import json
from pathlib import Path

from build_search_index import build_search_index
from build_site import build_site
from audit_forms_regression import retained_workspace

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def verify_staging(path: Path) -> None:
    required = (
        "index.html",
        "sitemap.xml",
        "assets/css/site.css",
        "assets/js/search-core.js",
        "assets/js/search.js",
        "assets/js/site-tools.js",
        "assets/js/official-updates-lookup.js",
        "assets/data/search-index.json",
        "assets/data/search-concepts.json",
        "assets/data/search-intents.json",
        "assets/data/faq-items.json",
        "assets/data/official-updates.json",
        "assets/data/current-coverage.json",
        "downloads/policy-agri-loan-handbook-114.pdf",
    )
    missing = [name for name in required if not (path / name).is_file()]
    html_count = len(list(path.rglob("*.html")))
    if missing or html_count != 399:
        raise RuntimeError(f"incomplete staged site: missing={missing}, html={html_count}")


def build_all(target: Path = SITE) -> Path:
    target = Path(target).absolute()
    if target.resolve() != target or (target != SITE and ROOT / 'tmp/release-gates' not in target.parents):
        raise ValueError('Build target must be site or a non-symlink retained workspace')
    target.parent.mkdir(parents=True, exist_ok=True)
    workspace = retained_workspace('atomic-build', required_bytes=100 * 1024 * 1024)
    staging = workspace / 'staging'
    previous = workspace / 'previous'
    record = {'target': str(target.relative_to(ROOT)), 'status': 'building',
              'retention': 'no deletion; previous and failed outputs retained'}
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
                record['restoredPreviousSite'] = True
            raise
        record['status'] = 'published'
    except BaseException:
        record['status'] = 'failed'
        raise
    finally:
        record['stagingRetained'] = staging.exists()
        record['previousRetained'] = previous.exists()
        (workspace / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    return workspace


def main() -> None:
    build_all()
    print("Atomic site build complete")


if __name__ == "__main__":
    main()
