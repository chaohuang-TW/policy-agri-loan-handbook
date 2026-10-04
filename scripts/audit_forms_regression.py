#!/usr/bin/env python3
"""Run pre-commit gates and retain actual command/exit-code evidence.

No commit, branch switch, push or deployment is performed by this script.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/forms-review'
FOLLOWUP = REPORT / 'reading-faq-fix'
if (FOLLOWUP / 'baseline.json').exists():
    REPORT = FOLLOWUP
PYTHON_SCRIPTS = ['test_interpretation_parser', 'audit_content', 'validate_display_text',
    'validate_interpretation_metadata', 'validate_interpretation_decisions',
    'validate_index_quality', 'validate_navigation_targets', 'validate_page_rendering',
    'validate_visual_theme', 'validate_search_experience', 'validate_ux_structure',
    'validate_official_updates', 'validate_official_coverage',
    'validate_revision_consistency', 'validate_disaster_official_gateway',
    'validate_reading_navigation', 'validate_reference_lookup',
    'validate_official_updates_lookup', 'validate_forms_source_review',
    'audit_search_precision', 'audit_task_search_quality',
    'report_source_review_plan', 'report_official_update_inventory',
    'report_official_coverage', 'validate_site']


def retained_workspace(label, required_bytes=0):
    """Allocate a fresh, repo-scoped output; never clean up or reuse one."""
    if not re.fullmatch(r'[a-z][a-z0-9-]*', label):
        raise ValueError('Invalid retained-workspace label')
    parent = ROOT / 'tmp/release-gates'
    if shutil.disk_usage(ROOT).free < required_bytes + 512 * 1024 * 1024:
        raise RuntimeError('Insufficient capacity for retained outputs; no files removed')
    if parent.resolve() != parent.absolute():
        raise ValueError('Retained workspace must not traverse symlinks')
    parent.mkdir(parents=True, exist_ok=True)
    destination = parent / (label + '-' + uuid.uuid4().hex)
    destination.mkdir(exist_ok=False)
    print('Retained workspace: ' + str(destination.relative_to(ROOT)), flush=True)
    return destination


def copy_retained_tree(source, destination):
    """Independent byte copies, without hardlinks, chmod or cleanup."""
    source, destination = Path(source), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('Refusing to overwrite a fixture directory')
    destination.mkdir(parents=True, exist_ok=False)
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise ValueError('Fixture source contains a symlink')
        target = destination / path.relative_to(source)
        if path.is_dir(): target.mkdir(exist_ok=False)
        elif path.is_file(): shutil.copyfile(path, target)


def mutation_command(command, fixture):
    fixture = Path(fixture)
    if ROOT / 'tmp/release-gates' not in fixture.resolve().parents:
        raise ValueError('Validator logs must stay inside retained fixtures')
    # Keep raw machine-local diagnostics outside the validator's fixture tree;
    # the UX gate deliberately scans every file within that tree.
    logs = fixture.parent / 'validator-logs' / fixture.name
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / (uuid.uuid4().hex + '.json')
    try:
        completed = subprocess.run(command, cwd=fixture, text=True, capture_output=True,
            timeout=120, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        record = {'command': command, 'returncode': completed.returncode,
                  'stdout': completed.stdout, 'stderr': completed.stderr}
    except subprocess.TimeoutExpired as error:
        def as_text(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
        record = {'command': command, 'timeout': True,
                  'stdout': as_text(error.stdout), 'stderr': as_text(error.stderr)}
        with log.open('x', encoding='utf-8') as output:
            json.dump(record, output, ensure_ascii=False, indent=2)
        raise
    with log.open('x', encoding='utf-8') as output:
        json.dump(record, output, ensure_ascii=False, indent=2)
    completed.retained_log = str(log.relative_to(ROOT))
    return completed


def positive_control(command, fixture):
    completed = mutation_command(command, fixture)
    output = completed.stdout + completed.stderr
    if completed.returncode != 0 or not re.search(r'PASS(?:ED)?', output):
        raise AssertionError('Positive control failed: ' + output[-2000:])
    return {'status': 'PASS'}


def causal_failure(completed, expected, label):
    """An unrelated crash is a Gate failure, never a caught mutation."""
    output = completed.stdout + completed.stderr
    forbidden = ('Traceback (most recent call last)', 'ModuleNotFoundError',
                 'ImportError', 'FileNotFoundError', 'SyntaxError', 'ReferenceError')
    if completed.returncode == 0 or any(value in output for value in forbidden):
        raise AssertionError('Mutation failed to reach intended gate: ' + label + '\n' + output[-2000:])
    diagnostics = output.splitlines()
    try:
        value = json.loads(completed.stdout)
        if isinstance(value, dict) and 'errors' in value:
            diagnostics = value['errors']
    except json.JSONDecodeError:
        pass
    if isinstance(expected, dict):
        # Older Node assertions lack labels: bind to the exact assertion text,
        # then derive its current source line, rather than pinning a line number.
        source = ROOT / 'scripts/test_search_core.cjs'
        lines = source.read_text().splitlines()
        hits = [i + 1 for i, line in enumerate(lines) if line.strip() == expected['assertion']]
        if len(hits) != 1 or 'AssertionError' not in output:
            raise AssertionError('Missing designated Node assertion: ' + label)
        matching = [line for line in diagnostics if re.search(r'test_search_core\.cjs:' + str(hits[0]) + r':\d+', line)]
    else:
        matching = [line for line in diagnostics if expected in line]
    if not matching:
        rendered_expected = json.dumps(expected, ensure_ascii=False) if isinstance(expected, dict) else expected
        raise AssertionError('Wrong mutation diagnostic: ' + label + '; expected ' + rendered_expected + '\n' + output[-2000:])
    return (expected['assertion'] if isinstance(expected, dict) else matching[0]).replace(str(ROOT), '<repository>')


def commands(mode):
    if mode == 'release-reproducibility':
        return [[sys.executable, '-B', 'scripts/test_build_reproducibility.py', '--retain-workspace']]
    if mode == 'release-mutations':
        return [[sys.executable, '-B', 'scripts/' + name + '.py', '--retain-workspace']
                for name in ('test_validator_mutations', 'test_reference_lookup_mutations', 'test_official_updates_lookup_mutations')]
    if mode == 'release-online':
        return [[sys.executable, '-B', 'scripts/' + name + '.py']
                for name in ('audit_official_update_sources', 'audit_disaster_official_gateway')]
    if mode == 'build':
        if REPORT == FOLLOWUP:
            return [[sys.executable, '-B', 'scripts/build_all.py']]
        return [[sys.executable, '-B', 'scripts/build_all.py']]
    if mode == 'validation':
        return [[sys.executable, f'scripts/{s}.py'] for s in PYTHON_SCRIPTS] + [
            [sys.executable, 'scripts/validate_forms_source_review.py', '--write-design-manifest'],
            [sys.executable, 'scripts/design_integrity.py', 'verify', str((REPORT / 'allowed-forms-design-manifest.json').relative_to(ROOT))],
            ['node', 'scripts/test_search_core.cjs'], ['node', 'scripts/test_task_search_semantics.cjs'],
            ['node', 'scripts/test_official_updates_lookup.cjs'],
            ['node', 'scripts/benchmark_search_core.cjs'], ['node', 'scripts/benchmark_official_updates_lookup.cjs'],
            ['git', 'diff', '--check']]
    if mode == 'mutation':
        if REPORT == FOLLOWUP:
            return [[sys.executable, '-B', '-c', 'import sys;from pathlib import Path;sys.path.insert(0,"scripts");import test_forms_source_review_mutations as m;m.REPORT=Path("reports/forms-review/reading-faq-fix");m.main()'], [sys.executable, 'scripts/audit_forms_source.py', 'test-followup-mutations']]
        return [[sys.executable, f'scripts/{s}.py'] for s in ['test_validator_mutations', 'test_reference_lookup_mutations', 'test_official_updates_lookup_mutations', 'test_forms_source_review_mutations']]
    if mode == 'reproducibility':
        if REPORT == FOLLOWUP:
            return [[sys.executable, '-B', 'scripts/test_build_reproducibility.py', '--retain-workspace']]
        return [[sys.executable, 'scripts/test_build_reproducibility.py']]
    if REPORT == FOLLOWUP:
        import uuid
        return [['node', 'node_modules/@playwright/test/cli.js', 'test', '--trace', 'off', '--output', 'tmp/reading-faq-browser-' + uuid.uuid4().hex]]
    npm_cli = os.environ.get('FORM_REVIEW_NPM_CLI')
    if npm_cli:
        return [['node', npm_cli, 'ci'], ['node', npm_cli, 'exec', '--', 'playwright', 'install', 'chromium'], ['node', npm_cli, 'exec', '--', 'playwright', 'test']]
    return [['npm','ci'], ['npx','playwright','install','chromium'], ['npx','playwright','test']]


def main():
    global REPORT
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['build','validation','mutation','reproducibility','browser','release-reproducibility','release-mutations','release-online']); args=parser.parse_args()
    if args.mode.startswith('release-'):
        REPORT = ROOT / 'reports/forms-review/release-gates' / (args.mode + '-' + uuid.uuid4().hex)
        REPORT.mkdir(parents=True, exist_ok=False)
        import hashlib
        inputs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for folder in ('source', 'data', 'curation', 'assets', 'site')
                  for p in (ROOT / folder).rglob('*') if p.is_file()}
        (REPORT / 'input-checksums.json').write_text(json.dumps(inputs, indent=2) + '\n')
    records=[]
    logs=REPORT/'logs'; logs.mkdir(parents=True,exist_ok=True)
    for index, command in enumerate(commands(args.mode), 1):
        label=' '.join(['python' if c == sys.executable else c for c in command])
        if command[:2] == ['node', os.environ.get('FORM_REVIEW_NPM_CLI')]:
            label = 'npm ' + ' '.join(command[2:])
        print(label,flush=True)
        completed=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=1800,env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1', 'GIT_OPTIONAL_LOCKS':'0'})
        output=completed.stdout+completed.stderr
        # Public evidence logs keep diagnostics, never machine-private paths.
        output=output.replace(str(ROOT), '<repository>')
        output=re.sub('/' + r'Users/[^\s\"\']+', '<local-runtime-path>', output)
        output=re.sub(r'/(?:private/)?var/folders/[^\s\"\']+', '<temporary-fixture>', output)
        file=logs/f'{args.mode}-{index:02d}.txt'; file.write_text(output)
        records.append({'command':label,'status':'PASS' if completed.returncode==0 else 'FAIL','exitCode':completed.returncode,'log':str(file.relative_to(ROOT))})
        print(records[-1]['status']+' '+output[-800:].strip(),flush=True)
        (REPORT/f'{args.mode}-results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        if completed.returncode:
            break
    if args.mode.startswith('release-'):
        changed = [name for name, digest in inputs.items()
                   if not (ROOT / name).is_file() or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
        if changed: raise SystemExit('Release Gate changed protected input: ' + ', '.join(changed))
    if any(r['status']!='PASS' for r in records):raise SystemExit(1)
    print(f'{args.mode.upper()} PASS: {len(records)}/{len(records)} commands',flush=True)


if __name__ == '__main__':main()
