#!/usr/bin/env python3
"""Report the formal system/business official-update track."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads(path.read_text(encoding="utf-8"))
system=load(ROOT/"data/current/official-updates.json"); system_decisions=load(ROOT/"curation/current/official-update-decisions.json")
logs=load(ROOT/"curation/current/source-review-log.json"); ids={x["id"] for x in system_decisions}; refs={i for x in logs for i in x["candidateIds"]}; manual={x["id"] for x in system_decisions if x.get("discoverySource")=="manual-known-case"}
print(json.dumps({"systemBusinessUpdates":{"included":len(system),"decisions":Counter(x["decision"] for x in system_decisions),"sourceTypes":Counter(x["sourceType"] for x in system)},"routineDisasterNoticesMirrored":0,"officialGatewayUrl":"https://www.afna.gov.tw/list.php?theme=natural_disaster&subtheme=","orphanDecisionCandidates":len(ids-refs-manual),"unknownCandidateRefs":len(refs-ids)},ensure_ascii=False,indent=2))
