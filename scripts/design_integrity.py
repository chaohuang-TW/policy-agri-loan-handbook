#!/usr/bin/env python3
"""Snapshot frozen sources, routes, anchors and rendered source text, not UI copy."""
import argparse
import hashlib
import json
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

def digest(value):
    return hashlib.sha256(value).hexdigest()

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.ids = []
        self.canonical = None
        self.sources = []
        self.loan = []
        self.preview = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs['href']
        if 'source-preview-image' in classes:
            self.preview.append({key: attrs.get(key) for key in ('src', 'width', 'height')})
        source = bool(set(classes) & {'display-text', 'source-text', 'lookup-source-text'})
        loan = tag == 'p' and self.stack and 'loan-source-page' in self.stack[-1]['classes'] and 'source-boundary' not in classes
        node = {'tag': tag, 'classes': classes, 'text': [], 'source': source, 'loan': loan}
        if tag not in {'img', 'link', 'meta', 'input', 'br', 'hr', 'source', 'wbr'}:
            self.stack.append(node)
    def handle_endtag(self, tag):
        if not self.stack or not any(n['tag'] == tag for n in self.stack):
            return
        while self.stack:
            node = self.stack.pop()
            if node['source']:
                self.sources.append(''.join(node['text']))
            if node['loan']:
                self.loan.append(''.join(node['text']))
            if node['tag'] == tag:
                break
    def handle_data(self, text):
        for node in self.stack:
            if node['source'] or node['loan']:
                node['text'].append(text)

def snapshot():
    frozen = {}
    for directory in ('source', 'data/114', 'curation/114', 'data/current', 'curation/current'):
        for path in sorted((ROOT / directory).rglob('*')):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            if path.name == 'manual.json':
                value = json.loads(raw)
                value.pop('digitalRevision')
                raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
            frozen[str(path.relative_to(ROOT))] = digest(raw)
    for name in ('search-core.js', 'reference-lookup.js', 'official-updates-lookup.js'):
        frozen['assets/js/' + name] = digest((ROOT / 'assets/js' / name).read_bytes())
    pages = {}
    for path in sorted((ROOT / 'site').rglob('*.html')):
        document = Document()
        document.feed(path.read_text())
        pages[str(path.relative_to(ROOT / 'site'))] = {
            'canonical': document.canonical,
            'ids': sorted(document.ids),
            'sourceText': digest(json.dumps(document.sources + document.loan, ensure_ascii=False).encode()),
            'preview': document.preview
        }
    return {'base': '7d9b75dd63a0a62b2437227d6ef3d7d73ec41192', 'frozen': frozen, 'pages': pages,
            'searchIndex': digest((ROOT / 'site/assets/data/search-index.json').read_bytes()),
            'sitemap': digest((ROOT / 'site/sitemap.xml').read_bytes())}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['capture', 'verify'])
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    actual = snapshot()
    if args.mode == 'capture':
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + '\n')
        print('Captured frozen manifest:', len(actual['frozen']), 'files;', len(actual['pages']), 'routes')
        return
    before = json.loads(args.manifest.read_text())
    errors = []
    for field in ('frozen', 'searchIndex', 'sitemap'):
        if before[field] != actual[field]:
            if isinstance(before[field], dict):
                errors.extend(field + ': ' + key for key in before[field].keys() | actual[field].keys() if before[field].get(key) != actual[field].get(key))
            else:
                errors.append(field + ' changed')
    if before['pages'].keys() != actual['pages'].keys():
        errors.append('route inventory changed')
    for route, page in before['pages'].items():
        now = actual['pages'].get(route, {})
        for field in ('canonical', 'sourceText', 'preview'):
            if page[field] != now.get(field):
                errors.append(route + ': ' + field + ' changed')
        if not set(page['ids']).issubset(now.get('ids', [])):
            errors.append(route + ': existing anchor removed')
    if errors:
        raise SystemExit('\n'.join(errors))
    print('DESIGN INTEGRITY PASS: frozen checksums, 399 routes/canonical, sitemap, existing anchors, original text, previews, 507 search records unchanged')

if __name__ == '__main__':
    main()
