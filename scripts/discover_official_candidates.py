#!/usr/bin/env python3
"""Offline candidate-report helper. It never writes formal current data."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument("--source");args=p.parse_args();r=args.root
logs=json.loads((r/"curation/current/source-review-log.json").read_text());report=[]
for x in logs:
 if not args.source or x["sourceId"]==args.source:
  report.append({"source":x["sourceId"],"dateRange":[x["searchStartDate"],x["reviewedThrough"]],"queries":x["queries"],"listingPages":x["listingPagesReviewed"],"discoveryReason":"review log; manually decide candidates before formal inclusion"})
print(json.dumps({"candidateReport":report,"writesFormalData":False},ensure_ascii=False,indent=2))
