#!/usr/bin/env python3
"""Validate the separate official natural-disaster low-interest-loan track."""
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
ALLOWED={"law.afna.gov.tw","afna.gov.tw","www.afna.gov.tw","moa.gov.tw","www.moa.gov.tw","wm.moa.gov.tw"}; DEC={"include","exclude-no-low-interest-loan","already-covered","duplicate","needs-human-review"}
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def valid(v):
    if v is None:return True
    try: date.fromisoformat(v);return True
    except (TypeError,ValueError):return False
def okurl(v): p=urlparse(v); return p.scheme=="https" and p.hostname in ALLOWED
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);r=p.parse_args().root; data=load(r/"data/current/disaster-loan-announcements.json"); ds=load(r/"curation/current/disaster-loan-announcement-decisions.json"); errs=[]
 ids=[x.get("id") for x in data]; inc={x["id"] for x in ds if x.get("decision")=="include"}
 if len(ids)!=len(set(ids)):errs.append("duplicate disaster id")
 if inc!=set(ids):errs.append("include decisions and disaster records do not match exactly")
 keys=set()
 for x in ds:
  if x.get("decision") not in DEC or not x.get("officialTitle") or not x.get("reason") or not x.get("evidence") or not okurl(x.get("sourceUrl","")):errs.append(f"invalid disaster decision: {x.get('id')}")
 for x in data:
  required={"id","officialTitle","officialAgency","documentNumber","publishedDate","effectiveDate","applicationPeriod","sourceUrl","disasterName","areaText","itemText","relationEvidence","verifiedOn"}
  if required-set(x):errs.append(f"missing fields: {x.get('id')}");continue
  period=x["applicationPeriod"]; key=(x["sourceUrl"],x["publishedDate"],x["documentNumber"])
  if not x["officialTitle"] or not x["officialAgency"] or not x["relationEvidence"] or not x["publishedDate"] or not x["verifiedOn"] or not isinstance(period,dict) or not all(valid(x[k]) for k in ("publishedDate","effectiveDate","verifiedOn")) or not valid(period.get("start")) or not valid(period.get("end")) or (period.get("start") and period.get("end") and period["start"]>period["end"]):errs.append(f"invalid disaster metadata: {x['id']}")
  if not okurl(x["sourceUrl"]):errs.append(f"non-HTTPS allowlisted disaster source: {x['id']}")
  if key in keys:errs.append(f"duplicate disaster announcement: {x['id']}")
  keys.add(key)
 if errs:print("DISASTER ANNOUNCEMENT VALIDATION FAILED");print(*("- "+e for e in errs),sep="\n");return 1
 print(f"DISASTER ANNOUNCEMENT VALIDATION PASSED: {len(data)} announcements")
if __name__=="__main__":raise SystemExit(main() or 0)
