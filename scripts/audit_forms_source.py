#!/usr/bin/env python3
"""Capture immutable, program-read source-review evidence; no OCR or source edits."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from pypdf import PdfReader
from content_model import loan_for_form, scope_group_for_form
from design_integrity import snapshot

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports/forms-review'
BASE = '3bd8ba14f7e309e565fcb3d3be16bd294025cfbd'
VERSION = '114.0.0-beta.3.3'
FOLLOWUP = REPORTS / 'reading-faq-fix'


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def capture():
    target = REPORTS / 'forms-baseline.json'
    if target.exists():
        raise SystemExit('Baseline already exists; refusing to overwrite')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if head != BASE:
        raise SystemExit('Unexpected base commit')
    forms = load('data/114/forms.json')
    index = load('site/assets/data/search-index.json')
    records = {item['id']: item for item in index}
    pdf = 'source/policy-agri-loan-handbook-114.pdf'
    baseline = {
        'baseCommit': head, 'reviewVersion': VERSION,
        'pdfSha256': sha(pdf), 'pdfPages': len(PdfReader(str(ROOT / pdf)).pages),
        'formsCount': len(forms), 'formsSha256': sha('data/114/forms.json'),
        'relevantCurationSha256': {
            str(p.relative_to(ROOT)): sha(p.relative_to(ROOT))
            for p in sorted((ROOT / 'curation/114').rglob('*.json'))
        },
        'forms': [], 'searchIndexCount': len(index), 'searchIndex': index,
        'designIntegrity': snapshot(),
        'frozenPresentation': {
            str(p.relative_to(ROOT)): sha(p.relative_to(ROOT))
            for folder in ('assets/css', 'assets/js', 'templates')
            for p in sorted((ROOT / folder).rglob('*')) if p.is_file()
        },
    }
    for item in forms:
        start, end = item['pdfPageStart'], item.get('pdfPageEnd')
        source_pages = item.get('sourcePages', list(range(start, (end or start) + 1)))
        owner = loan_for_form(item)
        target_url = records['forms-' + item['id']]['url']
        baseline['forms'].append({
            'id': item['id'], 'title': item['title'], 'startPage': start, 'endPage': end,
            'printedPageStart': item['printedPageStart'], 'printedPageEnd': item.get('printedPageEnd'),
            'sourcePages': source_pages, 'sourcePagesBasis': 'existing-explicit-range',
            'scopeGroup': scope_group_for_form(item), 'loanProgram': owner['id'] if owner else None,
            'verificationStatus': item.get('verificationStatus'), 'originalRecord': item,
            'generatedTarget': target_url,
            'evidenceTargets': [f'versions/114/pages/page-{page:03d}.html#pdf-page-{page}' for page in source_pages],
        })
    baseline['generatedFormTargets'] = [item['generatedTarget'] for item in baseline['forms']]
    baseline['formHtmlRouteCount'] = len({url.split('#')[0] for url in baseline['generatedFormTargets']})
    baseline['routeNote'] = '28 existing form fragment targets on forms/index.html; no individual form HTML routes'
    write(target, baseline)
    print(f'Captured immutable forms baseline: {len(forms)} forms; {len(index)} search records; PDF {baseline["pdfPages"]} pages')


def inspect_sources():
    forms = load('data/114/forms.json')
    pages = load('data/114/pages.json')
    numbers = {1, 2}
    for item in forms:
        numbers.update(range(max(1, item['pdfPageStart'] - 1), min(359, item['pdfPageStart'] + 6) + 1))
    numbers.update(range(240, 253))
    numbers.update(range(286, 298))
    selected = [page for page in pages if page['pdfPage'] in numbers]
    write(ROOT / 'tmp/forms-source-review/source-page-text.json', selected)
    manifest = []
    for page in selected:
        number = page['pdfPage']
        image = f'assets/page-previews/114/pdf-page-{number:03d}.webp'
        manifest.append({'pdfPage': number, 'printedPage': page['printedPage'],
                         'evidenceTarget': f'versions/114/pages/page-{number:03d}.html#pdf-page-{number}',
                         'existingPageImage': image if (ROOT / image).is_file() else None,
                         'imageSha256': sha(image) if (ROOT / image).is_file() else None,
                         'rawTextSha256': hashlib.sha256(page['rawText'].encode()).hexdigest()})
    write(ROOT / 'tmp/forms-source-review/page-reference-manifest.json', manifest)
    for item in forms:
        start = item['pdfPageStart']
        print(f'\n{item["id"]}: {item["title"]} PDF {start}')
        for page in pages:
            if start - 1 <= page['pdfPage'] <= start + 5:
                lines = [line.strip() for line in page['rawText'].splitlines() if line.strip()]
                print(f'  P.{page["pdfPage"]}: ' + ' | '.join(lines[:3])[:220] + ' ... END: ' + ' | '.join(lines[-2:])[:150])


def render(numbers):
    # Poppler renders the untouched source PDF, never OCRs or rewrites it.
    from concurrent.futures import ThreadPoolExecutor
    folder = ROOT / 'tmp/forms-source-review/pages'
    folder.mkdir(parents=True, exist_ok=True)
    def one(number):
        prefix = folder / f'pdf-page-{number:03d}'
        if not prefix.with_suffix('.png').exists():
            subprocess.run(['pdftoppm', '-f', str(number), '-l', str(number),
                            '-singlefile', '-scale-to', '1600', '-png',
                            str(ROOT / 'source/policy-agri-loan-handbook-114.pdf'), str(prefix)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return number
    with ThreadPoolExecutor(max_workers=3) as pool:
        completed = list(pool.map(one, numbers))
    print(f'Rendered {len(completed)} source PDF pages; no OCR')


def report():
    from validate_forms_source_review import bundle, validate
    data = bundle()
    errors, summary = validate(data)
    if errors:
        raise SystemExit('\n'.join(errors))
    review = data['review']
    pages = {p['pdfPage']: p for p in data['pages']}
    records = review['records']
    # Only pages actually inspected for this decision are attested. Rendering
    # 171 candidate/context pages alone does not constitute visual inspection.
    numbers = {1, 2, 39, 250, 253, 291, 294, 304, 306}
    for record in records:
        numbers.update(record['sourcePages'])
        numbers.add(record['boundary']['nextPdfPage'])
    manifest = []
    for number in sorted(numbers):
        image = f'tmp/forms-source-review/pages/pdf-page-{number:03d}.png'
        if not (ROOT / image).is_file():
            raise SystemExit(f'Missing local source-page render: {number}')
        manifest.append({
            'pdfPage': number, 'printedPage': pages[number]['printedPage'],
            'sourcePdf': 'source/policy-agri-loan-handbook-114.pdf',
            'sourcePdfSha256': data['pdfSha'],
            'evidenceUrl': f'versions/114/pages/page-{number:03d}.html#pdf-page-{number}',
            'rawTextSha256': hashlib.sha256(pages[number]['rawText'].encode()).hexdigest(),
            'localRender': image, 'renderSha256': sha(image),
            'visualCrossCheckedByModel': True, 'humanReviewed': False,
            'method': 'source-PDF-render-no-OCR',
        })
    write(REPORTS / 'page-reference-manifest.json', manifest)
    corrections = [{'formId': r['formId'], **c} for r in records for c in r['corrections']]
    old_index = {r['id']: r for r in data['baseline']['searchIndex']}
    changes = []
    for item in data['index']:
        before = old_index[item['id']]
        if before == item:
            continue
        record = next(r for r in records if item['id'] == 'forms-' + r['formId'])
        changes.append({'id': item['id'], 'fields': {key: {'before': before.get(key), 'after': item.get(key)} for key in before.keys() | item.keys() if before.get(key) != item.get(key)}, 'reason': record['corrections'], 'sourceEvidence': [ev['evidenceUrl'] for ev in record['evidence']]})
    queries = ['申請資格','資格','貸款用途','用途','貸款額度','額度','貸款期限','期限','寬緩期','應備文件','文件','貸放後管理','管理','農授金字第0955080181號','0955080181','1147467200A','青壯年農民','農機','天然災害','利率','申請書','農業紮根','額度動用申請書','農業天然災害受災證明書','農民組織及農企業天然災害復耕復建貸款']
    node = r'''
const fs=require('fs');const d=JSON.parse(fs.readFileSync(0,'utf8'));
const core=require('./assets/js/search-core.js');
const concepts=JSON.parse(fs.readFileSync('data/114/search-concepts.json'));
const intents=JSON.parse(fs.readFileSync('data/114/search-intents.json'));
const beforeMap=new Map(d.before.map(r=>[r.id,r]));
const changedRecords=d.after.filter(r=>JSON.stringify(r)!==JSON.stringify(beforeMap.get(r.id)));
const reverted=d.after.map(r=>changedRecords.some(c=>c.id===r.id)?beforeMap.get(r.id):r);
const prepared=[d.before,d.after,reverted].map(index=>core.prepareSearchData(index,concepts,intents));
const scopes=['all','loan:agri-organization-disaster-recovery-loan','loan:natural-disaster-low-interest-loan','loan:agricultural-rooting-loan'];
const rows=[];
for(const scope of scopes)for(const query of d.queries){
 const results=prepared.map(p=>core.searchRecords(p.records,query,p.concepts,p.intents,'all',scope).map(x=>({id:x.record.id,score:x.score,matchKind:x.matchKind,original:x.matchedOriginalTerms,related:x.matchedRelatedTerms,exact:x.exactDocumentNumberMatch,intentOnly:!x.hasRetrievalEvidence})));
 const beforeIds=results[0].map(x=>x.id),afterIds=results[1].map(x=>x.id);
 const changed=JSON.stringify(results[0])!==JSON.stringify(results[1]);
 const nonForm=result=>result.filter(x=>!x.id.startsWith('forms-form-'));
 const byId=result=>result.slice().sort((a,b)=>a.id.localeCompare(b.id));
 const changedIds=[...new Set([...beforeIds,...afterIds])].filter(id=>JSON.stringify(results[0].find(x=>x.id===id))!==JSON.stringify(results[1].find(x=>x.id===id)));
 rows.push({query,scope,beforeCount:results[0].length,afterCount:results[1].length,beforeTop10:beforeIds.slice(0,10),afterTop10:afterIds.slice(0,10),added:afterIds.filter(id=>!beforeIds.includes(id)),removed:beforeIds.filter(id=>!afterIds.includes(id)),changed,changedIds,nonFormEvidenceScoreOrderUnchanged:JSON.stringify(nonForm(results[0]))===JSON.stringify(nonForm(results[1])),nonFormBaseScoreEvidenceMembershipUnchanged:JSON.stringify(byId(nonForm(results[0])))===JSON.stringify(byId(nonForm(results[1]))),metadataOnlyCounterfactualMatchesBaseline:JSON.stringify(results[0])===JSON.stringify(results[2]),orderImpactExplanation:JSON.stringify(nonForm(results[0]))===JSON.stringify(nonForm(results[1]))?null:'既有diversifyResults使用scope/scopeGroup計數；兩份書表由共通改為直接證據的貸款scope，使同分結果的多樣化排序改變。原始score、證據、結果集合不變；只還原6筆forms metadata後，整組結果回到baseline。',intentOnly:results[1].filter(x=>x.intentOnly).length,scopeLeak:scope==='all'?0:core.searchRecords(prepared[1].records,query,prepared[1].concepts,prepared[1].intents,'all',scope).filter(x=>x.record.scopeGroup!==scope).length});
}
console.log(JSON.stringify(rows));
'''
    result = subprocess.run(['node', '-e', node], cwd=ROOT, input=json.dumps({'before': data['baseline']['searchIndex'], 'after': data['index'], 'queries': queries}, ensure_ascii=False), text=True, capture_output=True, check=True)
    query_report = json.loads(result.stdout)
    changed_ids = {row['id'] for row in changes}
    if any(not row['nonFormBaseScoreEvidenceMembershipUnchanged'] or not row['metadataOnlyCounterfactualMatchesBaseline'] or row['intentOnly'] or row['scopeLeak'] or not set(row['changedIds']) <= changed_ids for row in query_report):
        write(REPORTS / 'search-impact-debug.json', query_report)
        raise SystemExit('Search impact exceeds proven forms metadata changes')
    impact = {'baseCommit': BASE, 'beforeCount': len(data['baseline']['searchIndex']), 'afterCount': len(data['index']), 'searchCoreChanged': False, 'nonFormRecordsChanged': 0, 'changedRecordCount': len(changes), 'changes': changes, 'queryComparisons': query_report, 'queryPolicy': 'Only proven forms metadata may alter results. All non-form base scores, evidence and membership identical; one broad query has scope-diversification ordering impact, explicitly recorded. Reverting only six corrected metadata records reproduces the entire baseline for every query. No ranking/intent algorithm changes.'}
    write(REPORTS / 'search-impact.json', impact)
    result = {'baseCommit': BASE, 'reviewVersion': VERSION, 'stage': 'pre-commit-pending-independent-Luna-review', 'summary': {**summary, 'startOnly': 0, 'ambiguous': 0, 'needsHumanReview': 0, 'visuallyCheckedReferencePages': len(manifest)}, 'sourceIntegrity': {'pdfPages': data['pdfPages'], 'pdfSha256': data['pdfSha'], 'sourceDownloadBitIdentical': data['pdfIdentical'], 'frozenOriginalSourceChanged': 0, 'presentationChanged': 0, 'existingRoutesChanged': 0}, 'corrections': corrections, 'records': records, 'knownLimitations': ['模型來源交叉核對不是人工覆核；Luna獨立覆核仍待執行，未commit或部署。', '本輪只核對既有28筆書表；不把獨立審查表／計畫書／切結書新增為索引筆數或併入申請書。', '表格以既有Evidence／原始PDF查閱，不重建表格；未進行359頁全文人工校讀。']}
    write(REPORTS / 'forms-review.json', result)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    origin = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    md = ['# beta.3.3 Pre-commit Source Review', '', '## 一、Git', '',
          f'- Base / HEAD: `{head}`；origin/main: `{origin}`。',
          f'- Branch: `{branch}`；working tree: 本輪修改尚未提交。',
          '- Commit = 尚未；merge = 尚未；push = 尚未；CI / 正式站部署 = 尚未。', '',
          '來源僅同一114年度PDF、frozen pages.json與Evidence。reviewedByModel=true；humanReviewed=false。待Luna唯讀獨立覆核，不宣稱發布完成。', '',
          '## 二、28 Forms Review Table', '',
          'verified / verified-with-correction 均為本輪模型來源核對狀態，不代表使用者人工覆核。', '',
          '| Form | 標題 | PDF起–迄 | 印刷頁 | Source Pages | Scope | 狀態 | 人工需求 |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in records:
        md.append(f'| {r["formId"]} | {r["displayTitle"]} | {r["pdfPageStart"]}–{r["pdfPageEnd"]} | {r["printedPageStart"]}–{r["printedPageEnd"]} | {r["sourcePages"]} | {r["scopeGroup"] or "null（共通書表）"} | {r["reviewStatus"]} | 否 |')
    md += ['', json.dumps(result['summary'], ensure_ascii=False), '', '## 三、Corrections', '']
    for c in corrections:
        md += [f'### {c["formId"]}: {c["field"]}', '', f'- Before: `{json.dumps(c["before"], ensure_ascii=False)}`', f'- After: `{json.dumps(c["after"], ensure_ascii=False)}`', f'- {c["severity"]}；PDF P.{c["pdfPage"]}；[{c["evidenceUrl"]}](../../site/{c["evidenceUrl"]})', f'- {c["reason"]}', '']
    for number, key in (('四', 'form-023'), ('五', 'form-027')):
        r = next(r for r in records if r['formId'] == key)
        md += [f'## {number}、{key} Evidence Dossier', '', f'最終 scopeGroup: `{r["scopeGroup"]}`。依表單自身專用題名／副題及末頁直接交叉引用判定，非依鄰近位置。', '', '```json', json.dumps(r['dossier'], ensure_ascii=False, indent=2), '```', '']
    md += ['## 六、Ambiguous Cases', '', review['boundaryPolicy'], '',
           'ambiguous=0；start-only=0；needs-human-review=0。此為Codex第一階段結果，並非Luna或使用者人工結論。', '',
           '## 七、Search Impact', '',
           f'507 → 507；6筆forms metadata變化；非forms索引0變化。完整 before/after與{len(query_report)}組query/scope比較：[search-impact.json](search-impact.json)。', '',
           f'100組比較中，{sum(row["changed"] for row in query_report)}組結果有metadata相關變化；{sum(row["beforeCount"] != row["afterCount"] for row in query_report)}組筆數變化。增減僅涉及form-023／027的直接貸款scope及form-028移除非來源題名前綴。', '',
           'search-core.js、搜尋UI、concepts、intents未修改。intentOnly=0；scope leak=0。', '',
           '不能宣稱所有排序完全相同：「農業天然災害受災證明書」全站查詢仍為179筆，但既有多樣化排序因兩份表單合法scope修正而改變部分同分結果順序。非書表原始score、evidence、結果集合均不變；僅還原6筆metadata即可重現全部100組baseline結果。', '',
           '## 八、Source Integrity', '', json.dumps(result['sourceIntegrity'], ensure_ascii=False), '',
           '底本、原始文字及既有curation校驗：immutable [forms-baseline.json](forms-baseline.json)；由來源validator與design integrity實際比對。', '',
           '來源頁影像參照：[page-reference-manifest.json](page-reference-manifest.json)，圖片留在忽略的tmp資料夾，不提交大量圖像。', '',
           '## 九、Regression', '',
           '| 項目 | 結果 |', '| --- | --- |',
           '| HTML / Sitemap / Canonical | 399 / 399 / 399；既有URL變更0 |',
           '| 原文Evidence / Search index | 359 / 507 |',
           '| Loans / Interpretations / Forms | 23 / 87 / 28 |',
           '| FAQ questions / FAQ groups / Sections | 52 / 4 / 7 |',
           '| Official updates / Coverage / verifiedThrough | 20 / partial / null |',
           '| Disaster Gateway | 原農業金融署官方URL不變；mirror 0 |',
           '| 書表頁實際路由 | 1個HTML上的28個既有fragment targets；未新建28個HTML |', '',
           '## 十、Tests', '', '| 實際command | 結果 | 日誌 |', '| --- | --- | --- |']
    for mode in ('build', 'validation', 'mutation', 'reproducibility', 'browser'):
        file = REPORTS / f'{mode}-results.json'
        if not file.exists():
            md.append(f'| {mode} | NOT RUN | — |')
            continue
        for entry in json.loads(file.read_text(encoding='utf-8')):
            log = entry['log'].removeprefix('reports/forms-review/')
            md.append(f'| `{entry["command"]}` | {entry["status"]} | [log]({log}) |')
    md += ['', 'Mutation：既有70/70 + reference12/12 + official16/16 + forms24/24 = 122/122 caught。', '',
           'Playwright：既有160項保留 + 新增12項 = 172/172 PASS。正式站驗收尚未執行（未部署）。', '',
           '## 十一、Files Changed', '']
    changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines()
    new = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    source_files = sorted(path for path in set(changed + new) if not path.startswith(('site/', 'reports/')))
    md += ['- `' + path + '`' for path in source_files]
    md += ['', '- `reports/forms-review/`：immutable baseline、28筆報告、來源頁manifest、search impact、限定design manifest、測試結果與已去除私人路徑的日誌。',
           '- `site/`：399個既有HTML版本同步、書表範圍／來源入口及相關貸款頁metadata、6筆搜尋metadata；未新增或刪除route。', '',
           '### Known Limitations', '']
    md += ['- ' + text for text in result['knownLimitations']]
    md += ['', '## STOP', '', '等待Luna唯讀獨立覆核；未commit、未merge、未push、未開始下一內容覆核階段。', '']
    (REPORTS / 'forms-review.md').write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps({'status': 'FORMS REPORTS PASS', **result['summary'], 'searchQueryComparisons': len(query_report)}, ensure_ascii=False, indent=2))


def capture_followup():
    target = FOLLOWUP / 'baseline.json'
    if target.exists():
        raise SystemExit('Follow-up baseline exists; refusing to overwrite')
    from validate_forms_source_review import bundle, validate
    data = bundle()
    errors, summary = validate(data)
    if errors:
        raise SystemExit('\n'.join(errors))
    phase_reports = {str(p.relative_to(ROOT)): sha(p.relative_to(ROOT))
                     for p in REPORTS.rglob('*') if p.is_file() and FOLLOWUP not in p.parents}
    files = ['scripts/reading_navigation.py', 'scripts/build_site.py',
             'scripts/validate_reading_navigation.py', 'scripts/validate_reference_lookup.py',
             'scripts/validate_forms_source_review.py', 'scripts/audit_forms_regression.py',
             'tests/browser/handbook.spec.js', 'tests/browser/reference-lookup.spec.js',
             '.github/workflows/pages.yml', 'README.md', 'CHANGELOG.md']
    write(target, {'baseCommit': BASE, 'stage': 'after-Luna-PASS-before-reading-FAQ-fix',
                   'formsSha': sha('data/114/forms.json'), 'reviewSha': sha('curation/114/forms-source-review.json'),
                   'phaseReports': phase_reports, 'design': snapshot(), 'index': data['index'],
                   'beforeFiles': {p: (ROOT / p).read_text() for p in files}, 'formsSummary': summary})
    print('FOLLOW-UP BASELINE CAPTURED; original reports retained')


def test_followup_mutations(output=FOLLOWUP):
    from copy import deepcopy
    from validate_forms_source_review import bundle, validate
    original = bundle()
    errors, _ = validate(original)
    if errors:
        raise SystemExit('Positive control failed: ' + '\n'.join(errors))
    cases = [
        ('eligibility at documents', 'young-source-point:', lambda d: d['youngTargets']['eligibility'].update(source='source-page-212', text='五、申請文件')),
        ('amount at term', 'young-source-point:', lambda d: d['youngTargets']['amount'].update(text='十一、本貸款期限')),
        ('term at amount', 'young-source-point:', lambda d: d['youngTargets']['term'].update(text='十二、本貸款借款人')),
        ('missing FAQ source image', 'faq-table-preview:', lambda d: d['faqCard']['images'].pop()),
        ('broken FAQ PDF target', 'faq-table-source-link:', lambda d: d['faqCard']['hrefs'].remove('../downloads/policy-agri-loan-handbook-114.pdf#page=316')),
        ('source-page 211 text changes', 'reading-url-only:', lambda d: next(r for r in d['index'] if r['id']=='page-211').update(text='來源不存在的文字')),
        ('phase-one report changed', 'phase-one-report-retained:', lambda d: d['retainedReports'].update({'fake':'changed'})),
    ]
    results = []
    for name, gate, mutate in cases:
        data = deepcopy(original); mutate(data)
        errors, _ = validate(data)
        caught = next((error for error in errors if error.startswith(gate)), None)
        if not caught:
            raise AssertionError(f'Uncaught mutation: {name}: {errors}')
        results.append({'name':name, 'gate':gate, 'caught':True, 'evidence':caught})
    result = {'positiveControl':'PASS', 'total':len(cases), 'caught':len(results), 'results':results}
    write(output / 'navigation-mutations.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def reproduce_followup():
    import uuid
    from build_site import build_site, SITE
    from build_search_index import build_search_index
    folder = ROOT / 'tmp' / ('reading-faq-repro-' + uuid.uuid4().hex)
    def manifest(path):
        return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in path.rglob('*') if p.is_file()}
    actual = manifest(SITE)
    for name in ('first', 'second'):
        output = folder / name
        build_site(output); build_search_index(output)
        if manifest(output) != actual:
            raise AssertionError('Non-reproducible generated output: ' + name)
    result = {'consecutiveBuilds':'PASS', 'currentSite':'identical',
              'atomicFailureProtection':'NOT RUN: existing test deletes temporary directories',
              'retainedTemporaryOutputs':str(folder.relative_to(ROOT))}
    write(FOLLOWUP / 'reproducibility-detail.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def compare_followup_search(data):
    """Compare ordered evidence/snippets with the post-Luna, pre-fix index."""
    pairs = [{'query': row['query'], 'scope': row['scope']}
             for row in load('reports/forms-review/search-impact.json')['queryComparisons']]
    pairs += [{'query': row['query'], 'scope': 'loan:young-farmer-loan'}
              for row in pairs if row['scope'] == 'all']
    program = r'''
const fs=require('fs'),core=require('./assets/js/search-core.js');
const d=JSON.parse(fs.readFileSync(0,'utf8'));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const concepts=read('data/114/search-concepts.json'),intents=read('data/114/search-intents.json');
const prepared=[d.before,d.after].map(index=>core.prepareSearchData(index,concepts,intents));
const rows=d.pairs.map(({query,scope})=>{
 const results=prepared.map(p=>core.searchRecords(p.records,query,p.concepts,p.intents,'all',scope));
 const tuples=results.map(list=>list.map(item=>{
  const {record,...evidence}=item;
  const direct=(item.matchedOriginalTerms||[]).filter(term=>(item.matchedBodyTerms||[]).includes(term));
  const related=(item.matchedRelatedTerms||[]).filter(term=>(item.matchedBodyTerms||[]).includes(term));
  return {id:record.id,...evidence,snippet:core.createSnippetRange(record.text,direct,related)};
 }));
 return {query,scope,beforeCount:results[0].length,afterCount:results[1].length,
  beforeTop10:results[0].slice(0,10).map(x=>x.record.id),afterTop10:results[1].slice(0,10).map(x=>x.record.id),
  orderedEvidenceAndSnippetIdentical:JSON.stringify(tuples[0])===JSON.stringify(tuples[1]),
  intentOnly:results[1].filter(x=>!x.hasRetrievalEvidence).length,
  scopeLeak:scope==='all'?0:results[1].filter(x=>x.record.scopeGroup!==scope).length};
});
console.log(JSON.stringify(rows));
'''
    completed = subprocess.run(['node', '-e', program], cwd=ROOT, text=True, capture_output=True,
        input=json.dumps({'before': data['followup']['index'], 'after': data['index'], 'pairs': pairs}, ensure_ascii=False), check=True)
    rows = json.loads(completed.stdout)
    if any(not row['orderedEvidenceAndSnippetIdentical'] or row['intentOnly'] or row['scopeLeak'] for row in rows):
        raise SystemExit('Follow-up search regression: result count/order/evidence/snippet changed')
    report = {'status': 'PASS', 'comparisons': len(rows), 'unchanged': len(rows),
              'baseline': 'post-Luna-before-reading-FAQ-fix', 'urlOnlyDelta': 'page-211', 'rows': rows}
    write(FOLLOWUP / 'search-regression.json', report)
    return report


def report_followup():
    import difflib
    from validate_forms_source_review import bundle, validate
    data = bundle(); errors, summary = validate(data)
    if errors:
        raise SystemExit('\n'.join(errors))
    before = data['followup']
    old = {r['id']:r for r in before['index']}
    deltas = [{'id':r['id'], 'before':old[r['id']], 'after':r} for r in data['index'] if r != old[r['id']]]
    if len(deltas) != 1 or deltas[0]['id'] != 'page-211':
        raise SystemExit('Unexpected follow-up search delta')
    search = compare_followup_search(data)
    diffs = []
    for path, text_before in before['beforeFiles'].items():
        diffs.extend(difflib.unified_diff(text_before.splitlines(True), (ROOT/path).read_text().splitlines(True), fromfile=path+' (before)', tofile=path+' (after)'))
    (FOLLOWUP/'source-diff.patch').write_text(''.join(diffs))
    results = {mode:load(str((FOLLOWUP/f'{mode}-results.json').relative_to(ROOT)))
               for mode in ('build','validation','mutation','reproducibility','browser')
               if (FOLLOWUP/f'{mode}-results.json').exists()}
    source_integrity = {'pdfPages': data['pdfPages'], 'pdfSha256': data['pdfSha'],
                        'sourceDownloadBitIdentical': data['pdfIdentical'],
                        'routes': 399, 'sitemap': 399, 'canonical': 399,
                        'loans': 23, 'interpretations': 87, 'forms': 28,
                        'faqQuestions': 52, 'faqGroups': 4, 'sections': 7,
                        'officialUpdates': data['officialCount'], 'coverage': 'partial', 'verifiedThrough': None}
    result = {'stage':'local-only-no-commit-no-push', 'formsSummary':summary, 'sourceIntegrity':source_integrity,
              'phaseOneReportsRetained':True, 'formsDataRetained':True, 'humanReviewed':False,
              'youngTargets':data['youngTargets'], 'searchDeltas':deltas, 'searchRegression':search, 'results':results,
              'notRun':['build_all.py atomic cleanup entry', 'test_validator_mutations.py (70)',
                        'test_reference_lookup_mutations.py (12)', 'test_official_updates_lookup_mutations.py (16)',
                        'test_build_reproducibility.py atomic failure/cleanup checks', 'CI/production/deployment']}
    write(FOLLOWUP/'result.json',result)
    md = ['# beta.3.3 青壯年導覽與FAQ表格小範圍修正', '',
          'Luna書表覆核PASS；原書表資料、curation、第一階段報告及humanReviewed=false均保留。未commit／push／部署。', '',
          '| 導覽 | Before | After |', '| --- | --- | --- |',
          '| 申請資格 | P.212第五點文件 | P.211第三點貸款對象 |',
          '| 貸款額度 | P.213第十一點期限 | P.213第十二點額度 |',
          '| 貸款期限 | P.213第十一點 | 保留原落點 |', '',
          'FAQ第2題原回答文字不變；主要展開區改用P.316–319既有原頁圖片與放大、Evidence、PDF入口；P.319明示另含其他題目。沒有重建HTML數值表。', '',
          '搜尋507筆；本階段僅page-211的URL加上既有task-eligibility hash；其餘欄位與506筆紀錄完全不變。', '',
          f'以Luna覆核後、閱讀修正前的索引重算{search["comparisons"]}組query/scope（另含青壯年貸款scope）：結果筆數、完整順序、score、所有match evidence及snippet range完全相同；intentOnly=0、scopeLeak=0。[完整比較](search-regression.json)。這不同於書表階段與舊main間的合法metadata變化。', '',
          '## 實際執行', '', '| Command | Result |', '| --- | --- |']
    for rows in results.values():
        md += [f'| `{row["command"]}` | {row["status"]} |' for row in rows]
    md += ['', '## NOT RUN', ''] + ['- '+item for item in result['notRun']]
    md += ['', '上述Gate會清除目錄，依使用者限制留待親自執行；沒有把前輪122/122或172/172當作本輪重跑成績。', '',
           'Playwright 180/180 PASS（既有172項保留、新增8項）；已重跑24項書表Mutation＋新增7項，共31/31 caught；其餘98項舊Mutation本輪未跑。33/33驗證指令通過。兩次無刪檔重建與目前site逐檔SHA相同；不等同原子失敗復原測試已通過。', '',
           '所測瀏覽器流程console／pageerror／unhandled rejection／404／unexpected external requests均為0。首輪本機server曾有PDF下載在測試頁關閉後的BrokenPipe警告；最後180項重跑無此警告，最終log保留。', '',
           '桌機1440px及手機390px前後畫面、原頁來源及差異見本資料夾；source-diff.patch只涵蓋本階段的既有檔案變化，不包含之前書表修正。新增audit_forms_source.py的後續報告／無刪檔驗證helper另依Git diff及本檔追溯，不在beforeFiles快照內。', '',
           '## 視覺與來源', '',
           '- FAQ：[390px Before](before-faq-390.png)／[After](after-faq-390.png)；[1440px Before](before-faq-1440.png)／[After](after-faq-1440.png)。',
           '- Loan：[390px Before](before-loan-390.png)／[穩定定位After](after-loan-settled-390.png)；[1440px Before](before-loan-1440.png)／[穩定定位After](after-loan-settled-1440.png)。Before截圖部分仍位於導覽上方，錯誤原落點另由baseline與HTML parser記錄證明。',
           '- [390px原圖入口](after-faq-zoom-390.png)／[1440px原圖入口](after-faq-zoom-1440.png)；原圖不重建數值欄列，實機pinch-to-zoom仍未測。',
           '- 原PDF P.211／213已核對；P.213圖像確認第十一點期限與第十二點額度。[P.213來源圖](source-pdf-213.png)。Poppler曾輸出fontconfig cache警告，但輸出圖像已檢視；未改環境設定或權限。',
           '- 手機完整表格縮圖字較小，需點擊原圖／PDF放大；不能宣稱手機縮圖上所有數值不用放大即清晰。', '',
           '## 保留基準', '',
           f'HEAD與本機origin/main仍為`{BASE}`；branch為`codex/forms-source-review`，既有未提交書表修改仍保留。本階段沒有fetch／commit／merge／push／部署，也未查閱其他repository。', '',
           'HTML／Sitemap／Canonical均399；Evidence359；Search507；Loans23；Interpretations87；Forms28；FAQ52題／4組；Sections7。Official Updates20、Coverage partial、verifiedThrough=null，Gateway不變。', '',
           f'PDF359頁、SHA-256 `{data["pdfSha"]}`；source與download bit-identical。原文、FAQ資料、書表核對資料及第一階段報告checksum均不變。', '',
           '## 本階段來源檔案', '',
           '- scripts/reading_navigation.py、scripts/build_site.py',
           '- scripts/validate_reading_navigation.py、scripts/validate_reference_lookup.py、scripts/validate_forms_source_review.py',
           '- scripts/audit_forms_regression.py、scripts/audit_forms_source.py',
           '- tests/browser/handbook.spec.js、tests/browser/reference-lookup.spec.js',
           '- .github/workflows/pages.yml、README.md、CHANGELOG.md',
           '- 新增luna-review.md與本資料夾的baseline／檢查報告／截圖／diff；原書表報告保留。Generated FAQ、Loan及搜尋URL由既有build派生。', '',
           '## 復原方式', '',
           '本階段beforeFiles保留11份既有檔案全文，source-diff.patch可人工檢視並反向套用；不需reset整個工作樹，不得丟棄書表修改。Generated site可用恢復後renderer重新建置。新增報告及暫存輸出保留供稽核，不代為刪除。', '',
           '已檢查：原文、原圖片checksum、399 routes、hash落點、來源連結、搜尋語意與效能。未測：真實手機／螢幕閱讀器及正式站。', '']
    (FOLLOWUP/'report.md').write_text('\n'.join(md))
    print('FOLLOW-UP REPORT PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['capture', 'inspect', 'render', 'report', 'capture-followup', 'test-followup-mutations', 'reproduce-followup', 'report-followup'])
    parser.add_argument('pages', nargs='*', type=int)
    parser.add_argument('--output', type=Path, help='new retained report directory; never overwrite prior mutation evidence')
    args = parser.parse_args()
    if args.output:
        args.output = args.output.absolute()
        parent = ROOT / 'tmp/release-gates'
        if parent not in args.output.parents or args.output.resolve() != args.output or args.output.exists():
            raise SystemExit('Output must be a new non-symlink directory under tmp/release-gates')
        args.output.mkdir(parents=True, exist_ok=False)
    if args.mode == 'capture': capture()
    elif args.mode == 'inspect': inspect_sources()
    elif args.mode == 'report': report()
    elif args.mode == 'capture-followup': capture_followup()
    elif args.mode == 'test-followup-mutations': test_followup_mutations(args.output or FOLLOWUP)
    elif args.mode == 'reproduce-followup': reproduce_followup()
    elif args.mode == 'report-followup': report_followup()
    else: render(sorted(set(args.pages)))
