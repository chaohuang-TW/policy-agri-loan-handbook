#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main():
    css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
    errors = []
    for token in ("color-scheme: light;", "--page-bg:", "--surface-mint:", "--surface-sky:", "--primary-700:", "--space-8:", "@media print", "prefers-reduced-motion"):
        if token not in css: errors.append("missing " + token)
    for forbidden in ("color-scheme: light dark", "@media (prefers-color-scheme: dark)", "0 14px 32px"):
        if forbidden in css: errors.append("forbidden " + forbidden)
    if errors:
        print("VISUAL THEME VALIDATION FAILED\n" + "\n".join("- " + x for x in errors)); return 1
    print("VISUAL THEME VALIDATION PASSED"); return 0
if __name__ == "__main__": raise SystemExit(main())
