#!/usr/bin/env python3
"""Online pre-commit audit for formal disaster-announcement records; not CI."""
import json, ssl, urllib.request
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]; ALLOWED={"law.afna.gov.tw","afna.gov.tw","www.afna.gov.tw","moa.gov.tw","www.moa.gov.tw","wm.moa.gov.tw"}
items=json.loads((ROOT/"data/current/disaster-loan-announcements.json").read_text()); failures=[]
for item in items:
 try:
  with urllib.request.urlopen(urllib.request.Request(item["sourceUrl"],headers={"User-Agent":"policy-agri-loan-handbook-source-audit/1.0"}),timeout=25,context=ssl.create_default_context()) as r:
   text=r.read().decode("utf-8",errors="replace"); final=r.geturl()
   if r.status>=400 or urlparse(final).scheme!="https" or urlparse(final).hostname not in ALLOWED: raise ValueError(f"unsafe final URL {final}")
   if item["officialTitle"] not in text and (not item["documentNumber"] or item["documentNumber"] not in text): raise ValueError("title/document number not found")
   print(f"OK {item['id']} {final}")
 except Exception as e: failures.append(f"{item['id']}: {e}")
if failures:
 print("DISASTER SOURCE ONLINE AUDIT FAILED");print(*("- "+x for x in failures),sep="\n");raise SystemExit(1)
print(f"DISASTER SOURCE ONLINE AUDIT PASSED: {len(items)}/{len(items)}")
