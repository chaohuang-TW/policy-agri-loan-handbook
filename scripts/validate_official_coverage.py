#!/usr/bin/env python3
"""Validate source-review completeness claims and candidate lineage."""
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path

REQ={"afna-law","afna-main","moa","agribank"}
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); root=p.parse_args().root
    logs=load(root/"curation/current/source-review-log.json"); review=load(root/"data/current/coverage.json")["officialUpdateReview"]
    decisions=load(root/"curation/current/official-update-decisions.json")
    decision_ids={x["id"] for x in decisions}; errors=[]; referenced=set()
    if {x.get("sourceId") for x in logs}!=REQ: errors.append("required source reviews missing")
    for x in logs:
        try: date.fromisoformat(x["searchStartDate"]); date.fromisoformat(x["reviewedThrough"])
        except (KeyError,ValueError): errors.append(f"invalid review date: {x.get('sourceId')}")
        ids=x.get("candidateIds")
        if x.get("status") not in {"complete","partial","blocked"} or not x.get("reviewMethods") or not x.get("queries") or not x.get("listingPagesReviewed") or not isinstance(x.get("discoveryHitCount"),int) or not isinstance(x.get("candidateCount"),int) or not isinstance(ids,list): errors.append(f"incomplete source review: {x.get('sourceId')}"); continue
        out=x.get("outOfScopeDiscoveryHitCount", 0)
        if not isinstance(out, int) or out < 0: errors.append(f"invalid out-of-scope count: {x['sourceId']}")
        if x["candidateCount"] != len(ids) or x["discoveryHitCount"] < x["candidateCount"] + out: errors.append(f"invalid candidate count lineage: {x['sourceId']}")
        if out > 0 and (not x.get("outOfScopePolicy") or not x.get("notes")): errors.append(f"missing out-of-scope policy: {x['sourceId']}")
        unknown=set(ids)-decision_ids
        if unknown: errors.append(f"unknown candidate refs: {x['sourceId']}")
        referenced.update(ids)
    manual={x["id"] for x in decisions if x.get("discoverySource")=="manual-known-case"}
    orphan=decision_ids-referenced-manual
    if orphan: errors.append("orphan decision candidates")
    if review.get("coverageStatus") not in {"complete","partial"}: errors.append("invalid coverage status")
    if review.get("coverageStatus")=="complete":
        if any(x["status"]!="complete" for x in logs): errors.append("complete coverage has incomplete source")
        if not review.get("verifiedThrough"): errors.append("complete coverage has no verifiedThrough")
        elif any(review["verifiedThrough"]>x["reviewedThrough"] for x in logs): errors.append("global verifiedThrough exceeds source review")
    if review.get("coverageStatus")=="partial" and review.get("verifiedThrough") is not None: errors.append("partial coverage must not claim global verifiedThrough")
    if errors:
        print("OFFICIAL COVERAGE VALIDATION FAILED"); print(*("- "+x for x in errors),sep="\n"); return 1
    print(f"OFFICIAL COVERAGE VALIDATION PASSED: {review['coverageStatus']}; orphan=0 unknown=0")
if __name__=="__main__": raise SystemExit(main() or 0)
