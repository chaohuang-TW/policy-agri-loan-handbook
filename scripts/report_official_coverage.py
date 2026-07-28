#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads(p.read_text(encoding="utf-8"))
coverage=load(ROOT/"data/current/coverage.json")["officialUpdateReview"]; logs=load(ROOT/"curation/current/source-review-log.json"); system=load(ROOT/"curation/current/official-update-decisions.json"); disaster=load(ROOT/"curation/current/disaster-loan-announcement-decisions.json")
print(json.dumps({"reviewPeriod":[coverage["searchStartDate"],coverage["verifiedThrough"]],"sources":[{"source":x["sourceName"],"status":x["status"],"reviewedThrough":x["reviewedThrough"],"queries":x["queries"],"candidateCount":x["candidateCount"]} for x in logs],"systemBusinessUpdates":{"total":len(system),"decisions":Counter(x["decision"] for x in system)},"disasterAnnouncements":{"totalCandidates":len(disaster),"decisions":Counter(x["decision"] for x in disaster)},"coverageStatus":coverage["coverageStatus"],"verifiedThrough":coverage["verifiedThrough"]},ensure_ascii=False,indent=2))
