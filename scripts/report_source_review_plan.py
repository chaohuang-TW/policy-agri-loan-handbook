#!/usr/bin/env python3
"""Offline read-only report of the manual official-source review plan; not a crawler."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); p.add_argument("--source"); args=p.parse_args(); root=args.root
logs=json.loads((root/"curation/current/source-review-log.json").read_text()); report=[]
for x in logs:
    if not args.source or x["sourceId"]==args.source:
        report.append({"source":x["sourceId"],"dateRange":[x["searchStartDate"],x["reviewedThrough"]],"queries":x["queries"],"listingPages":x["listingPagesReviewed"],"status":x["status"],"writesFormalData":False})
print(json.dumps({"sourceReviewPlan":report,"isCrawler":False},ensure_ascii=False,indent=2))
