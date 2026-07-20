#!/usr/bin/env python3
"""Ensure every generated relative HTML fragment target exists."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'site'
class P(HTMLParser):
 def __init__(self): super().__init__(); self.ids=set(); self.links=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if d.get('id'): self.ids.add(d['id'])
  if t=='a' and d.get('href'): self.links.append(d['href'])
def main():
 errors=[]
 for f in SITE.rglob('*.html'):
  p=P(); p.feed(f.read_text(encoding='utf-8'))
  for href in p.links:
   u=urlsplit(href)
   if u.scheme or u.netloc or href.startswith('#') and not u.fragment: continue
   target=(f.parent/unquote(u.path)).resolve() if u.path else f
   if not target.exists(): errors.append(f'missing target {f.relative_to(SITE)} -> {href}'); continue
   if u.fragment and target.suffix=='.html':
    q=P(); q.feed(target.read_text(encoding='utf-8'))
    if u.fragment not in q.ids: errors.append(f'missing fragment {f.relative_to(SITE)} -> {href}')
 if not (SITE/'versions/114/sections/natural-disaster-rules/index.html').is_file(): errors.append('natural-disaster-rules missing')
 if errors: print('NAVIGATION TARGET VALIDATION FAILED\n'+'\n'.join('- '+x for x in errors)); return 1
 print('NAVIGATION TARGET VALIDATION PASSED')
 return 0
if __name__=='__main__': raise SystemExit(main())
