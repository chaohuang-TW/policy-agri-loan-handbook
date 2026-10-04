#!/usr/bin/env python3
"""Validate model source review, direct quotations, HTML and allowed deltas.

This does not certify human review or independently replace the visual review.
The immutable pre-edit baseline is retained, not recaptured after correction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from pypdf import PdfReader
from design_integrity import snapshot

ROOT = Path(__file__).resolve().parents[1]
BASE = '3bd8ba14f7e309e565fcb3d3be16bd294025cfbd'
VERSION = '114.0.0-beta.3.3'
PDF_SHA = '0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54'
REVIEW = 'curation/114/forms-source-review.json'
REPORT = ROOT / 'reports/forms-review'
FOLLOWUP = REPORT / 'reading-faq-fix'


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def compact(text):
    # Whitespace only: no punctuation replacement, OCR or semantic matching.
    return re.sub(r'\s+', '', text)


class FormsHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = {}; self.ids = []; self.current = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])
        if tag == 'li' and 'data-form-id' in attrs:
            self.current = attrs['data-form-id']
            self.rows[self.current] = {'attrs': attrs, 'links': [], 'text': ''}
        if tag == 'a' and self.current:
            self.rows[self.current]['links'].append(attrs)
    def handle_data(self, text):
        if self.current: self.rows[self.current]['text'] += text
    def handle_endtag(self, tag):
        if tag == 'li': self.current = None


def bundle():
    pdf = ROOT / 'source/policy-agri-loan-handbook-114.pdf'
    download = ROOT / 'site/downloads/policy-agri-loan-handbook-114.pdf'
    doc = FormsHTML(); doc.feed((ROOT / 'site/forms/index.html').read_text())
    current = snapshot()
    data = {
        'forms': load('data/114/forms.json'), 'review': load(REVIEW),
        'baseline': load('reports/forms-review/forms-baseline.json'),
        'pages': load('data/114/pages.json'), 'loans': load('data/114/loan-programs.json'),
        'index': load('site/assets/data/search-index.json'), 'html': doc.rows,
        'htmlIds': doc.ids, 'currentSnapshot': current,
        'presentation': {p: sha(p) for p in load('reports/forms-review/forms-baseline.json')['frozenPresentation']},
        'pdfSha': sha(pdf), 'pdfPages': len(PdfReader(str(pdf)).pages),
        'pdfIdentical': pdf.read_bytes() == download.read_bytes(),
        'coverage': load('data/current/coverage.json')['officialUpdateReview'],
        'officialCount': len(load('data/current/official-updates.json')),
        'versions': [load('data/114/manual.json')['digitalRevision'],
                     load('data/versions.json')['versions'][0]['digitalRevision'],
                     load('package.json')['version'], load('package-lock.json')['version'],
                     load('package-lock.json')['packages']['']['version']],
    }
    if (FOLLOWUP / 'baseline.json').exists():
        from validate_reading_navigation import parse as reading_parse
        from validate_reference_lookup import parse as lookup_parse
        data['followup'] = load('reports/forms-review/reading-faq-fix/baseline.json')
        data['youngTargets'] = reading_parse(ROOT / 'site/loans/young-farmer-loan/index.html').reading_targets
        data['faqCard'] = next(card for card in lookup_parse(ROOT / 'site/faq/index.html').cards if card['id'] == 'faq-112-12-q02')
        data['retainedReports'] = {p: sha(p) for p in data['followup']['phaseReports']}
        data['retainedForms'] = [sha('data/114/forms.json'), sha(REVIEW)]
    return data


def validate(data):
    errors = []
    def require(condition, code, detail=''):
        if not condition: errors.append(f'{code}: {detail}')
    forms, review, baseline = data['forms'], data['review'], data['baseline']
    records = review['records']
    expected = {f'form-{n:03d}' for n in range(1, 29)}
    require(len(forms) == 28, 'forms-count')
    require(len(records) == 28, 'review-count')
    ids = [r['formId'] for r in records]
    require(len(ids) == len(set(ids)), 'duplicate-review')
    require(set(ids) == expected == {f['id'] for f in forms}, 'review-id-inventory')
    require(baseline['baseCommit'] == review['baseCommit'] == BASE, 'base-commit')
    require(review['reviewVersion'] == VERSION and all(v == VERSION for v in data['versions']), 'revision')
    require(data['pdfSha'] == baseline['pdfSha256'] == review['pdfSha256'] == PDF_SHA, 'pdf-sha')
    require(data['pdfPages'] == 359 and data['pdfIdentical'], 'pdf-integrity')
    require(data['officialCount'] == 20, 'official-count')
    require(data['coverage']['coverageStatus'] == 'partial' and data['coverage']['verifiedThrough'] is None, 'coverage')
    require(review.get('humanReviewCompleted') is False, 'human-review-claim')
    require(len(data['index']) == 507, 'search-count')
    require(len({r['id'] for r in data['index']}) == 507, 'search-ids')
    pages = {p['pdfPage']: p for p in data['pages']}
    owners = {'loan:' + l['id']: l['title'] for l in data['loans']}
    before_forms = {r['id']: r for r in baseline['forms']}
    by_id = {f['id']: f for f in forms}
    valid_status = {'verified', 'verified-with-correction', 'start-only', 'ambiguous', 'needs-human-review'}
    def target(url, code):
        parts = urlsplit(url)
        require(not parts.scheme and not parts.netloc and not parts.query, code, url)
        path = (ROOT / 'site' / unquote(parts.path)).resolve()
        require(path.is_relative_to(ROOT / 'site') and path.is_file(), code, url)
        if path.is_file() and parts.fragment:
            doc = FormsHTML(); doc.feed(path.read_text())
            require(unquote(parts.fragment) in doc.ids, code, url)
    for r in records:
        key = r['formId']; f = by_id.get(key)
        if f is None: continue
        require(r.get('reviewStatus') in valid_status, 'review-status', key)
        require(not r.get('humanReviewed') and r.get('reviewedByModel') is True, 'human-review-claim', key)
        require(not (r['reviewStatus'].startswith('verified') and r.get('requiresHumanReview')), 'contradictory-human-status', key)
        sp = r.get('sourcePages', [])
        require(bool(sp) and len(set(sp)) == len(sp) and all(isinstance(p, int) and 1 <= p <= 359 for p in sp), 'source-pages', key)
        start, end = r.get('pdfPageStart'), r.get('pdfPageEnd')
        require(start in pages and (end is None or end in pages and end >= start), 'range-order', key)
        require(r['reviewStatus'] != 'start-only' or end is None and f.get('pdfPageEnd') is None, 'start-only-end', key)
        require(all(isinstance(p, int) and start <= p <= (end or start) for p in sp), 'source-range', key)
        require(sp == sorted(sp) and sp and sp[0] == start and (end is None or sp[-1] == end), 'source-range', key)
        for field in ('pdfPageStart', 'pdfPageEnd', 'printedPageStart', 'printedPageEnd', 'sourcePages', 'scopeGroup'):
            require(f.get(field) == r.get(field), 'form-review-mapping', key + ':' + field)
        if start in pages:
            require(r['printedPageStart'] == pages[start]['printedPage'], 'printed-page', key)
            require(compact(r['sourceTitle']) in compact(pages[start]['rawText']), 'source-title', key)
            require(compact(f['title']) == compact(r['sourceTitle']) and f.get('sourceTitle') == r['sourceTitle'], 'source-title', key)
            if r.get('sourceSubtitle'):
                require(compact(r['sourceSubtitle']) in compact(pages[start]['rawText']) and f.get('sourceSubtitle') == r['sourceSubtitle'], 'source-subtitle', key)
        if end in pages: require(r['printedPageEnd'] == pages[end]['printedPage'], 'printed-page', key)
        require(f.get('sourceReviewStatus') == r['reviewStatus'] and f.get('sourceVerified') == r.get('sourceVerified') and f.get('requiresHumanReview') == r.get('requiresHumanReview'), 'review-metadata', key)
        evidence = r.get('evidence', [])
        require(bool(evidence) if r['reviewStatus'].startswith('verified') else True, 'missing-evidence', key)
        require([e['pdfPage'] for e in evidence] == sp, 'evidence-pages', key)
        for ev in evidence:
            target(ev['evidenceUrl'], 'evidence-target')
            p = ev['pdfPage']
            require(ev['evidenceUrl'] == f'versions/114/pages/page-{p:03d}.html#pdf-page-{p}', 'evidence-page-url', key)
            if p in pages:
                for field in ('headQuote', 'tailQuote'):
                    require(bool(ev.get(field)) and compact(ev[field]) in compact(pages[p]['rawText']), 'source-quotation', key + ':' + field)
        scope = r.get('scopeGroup')
        require(scope is None or scope in owners, 'scope-target', key)
        relations = r.get('relationEvidence', [])
        require(bool(relations) if scope else True, 'relation-evidence', key)
        for ev in relations:
            p = ev['pdfPage']
            require(p in sp and p in pages and compact(ev.get('quote', '')) in compact(pages[p]['rawText']), 'relation-evidence', key)
            if scope in owners:
                require(ev.get('scopeGroup') == scope and ev.get('criterion') == 'A-form-explicit-loan-name' and compact(owners[scope]) in compact(ev['quote']), 'relation-evidence', key)
        if r['reviewStatus'].startswith('verified'):
            boundary = r.get('boundary', {})
            require(boundary.get('nextPdfPage') == (end or start) + 1 and not boundary.get('includedNextForm'), 'ending-boundary', key)
            n = boundary.get('nextPdfPage')
            if n in pages:
                require(compact(boundary.get('nextHeadingQuote', '')) in compact(pages[n]['rawText']) and bool(boundary.get('nextHeadingQuote')), 'ending-boundary', key)
                target(boundary['nextEvidenceUrl'], 'boundary-target')
        if key in ('form-023', 'form-027'):
            dossier = r.get('dossier', {})
            for field in ('formId', 'formalTitle', 'pdfPage', 'printedPage', 'previousPage', 'currentPage', 'nextPage', 'nextBoundary', 'tocNode', 'explicitLoanName', 'explicitSectionName', 'directCrossReference', 'candidateScopeGroup', 'supportingEvidence', 'opposingEvidence', 'finalStatus', 'decisionCriterion'):
                require(field in dossier, 'dossier-' + field, key)
            require(dossier.get('candidateScopeGroup') == scope and dossier.get('decisionCriterion') == 'A-form-explicit-loan-name', 'dossier-decision', key)
        row = data['html'].get(key)
        require(row is not None, 'html-form-target', key)
        if row:
            require(f['title'] in row['text'], 'html-title', key)
            require(row['attrs'].get('data-form-scope') == (scope or '') and row['attrs'].get('data-form-review') == r['reviewStatus'], 'html-review-scope', key)
            evidence_links = [a for a in row['links'] if 'data-form-evidence' in a]
            require({int(a['data-form-evidence']) for a in evidence_links} == {start, end or start}, 'html-evidence-range', key)
            for a in evidence_links:
                n = int(a['data-form-evidence'])
                require(a['href'] == f'../versions/114/pages/page-{n:03d}.html#pdf-page-{n}', 'html-evidence-target', key)
            pdf_links = [a for a in row['links'] if 'data-form-pdf' in a]
            require(len(pdf_links) == 1 and pdf_links[0]['href'] == f'../downloads/policy-agri-loan-handbook-114.pdf#page={start}', 'html-pdf-target', key)
        old = before_forms[key]['originalRecord']
        mutable = {'title', 'pdfPageEnd', 'printedPageEnd', 'sourceTitle', 'sourceSubtitle', 'sourcePages', 'rangeStatus', 'scopeGroup', 'sourceReviewStatus', 'sourceVerified', 'reviewedByModel', 'requiresHumanReview'}
        require(all(f.get(field) == value for field, value in old.items() if field not in mutable) and not set(f) - set(old) - mutable, 'unauthorized-form-field', key)
    require(len(data['html']) == 28 and len(data['htmlIds']) == len(set(data['htmlIds'])), 'html-inventory')
    current = data['currentSnapshot']; original = baseline['designIntegrity']
    followup = data.get('followup')
    if followup:
        from validate_reading_navigation import validate_young_targets
        from validate_reference_lookup import validate_faq_tables
        errors.extend(validate_young_targets(data['youngTargets']))
        errors.extend(validate_faq_tables(data['faqCard']))
        require(data['retainedReports'] == followup['phaseReports'], 'phase-one-report-retained')
        require(data['retainedForms'] == [followup['formsSha'], followup['reviewSha']], 'phase-one-forms-retained')
    require(data['presentation'] == baseline['frozenPresentation'], 'presentation-frozen')
    permitted = {'data/114/forms.json', REVIEW}
    require(all(current['frozen'].get(p) == digest for p, digest in original['frozen'].items() if p not in permitted) and not set(current['frozen']) - set(original['frozen']) - permitted, 'frozen-source-official')
    require(current['pages'].keys() == original['pages'].keys() and len(current['pages']) == 399 and current['sitemap'] == original['sitemap'], 'route-inventory')
    for path, before in original['pages'].items():
        after = current['pages'].get(path, {})
        fields = ('canonical', 'sourceText') if followup and path == 'faq/index.html' else ('canonical', 'sourceText', 'preview')
        require(all(after.get(k) == before[k] for k in fields) and set(before['ids']).issubset(after.get('ids', [])), 'rendered-source-frozen', path)
        if followup and path == 'faq/index.html':
            expected_preview = [{k: image.get(k) for k in ('src', 'width', 'height')} for image in data['faqCard']['images']]
            require(after.get('preview') == expected_preview and len(expected_preview) == 4, 'faq-preview-delta')
    old_index = {r['id']: r for r in baseline['searchIndex']}
    changed = []
    allowed_index_fields = {'title', 'text', 'headings', 'breadcrumb', 'scope', 'scopeGroup', 'contextTitle'}
    for record in data['index']:
        old = old_index.get(record['id'])
        if old == record: continue
        changed.append(record['id'])
        if followup and record['id'] == 'page-211':
            require(old is not None and {k for k in old.keys() | record.keys() if old.get(k) != record.get(k)} == {'url'}
                    and record['url'] == 'loans/young-farmer-loan/index.html#task-eligibility', 'reading-url-only', record['id'])
            continue
        require(old is not None and record['id'].startswith('forms-form-'), 'non-form-search-change', record['id'])
        if old and record['id'].startswith('forms-form-'):
            f = by_id.get(record['id'].removeprefix('forms-'), {})
            fields = {k for k in old.keys() | record.keys() if old.get(k) != record.get(k)}
            require(fields <= allowed_index_fields, 'search-schema-change', record['id'])
            require(record.get('title') == f.get('title') and record.get('scopeGroup') == f.get('scopeGroup'), 'search-form-mapping', record['id'])
    return errors, {'forms': len(forms), 'reviews': len(records), 'sourcePages': sum(len(r['sourcePages']) for r in records), 'multiPageForms': sum(len(r['sourcePages']) > 1 for r in records), 'corrected': sum(r['reviewStatus'] == 'verified-with-correction' for r in records), 'verified': sum(r['reviewStatus'] == 'verified' for r in records), 'humanReviewItems': sum(r['requiresHumanReview'] for r in records), 'routes': len(current['pages']), 'searchCount': len(data['index']), 'changedSearchRecords': changed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-design-manifest', action='store_true', help='derive narrow allowed-delta manifest only after all source gates pass')
    args = parser.parse_args()
    data = bundle(); errors, summary = validate(data)
    original = subprocess.check_output(['git', 'show', BASE + ':data/114/forms.json'], cwd=ROOT)
    if hashlib.sha256(original).hexdigest() != data['baseline']['formsSha256']:
        errors.append('immutable-baseline: original forms SHA differs from base Git object')
    if errors: raise SystemExit('\n'.join(errors))
    if args.write_design_manifest:
        expected = deepcopy(data['baseline']['designIntegrity'])
        # Preserve routes, original text, images, all old IDs and the original
        # baseline. Only verified forms metadata and its derived index vary.
        for p in ('data/114/forms.json', REVIEW):
            expected['frozen'][p] = data['currentSnapshot']['frozen'][p]
        expected['searchIndex'] = data['currentSnapshot']['searchIndex']
        destination = REPORT
        if data.get('followup'):
            expected['pages']['faq/index.html']['preview'] = data['currentSnapshot']['pages']['faq/index.html']['preview']
            destination = FOLLOWUP
        (destination / 'allowed-forms-design-manifest.json').write_text(json.dumps(expected, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'FORMS SOURCE REVIEW PASS', **summary}, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
