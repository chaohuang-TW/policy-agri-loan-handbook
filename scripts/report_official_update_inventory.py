#!/usr/bin/env python3
"""Report the two deliberately separate official data tracks."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads(path.read_text(encoding="utf-8"))
system=load(ROOT/"data/current/official-updates.json"); system_decisions=load(ROOT/"curation/current/official-update-decisions.json")
disaster=load(ROOT/"data/current/disaster-loan-announcements.json"); disaster_decisions=load(ROOT/"curation/current/disaster-loan-announcement-decisions.json")
print(json.dumps({"systemBusinessUpdates":{"included":len(system),"decisions":Counter(x["decision"] for x in system_decisions),"sourceTypes":Counter(x["sourceType"] for x in system)},"disasterLoanAnnouncements":{"included":len(disaster),"decisions":Counter(x["decision"] for x in disaster_decisions)}},ensure_ascii=False,indent=2))
