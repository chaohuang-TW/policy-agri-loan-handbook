#!/usr/bin/env python3
"""Report the two deliberately separate official data tracks."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads(path.read_text(encoding="utf-8"))
system=load(ROOT/"data/current/official-updates.json"); system_decisions=load(ROOT/"curation/current/official-update-decisions.json")
disaster=load(ROOT/"data/current/disaster-loan-announcements.json"); disaster_decisions=load(ROOT/"curation/current/disaster-loan-announcement-decisions.json")
logs=load(ROOT/"curation/current/source-review-log.json"); decisions=system_decisions+disaster_decisions; ids={x["id"] for x in decisions}; refs={i for x in logs for i in x["candidateIds"]}; manual={x["id"] for x in decisions if x.get("discoverySource")=="manual-known-case"}
print(json.dumps({"systemBusinessUpdates":{"included":len(system),"decisions":Counter(x["decision"] for x in system_decisions),"sourceTypes":Counter(x["sourceType"] for x in system)},"disasterLoanAnnouncements":{"included":len(disaster),"decisions":Counter(x["decision"] for x in disaster_decisions)},"orphanDecisionCandidates":len(ids-refs-manual),"unknownCandidateRefs":len(refs-ids)},ensure_ascii=False,indent=2))
