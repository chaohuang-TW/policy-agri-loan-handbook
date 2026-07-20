#!/usr/bin/env python3
"""Validate durable, source-traceable interpretation-candidate decisions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/114"
CURATION = ROOT / "curation/114/interpretation-candidate-decisions.json"
REQUIRED_IDS = {f"interpretation-candidate-{n}" for n in ("089", "092", "094", "099", "108", "112", "114", "118")}
ALLOWED = {"promoted-to-source-index", "duplicate-detection", "cited-document", "continuation-reference", "duplicate-variant", "false-positive", "pending-review"}

def main() -> int:
    errors=[]
    decisions=json.loads(CURATION.read_text(encoding="utf-8")) if CURATION.exists() else []
    candidates=json.loads((DATA/"interpretation-candidates.json").read_text(encoding="utf-8"))
    pages=json.loads((DATA/"pages.json").read_text(encoding="utf-8"))
    sources={x['id'] for x in json.loads((DATA/"interpretations.json").read_text(encoding="utf-8"))}
    by_key={x['candidateKey']:x for x in candidates}
    if {x.get('candidateIdAtReview') for x in decisions} != REQUIRED_IDS: errors.append("eight required candidate decisions are missing or extra")
    for d in decisions:
        c=by_key.get(d.get('candidateKey'))
        if not c or (c['documentNumber'],c['printedPage'],c['pdfPage']) != (d.get('documentNumber'),d.get('printedPage'),d.get('pdfPage')): errors.append(f"candidate mismatch: {d.get('candidateKey')}"); continue
        if d.get('decision') not in ALLOWED or d.get('decisionBasis') != 'source-page-comparison' or d.get('reviewStatus') == 'manually-reviewed': errors.append(f"invalid decision metadata: {c['id']}")
        if not d.get('evidencePages') or not d.get('evidenceExcerpt') or not any(d['evidenceExcerpt'] in pages[p-1]['rawText'] for p in d['evidencePages']): errors.append(f"untraceable evidence: {c['id']}")
        if d['decision'] in {'continuation-reference','duplicate-variant'} and not (d.get('linkedInterpretationId') or d.get('linkedCandidateKey')): errors.append(f"missing link: {c['id']}")
        if d['decision']=='promoted-to-source-index' and d.get('linkedInterpretationId') not in sources: errors.append(f"invalid promoted source: {c['id']}")
        if d['decision']=='false-positive' and not d.get('notes'): errors.append(f"missing false-positive notes: {c['id']}")
        if d['decision']=='pending-review' and not d.get('notes'): errors.append(f"missing pending reason: {c['id']}")
        if c.get('decision') != d['decision']: errors.append(f"generated decision differs: {c['id']}")
    if errors: print('INTERPRETATION DECISIONS VALIDATION FAILED\n'+'\n'.join('- '+x for x in errors)); return 1
    print(f'INTERPRETATION DECISIONS VALIDATION PASSED: {len(decisions)} durable source decisions')
    return 0

if __name__ == '__main__': raise SystemExit(main())
