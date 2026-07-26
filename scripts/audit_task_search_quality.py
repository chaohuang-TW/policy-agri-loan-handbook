#!/usr/bin/env python3
"""Run the source-attested task-search quality matrix through the browser core."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js is required for task-search quality audit")
    completed = subprocess.run(
        [node, "scripts/test_task_search_semantics.cjs"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    if completed.returncode:
        print("TASK SEARCH QUALITY AUDIT FAILED")
        print((completed.stdout + completed.stderr).strip())
        return 1
    report = json.loads(completed.stdout)
    print("TASK SEARCH QUALITY AUDIT PASSED")
    for item in report["tasks"]:
        print(json.dumps({
            "label": item["label"],
            "visibleQuery": item["visibleQuery"],
            "conceptTerms": item["conceptTerms"],
            "totalResults": item["totalResults"],
            "top10Types": item["top10Types"],
            "top10Ids": item["top10Ids"],
            "top10Titles": item["top10Titles"],
            "directSourcePhraseMatchCount": item["directSourcePhraseMatchCount"],
            "contextTitleDistribution": item["contextTitleDistribution"],
            "top10SemanticMatchCount": item["top10SemanticMatchCount"],
            "pass": item["pass"],
        }, ensure_ascii=False))
    print(json.dumps({
        "sampleLoans": report["sampleLoans"],
        "sampleSections": report["sampleSections"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
