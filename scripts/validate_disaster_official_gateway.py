#!/usr/bin/env python3
"""Validate that disaster notices use the single AFNA official gateway."""
from __future__ import annotations
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.afna.gov.tw/list.php?theme=natural_disaster&subtheme="

def main():
    site = ROOT / "site"; gateway = site / "updates/disasters/index.html"; errors = []
    if not gateway.is_file(): errors.append("gateway page missing")
    parsed = urlparse(URL)
    if parsed.scheme != "https" or parsed.hostname != "www.afna.gov.tw" or parse_qs(parsed.query, keep_blank_values=True).get("theme") != ["natural_disaster"]: errors.append("gateway URL invalid")
    text = gateway.read_text(encoding="utf-8") if gateway.is_file() else ""
    required = [URL, 'target="_blank"', 'rel="noopener noreferrer"', "本站不另行複製或追蹤個別公告"]
    if any(value not in text for value in required): errors.append("gateway CTA missing or unsafe")
    forbidden = ("data-disaster-index", "data-disaster-filters", "data-disaster-year", "data-disaster-search", "disaster-announcement", "天然災害低利貸款公告 3筆")
    if any(value in text for value in forbidden): errors.append("gateway contains local announcement data")
    if (ROOT / "data/current/disaster-loan-announcements.json").exists() or (site / "assets/data/disaster-loan-announcements.json").exists(): errors.append("local disaster JSON exists")
    for path in (site / "index.html", site / "loans/natural-disaster-low-interest-loan/index.html", site / "versions/114/sections/natural-disaster-rules/index.html"):
        if "updates/disasters/" not in path.read_text(encoding="utf-8"): errors.append(f"missing gateway link: {path.relative_to(site)}")
    all_html = "\n".join(path.read_text(encoding="utf-8") for path in site.rglob("*.html"))
    if any(value in all_html for value in forbidden): errors.append("generated HTML has disaster announcement attributes")
    if errors:
        print("DISASTER OFFICIAL GATEWAY VALIDATION FAILED"); print(*("- " + e for e in errors), sep="\n"); return 1
    print("DISASTER OFFICIAL GATEWAY VALIDATION PASSED")

if __name__ == "__main__": raise SystemExit(main() or 0)
