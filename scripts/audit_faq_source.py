#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write the reproducible FAQ source-structure audit and question model."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from faq_lookup import build_audit  # noqa: E402


REPORTS = ROOT / "reports"
DATA = ROOT / "data" / "114"


def markdown(audit: dict) -> str:
    lines = [
        "# FAQ source structure audit",
        "",
        "This report is generated from the four ranges declared by `data/114/faq.json` and the existing `data/114/pages.json` text layer. It does not rewrite source wording.",
        "",
        f"- Groups: {audit['summary']['groupCount']}",
        f"- Source pages: {audit['summary']['sourcePageCount']}",
        f"- Deterministic question-level records: {audit['summary']['questionLevelRecords']}",
        f"- Page-level/start-only fallback records: {audit['summary']['pageLevelFallbackRecords']}",
        f"- Ambiguous cases: {audit['summary']['ambiguousCases']}",
        f"- Duplicate IDs: {audit['summary']['duplicateIds']}",
        f"- Source boundary errors: {audit['summary']['sourceBoundaryErrors']}",
        "",
        "## Groups",
        "",
        "| FAQ group | PDF pages | detected markers | question-level | fallback | ambiguous |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for group in audit["groups"]:
        detected = sum(1 for marker in group["questionMarkers"] if marker["candidate"])
        lines.append(
            f"| `{group['id']}` | {group['sourcePages'][0]}–{group['sourcePages'][-1]} | {detected} | {group['deterministicQuestionCount']} | {group['pageLevelFallbackCount']} | {len(group['ambiguousCases'])} |"
        )
        lines.append("")
        lines.append(f"### {group['title']}")
        lines.append("")
        lines.append(f"- Printed pages: {group['printedPages'][0]}–{group['printedPages'][-1]}")
        lines.append(f"- Question labels: {', '.join(marker['label'] for marker in group['questionMarkers'] if marker['candidate']) or 'none'}")
        lines.append(f"- Missing numeric labels among promoted candidates: {', '.join(str(value) for value in group['missingQuestionNumbers']) or 'none'}")
        lines.append(f"- False-positive risk: {group['falsePositiveRisk']}")
        if group["ambiguousCases"]:
            lines.append("- Ambiguous cases:")
            for case in group["ambiguousCases"]:
                lines.append(f"  - `{case['id']}`: {case['reason']}")
        lines.append("")
    lines.extend([
        "## Boundary rule",
        "",
        "A numbered marker is promoted only when the source segment contains an explicit `答` marker or a question punctuation before the next numbered marker. Table rows and non-question headings therefore remain outside the question-level model. Answers are bounded by the next promoted question or an explicit FAQ section-break heading; no end page is inferred from a later document.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    audit = build_audit()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "faq-source-structure-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "faq-source-structure-audit.md").write_text(markdown(audit), encoding="utf-8")
    (DATA / "faq-items.json").write_text(json.dumps(audit["records"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "FAQ SOURCE AUDIT PASSED", **audit["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

