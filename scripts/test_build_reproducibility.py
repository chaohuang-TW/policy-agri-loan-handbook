#!/usr/bin/env python3
"""Verify deterministic builders and atomic failure recovery in temporary outputs."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import build_all as atomic_builder
from build_search_index import build_search_index
from build_site import build_site

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
    before = {name: digest(ROOT / name) for name in PROTECTED}
    with tempfile.TemporaryDirectory(prefix="handbook-repro-") as raw:
        temp = Path(raw)
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
        shutil.copytree(first, protected_target)
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
        if protected_target.with_name(protected_target.name + ".__building__").exists():
            raise AssertionError("staging directory remained after failure")
        if protected_target.with_name(protected_target.name + ".__previous__").exists():
            raise AssertionError("previous directory remained after failure")

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
        "stagingCleanup": "passed",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
