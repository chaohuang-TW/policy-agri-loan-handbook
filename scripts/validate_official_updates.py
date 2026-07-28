#!/usr/bin/env python3
"""Validate the system/business post-handbook official update track."""
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from content_model import sections

ALLOWED={"law.afna.gov.tw","afna.gov.tw","www.afna.gov.tw","moa.gov.tw","www.moa.gov.tw","wm.moa.gov.tw","agribank.com.tw","www.agribank.com.tw"}
TYPES={"regulation","administrative-rule","interpretation","announcement","faq","form","disaster-measure","other-official"}
BASES={"explicit-title","explicit-subject","explicit-body","common-rule","disaster-rule","bank-product","human-reviewed"}
DECISIONS={"include","already-covered","exclude-irrelevant","needs-human-review"}
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def valid(v):
    if v is None: return True
    try: date.fromisoformat(v); return True
    except (TypeError, ValueError): return False
def https(v):
    p=urlparse(v); return p.scheme=="https" and p.hostname in ALLOWED
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); root=parser.parse_args().root
    updates=load(root/"data/current/official-updates.json"); decisions=load(root/"curation/current/official-update-decisions.json"); coverage=load(root/"data/current/coverage.json"); errors=[]
    disaster_ids={x["id"] for x in load(root/"data/current/disaster-loan-announcements.json")}
    ids=[x.get("id") for x in updates]; decisions_ids=[x.get("id") for x in decisions]
    if len(ids)!=len(set(ids)): errors.append("duplicate official update id")
    if set(ids) & disaster_ids: errors.append("disaster announcement mixed into system update track")
    if len(decisions_ids)!=len(set(decisions_ids)): errors.append("duplicate candidate decision id")
    if {x["id"] for x in decisions if x.get("decision")=="include"}!={x["id"] for x in updates}: errors.append("include decisions and official-updates records do not match exactly")
    for d in decisions:
        if d.get("decision") not in DECISIONS or not d.get("reason") or not d.get("evidence") or not https(d.get("sourceUrl","")): errors.append(f"invalid decision: {d.get('id')}")
    keys=set(); loan_ids={x["id"] for x in load(root/"data/114/loan-programs.json")}; section_ids={x["id"] for x in sections()}
    for x in updates:
        required={"id","officialTitle","sourceType","officialAgency","documentNumber","publishedDate","effectiveDate","versionDate","applicationPeriod","sourceUrl","relatedLoanIds","relatedSectionIds","relationBasis","relationEvidence","verifiedOn"}
        if required-set(x): errors.append(f"missing fields: {x.get('id')}"); continue
        if not x["officialTitle"] or not x["officialAgency"] or not x["relationEvidence"] or x["sourceType"] not in TYPES or x["relationBasis"] not in BASES: errors.append(f"invalid metadata: {x['id']}")
        if not any(x[k] for k in ("publishedDate","effectiveDate","versionDate")) or not x["verifiedOn"] or not all(valid(x[k]) for k in ("publishedDate","effectiveDate","versionDate","verifiedOn")): errors.append(f"invalid date: {x['id']}")
        p=x["applicationPeriod"]
        if not isinstance(x["relatedLoanIds"], list) or not isinstance(x["relatedSectionIds"], list) or not isinstance(p, dict) or set(p)!={"start","end"} or not valid(p["start"]) or not valid(p["end"]) or (p["start"] and p["end"] and p["start"]>p["end"]): errors.append(f"invalid application period: {x['id']}")
        key=(x["sourceUrl"],x["publishedDate"],x["documentNumber"])
        if key in keys: errors.append(f"duplicate official update event: {x['id']}")
        keys.add(key)
        if not https(x["sourceUrl"]): errors.append(f"non-HTTPS allowlisted official source: {x['id']}")
        if set(x["relatedLoanIds"])-loan_ids: errors.append(f"unknown related loan: {x['id']}")
        if set(x["relatedSectionIds"])-section_ids: errors.append(f"unknown related section: {x['id']}")
    review=coverage.get("officialUpdateReview",{})
    if review.get("included")!=len(updates) or review.get("needsHumanReview")!=sum(x.get("decision")=="needs-human-review" for x in decisions): errors.append("coverage counts do not match data")
    search=root/"site/assets/data/search-index.json"
    if search.is_file() and len(load(search)) != 507: errors.append("official updates leaked into the 507-record handbook search index")
    if errors:
        print("OFFICIAL UPDATE VALIDATION FAILED"); print(*("- "+e for e in errors),sep="\n"); return 1
    print(f"OFFICIAL UPDATE VALIDATION PASSED: {len(updates)} system/business updates")
if __name__=="__main__": raise SystemExit(main() or 0)
