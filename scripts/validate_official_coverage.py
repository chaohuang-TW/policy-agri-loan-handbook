#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from datetime import date
from pathlib import Path
REQ={"afna-law","afna-main","moa","agribank"}
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);r=p.parse_args().root; logs=load(r/"curation/current/source-review-log.json"); review=load(r/"data/current/coverage.json")["officialUpdateReview"];errs=[]
 if {x.get("sourceId") for x in logs}!=REQ:errs.append("required source reviews missing")
 for x in logs:
  try:date.fromisoformat(x["searchStartDate"]);date.fromisoformat(x["reviewedThrough"])
  except (KeyError,ValueError):errs.append(f"invalid review date: {x.get('sourceId')}")
  if x.get("status") not in {"complete","partial","blocked"} or not x.get("reviewMethods") or not x.get("queries") or not x.get("listingPagesReviewed") or not isinstance(x.get("candidateCount"),int):errs.append(f"incomplete source review: {x.get('sourceId')}")
 if review.get("coverageStatus") not in {"complete","partial"}:errs.append("invalid coverage status")
 if review.get("coverageStatus")=="complete":
  if any(x["status"]!="complete" for x in logs):errs.append("complete coverage has incomplete source")
  if not review.get("verifiedThrough"):errs.append("complete coverage has no verifiedThrough")
  elif any(review["verifiedThrough"]>x["reviewedThrough"] for x in logs):errs.append("global verifiedThrough exceeds source review")
 if review.get("coverageStatus")=="partial" and review.get("verifiedThrough") is not None: errs.append("partial coverage must not claim global verifiedThrough")
 if errs:print("OFFICIAL COVERAGE VALIDATION FAILED");print(*("- "+e for e in errs),sep="\n");return 1
 print(f"OFFICIAL COVERAGE VALIDATION PASSED: {review['coverageStatus']}")
if __name__=="__main__":raise SystemExit(main() or 0)
