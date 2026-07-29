#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
load=lambda path:json.loads(path.read_text(encoding="utf-8"))
coverage=load(ROOT/"data/current/coverage.json")["officialUpdateReview"]; logs=load(ROOT/"curation/current/source-review-log.json"); system=load(ROOT/"curation/current/official-update-decisions.json"); updates=load(ROOT/"data/current/official-updates.json")
decision_ids={x["id"] for x in system}; refs={i for x in logs for i in x["candidateIds"]}; manual={x["id"] for x in system if x.get("discoverySource")=="manual-known-case"}
print(json.dumps({"searchStartDate":coverage["searchStartDate"],"coverageStatus":coverage["coverageStatus"],"globalVerifiedThrough":coverage["verifiedThrough"],"sources":[{"source":x["sourceName"],"status":x["status"],"reviewedThrough":x["reviewedThrough"],"discoveryHitCount":x["discoveryHitCount"],"candidateCount":x["candidateCount"],"outOfScopeDiscoveryHitCount":x.get("outOfScopeDiscoveryHitCount",0),"candidateIds":x["candidateIds"]} for x in logs],"officialUpdates":{"total":len(updates),"decisions":Counter(x["decision"] for x in system)},"orphanDecisionCandidates":len(decision_ids-refs-manual),"unknownCandidateRefs":len(refs-decision_ids)},ensure_ascii=False,indent=2))
