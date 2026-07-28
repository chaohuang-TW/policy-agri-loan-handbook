#!/usr/bin/env python3
"""Print a reproducible candidate and inclusion inventory report."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
decisions = json.loads((ROOT / "curation/current/official-update-decisions.json").read_text(encoding="utf-8"))
updates = json.loads((ROOT / "data/current/official-updates.json").read_text(encoding="utf-8"))
coverage = json.loads((ROOT / "data/current/coverage.json").read_text(encoding="utf-8"))
print(json.dumps({
    "reviewRange": [
        coverage["officialUpdateReview"]["searchStartDate"],
        coverage["officialUpdateReview"]["verifiedThrough"],
    ],
    "candidateCount": len(decisions),
    "decisionCounts": Counter(item["decision"] for item in decisions),
    "includedCount": len(updates),
    "sourceTypeCounts": Counter(item["sourceType"] for item in updates),
    "relatedLoanCount": len({loan for item in updates for loan in item["relatedLoanIds"]}),
}, ensure_ascii=False, indent=2))
