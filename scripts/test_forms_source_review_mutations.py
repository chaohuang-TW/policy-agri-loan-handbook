#!/usr/bin/env python3
"""Exercise real source-review validation contracts on isolated in-memory data.

No mutation touches the shared worktree. Each case must trigger its intended
error code; an unrelated failure or exception is not counted as caught.
"""
import json
from copy import deepcopy
from validate_forms_source_review import bundle, validate, REPORT


def main():
    original = bundle()
    errors, _ = validate(original)
    if errors: raise SystemExit('Positive control failed: ' + '\n'.join(errors))
    cases = [
        ('review missing one record', 'review-count', lambda d: d['review']['records'].pop()),
        ('duplicate form review', 'duplicate-review', lambda d: d['review']['records'].__setitem__(1, deepcopy(d['review']['records'][0]))),
        ('unknown form ID', 'review-id-inventory', lambda d: d['review']['records'][0].update(formId='form-999')),
        ('source page zero', 'source-pages', lambda d: d['review']['records'][0].update(sourcePages=[0])),
        ('source page 360', 'source-pages', lambda d: d['review']['records'][0].update(sourcePages=[360])),
        ('missing Evidence target', 'evidence-target', lambda d: d['review']['records'][0]['evidence'][0].update(evidenceUrl='versions/114/pages/page-999.html#pdf-page-999')),
        ('start greater than end', 'range-order', lambda d: d['review']['records'][0].update(pdfPageEnd=39)),
        ('source page outside range', 'source-range', lambda d: d['review']['records'][0].update(sourcePages=[40,41])),
        ('start-only with invented end', 'start-only-end', lambda d: d['review']['records'][0].update(reviewStatus='start-only')),
        ('verified without evidence', 'missing-evidence', lambda d: d['review']['records'][0].update(evidence=[])),
        ('human-needed but verified', 'contradictory-human-status', lambda d: d['review']['records'][0].update(requiresHumanReview=True)),
        ('invalid scope', 'scope-target', lambda d: d['review']['records'][22].update(scopeGroup='loan:fake')),
        ('scope without relation evidence', 'relation-evidence', lambda d: d['review']['records'][22].update(relationEvidence=[])),
        ('form-023 dossier missing previous page', 'dossier-previousPage', lambda d: d['review']['records'][22]['dossier'].pop('previousPage')),
        ('form-027 dossier missing next page', 'dossier-nextPage', lambda d: d['review']['records'][26]['dossier'].pop('nextPage')),
        ('forms count 29', 'forms-count', lambda d: d['forms'].append(deepcopy(d['forms'][0]))),
        ('changed source PDF SHA', 'pdf-sha', lambda d: d.update(pdfSha='0'*64)),
        ('changed official layer', 'frozen-source-official', lambda d: d['currentSnapshot']['frozen'].update({'data/current/official-updates.json':'0'*64})),
        ('search index count 506', 'search-count', lambda d: d['index'].pop()),
        ('version mismatch', 'revision', lambda d: d['versions'].__setitem__(0, '114.0.0-beta.3.2')),
        ('fake source quotation', 'source-quotation', lambda d: d['review']['records'][0]['evidence'][0].update(headQuote='來源不存在的題名')),
        ('rewritten form title', 'source-title', lambda d: d['forms'][0].update(title='重寫來源題名')),
        ('broken rendered PDF target', 'html-pdf-target', lambda d: next(a for a in d['html']['form-001']['links'] if 'data-form-pdf' in a).update(href='../downloads/missing.pdf#page=40')),
        ('CSS changed', 'presentation-frozen', lambda d: d['presentation'].update({'assets/css/site.css':'0'*64})),
    ]
    results = []
    for number, (name, code, mutate) in enumerate(cases, 1):
        data = deepcopy(original); mutate(data)
        errors, _ = validate(data)
        matching = [e for e in errors if e.startswith(code + ':')]
        if not matching: raise AssertionError(f'Mutation not caught by intended gate: {number}. {name}; errors={errors}')
        results.append({'number': number, 'name': name, 'caught': True, 'gate': code, 'evidence': matching[0]})
    report = {'status': 'FORMS MUTATIONS PASS', 'positiveControl': 'PASS', 'total': len(cases), 'caught': len(results), 'uncaught': 0, 'results': results}
    (REPORT / 'forms-mutation-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
