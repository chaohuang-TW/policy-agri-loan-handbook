#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
load=lambda path:json.loads(path.read_text(encoding="utf-8"))
coverage=load(ROOT/"data/current/coverage.json")["officialUpdateReview"]; logs=load(ROOT/"curation/current/source-review-log.json"); system=load(ROOT/"curation/current/official-update-decisions.json"); disaster=load(ROOT/"curation/current/disaster-loan-announcement-decisions.json")
decision_ids={x["id"] for x in system+disaster}; refs={i for x in logs for i in x["candidateIds"]}; manual={x["id"] for x in system+disaster if x.get("discoverySource")=="manual-known-case"}
print(json.dumps({"searchStartDate":coverage["searchStartDate"],"coverageStatus":coverage["coverageStatus"],"globalVerifiedThrough":coverage["verifiedThrough"],"sources":[{"source":x["sourceName"],"status":x["status"],"reviewedThrough":x["reviewedThrough"],"discoveryHitCount":x["discoveryHitCount"],"candidateCount":x["candidateCount"],"candidateIds":x["candidateIds"]} for x in logs],"systemBusinessUpdates":{"total":len(system),"decisions":Counter(x["decision"] for x in system)},"disasterAnnouncements":{"totalCandidates":len(disaster),"decisions":Counter(x["decision"] for x in disaster)},"orphanDecisionCandidates":len(decision_ids-refs-manual),"unknownCandidateRefs":len(refs-decision_ids)},ensure_ascii=False,indent=2))
