#!/usr/bin/env python3
"""Verify deterministic builders and atomic failure recovery in temporary outputs."""
from __future__ import annotations

import hashlib
import json
import shutil
import argparse
from pathlib import Path

import build_all as atomic_builder
from build_search_index import build_search_index
from build_site import build_site
from audit_forms_regression import retained_workspace, copy_retained_tree

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PROTECTED = (
    "source/policy-agri-loan-handbook-114.pdf",
    "data/114/pages.json",
    "data/114/loan-programs.json",
    "data/114/interpretations.json",
    "data/114/forms.json",
    "data/114/faq.json",
    "data/114/appendices.json",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def assert_equal(left: Path, right: Path, label: str) -> None:
    left_manifest = manifest(left)
    right_manifest = manifest(right)
    if left_manifest != right_manifest:
        missing = sorted(set(left_manifest) ^ set(right_manifest))
        changed = sorted(
            key for key in set(left_manifest) & set(right_manifest)
            if left_manifest[key] != right_manifest[key]
        )
        raise AssertionError(f"{label}: missing={missing[:5]} changed={changed[:5]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--retain-workspace', action='store_true', help='outputs are always retained; explicit acknowledgement')
    parser.parse_args()
    before = {name: digest(ROOT / name) for name in PROTECTED}
    temp = retained_workspace('reproducibility', required_bytes=600 * 1024 * 1024)
    first = temp / "first"
    second = temp / "second"
    forward = temp / "forward"
    reverse = temp / "reverse"

    atomic_builder.build_all(first)
    assert_equal(SITE, first, "committed site differs from clean build")
    atomic_builder.build_all(second)
    assert_equal(first, second, "consecutive build_all outputs differ")

    build_site(forward)
    build_search_index(forward)
    assert_equal(first, forward, "build_site then build_search_index differs")

    build_search_index(reverse)
    atomic_builder.build_all(reverse)
    assert_equal(first, reverse, "build_search_index then build_site differs")

    protected_target = temp / "protected-site"
    copy_retained_tree(first, protected_target)
    marker_before = manifest(protected_target)
    original = atomic_builder.build_search_index

    def fail_index(_output: Path):
        raise RuntimeError("injected build failure")

    atomic_builder.build_search_index = fail_index
    try:
        try:
            atomic_builder.build_all(protected_target)
        except RuntimeError as error:
            if str(error) != "injected build failure":
                raise
        else:
            raise AssertionError("injected failure unexpectedly succeeded")
    finally:
        atomic_builder.build_search_index = original
    if manifest(protected_target) != marker_before:
        raise AssertionError("failed build changed the prior site")
    failures = [p for p in (ROOT / 'tmp/release-gates').glob('atomic-build-*')
                if (p / 'build-record.json').is_file()
                and json.loads((p / 'build-record.json').read_text()).get('target') == str(protected_target.relative_to(ROOT))]
    if len(failures) != 1 or not (failures[0] / 'staging').is_dir():
        raise AssertionError('failed build evidence was not retained')

    original_replace = atomic_builder.os.replace
    def fail_publish(source, destination):
        if Path(source).name == 'staging' and Path(destination) == protected_target:
            raise RuntimeError('injected publication failure')
        return original_replace(source, destination)
    atomic_builder.os.replace = fail_publish
    try:
        try:
            atomic_builder.build_all(protected_target)
        except RuntimeError as error:
            if str(error) != 'injected publication failure': raise
        else: raise AssertionError('publication failure unexpectedly succeeded')
    finally:
        atomic_builder.os.replace = original_replace
    if manifest(protected_target) != marker_before:
        raise AssertionError('publication failure did not restore the prior site')
    final_run = atomic_builder.build_all(protected_target)
    assert_equal(first, protected_target, 'successful replacement differs')
    if not (final_run / 'previous').is_dir():
        raise AssertionError('previous successful site was not retained')
    assert_equal(first, final_run / 'previous', 'retained prior site differs')
    for run in (ROOT / 'tmp/release-gates').glob('atomic-build-*'):
        if (run / 'build-record.json').is_file():
            record = json.loads((run / 'build-record.json').read_text())
            if record['target'].startswith(str(temp.relative_to(ROOT)) + '/'):
                if record['status'] == 'failed' and not record['stagingRetained']:
                    raise AssertionError('failed staging was not retained')
                if record['status'] == 'published' and record['stagingRetained']:
                    raise AssertionError('published output still marked as staging')

    after = {name: digest(ROOT / name) for name in PROTECTED}
    if before != after:
        raise AssertionError("source or protected data changed during reproducibility test")
    print(json.dumps({
        "status": "BUILD REPRODUCIBILITY PASSED",
        "committedSite": "identical",
        "consecutiveBuilds": "identical",
        "forwardOrder": "identical",
        "reverseOrder": "identical",
        "failureProtection": "passed",
        "publicationFailureRestoration": "passed",
        "controlledRetention": "passed; no deletion",
        "workspace": str(temp.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
