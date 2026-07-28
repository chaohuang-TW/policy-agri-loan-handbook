#!/usr/bin/env python3
"""Manually verify official update sources online; intentionally not run in CI."""
from __future__ import annotations

import html
import io
import json
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "law.afna.gov.tw", "afna.gov.tw", "www.afna.gov.tw",
    "moa.gov.tw", "www.moa.gov.tw", "wm.moa.gov.tw",
    "agribank.com.tw", "www.agribank.com.tw",
}


def normalized(value: str) -> str:
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE).casefold()


def source_text(body: bytes, content_type: str) -> str:
    if "application/pdf" in content_type or body.startswith(b"%PDF"):
        reader = PdfReader(io.BytesIO(body))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    decoded = body.decode("utf-8", errors="replace")
    return html.unescape(re.sub(r"<[^>]+>", " ", decoded))


def title_candidates(title: str) -> list[str]:
    candidates = [title]
    core = re.sub(r"^附件\s*\d+\s*[、,，]?\s*", "", title)
    core = re.sub(r"-{1,2}\s*\d+\s*版$", "", core)
    if core != title:
        candidates.append(core)
    return candidates


def main() -> int:
    updates = json.loads((ROOT / "data/current/official-updates.json").read_text(encoding="utf-8"))
    failures = []
    http_success = 0
    redirects = 0
    title_matches = 0
    document_matches = 0
    non_allowlisted = 0
    context = ssl.create_default_context()
    for item in updates:
        request = urllib.request.Request(item["sourceUrl"], headers={"User-Agent": "policy-agri-loan-handbook-source-audit/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=25, context=context) as response:
                final = response.geturl()
                host = urlparse(final).hostname
                body = response.read()
                if response.status >= 400:
                    failures.append(f"{item['id']}: status={response.status} final={final}")
                    continue
                http_success += 1
                if final != item["sourceUrl"]:
                    redirects += 1
                if host not in ALLOWED:
                    non_allowlisted += 1
                    failures.append(f"{item['id']}: non-allowlisted final={final}")
                    continue

                corpus = normalized(source_text(body, response.headers.get_content_type()))
                title_match = any(normalized(candidate) in corpus for candidate in title_candidates(item["officialTitle"]))
                document_match = bool(item["documentNumber"]) and normalized(item["documentNumber"]) in corpus
                if title_match:
                    title_matches += 1
                    match = "title"
                elif document_match:
                    document_matches += 1
                    match = "document-number"
                else:
                    failures.append(f"{item['id']}: officialTitle/documentNumber not found at {final}")
                    continue
                print(f"OK {item['id']} {response.status} match={match} {final}")
        except (urllib.error.URLError, TimeoutError) as error:
            failures.append(f"{item['id']}: {error}")
        except Exception as error:
            failures.append(f"{item['id']}: source parse failed: {error}")
    print(
        "SUMMARY "
        f"urls={len(updates)} httpSuccess={http_success} redirects={redirects} "
        f"titleMatches={title_matches} documentNumberMatches={document_matches} "
        f"nonAllowlisted={non_allowlisted} failures={len(failures)}"
    )
    if failures:
        print("OFFICIAL SOURCE ONLINE AUDIT FAILED")
        for failure in failures:
            print("- " + failure)
        return 1
    print(f"OFFICIAL SOURCE ONLINE AUDIT PASSED: {len(updates)}/{len(updates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
