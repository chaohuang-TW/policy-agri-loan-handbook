#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic FAQ source audit and question-level lookup model.

This module only reads the existing ``pages.json`` text layer and the four
FAQ ranges declared by ``faq.json``.  It never invents wording or infers a
semantic answer boundary.  A question is promoted only when a stable numbered
marker and an explicit ``答`` marker are both present before the next numbered
question marker.  Source-only records remain available for audit reporting.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from display_text import normalize_display_text, non_whitespace_characters

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"

NUMERAL_VALUES = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "十一": 11,
    "十二": 12,
    "十三": 13,
    "十四": 14,
    "十五": 15,
    "十六": 16,
    "十七": 17,
    "十八": 18,
    "十九": 19,
    "二十": 20,
    "二十一": 21,
    "二十二": 22,
    "二十三": 23,
    "二十四": 24,
}
MARKER_RE = re.compile(r"(?P<boundary>^|[）)])\s*(?P<label>[一二三四五六七八九十]+)\s*[、．.]", re.MULTILINE)
ANSWER_RE = re.compile(r"答\s*[:：]?")
QUESTION_PUNCTUATION = "？?﹖"
SECTION_BREAK_PHRASES = (
    "專案農貸諮詢專線",
    "相關書表配合訂定修正",
)


def load_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pages = __import__("json").loads((DATA / "pages.json").read_text(encoding="utf-8"))
    groups = __import__("json").loads((DATA / "faq.json").read_text(encoding="utf-8"))
    return pages, groups, [group for group in groups]


def _page_by_pdf(pages: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(page["pdfPage"]): page for page in pages}


def _units(group: dict[str, Any], pages_by_pdf: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for pdf_page in range(int(group["pdfPageStart"]), int(group["pdfPageEnd"]) + 1):
        page = pages_by_pdf[pdf_page]
        for paragraph_index, paragraph in enumerate(normalize_display_text(page.get("rawText", ""))):
            units.append({
                "pdfPage": pdf_page,
                "printedPage": page.get("printedPage"),
                "paragraphIndex": paragraph_index,
                "text": paragraph,
            })
    return units


def _markers(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for unit_index, unit in enumerate(units):
        for match in MARKER_RE.finditer(unit["text"]):
            label = match.group("label")
            if label not in NUMERAL_VALUES:
                continue
            markers.append({
                "unitIndex": unit_index,
                "offset": match.start("label"),
                "markerEnd": match.end(),
                "label": label,
                "number": NUMERAL_VALUES[label],
                "text": unit["text"][match.start("label"):],
                "pdfPage": unit["pdfPage"],
            })
    return markers


def _slice_units(units: list[dict[str, Any]], start: int, end: int | None) -> str:
    selected = units[start:end] if end is not None else units[start:]
    return "\n".join(unit["text"] for unit in selected).strip()


def _candidate_status(segment: str) -> tuple[bool, re.Match[str] | None]:
    answer = ANSWER_RE.search(segment)
    if answer:
        return True, answer
    return any(char in segment for char in QUESTION_PUNCTUATION), None


def _is_scope_break(marker: dict[str, Any]) -> bool:
    return any(phrase in marker["text"] for phrase in SECTION_BREAK_PHRASES)


def _trim_heading_suffix(text: str) -> str:
    # Headings such as ``（貸款用途)`` sit immediately before the next numbered
    # question in the extracted text.  They are not part of the preceding
    # answer and are removed only at this deterministic boundary.
    return re.sub(r"\s*[（(][^）)]{1,48}[）)]\s*$", "", text.strip())


def _source_pages(units: list[dict[str, Any]], start: int, end: int | None) -> list[int]:
    selected = units[start:end] if end is not None else units[start:]
    return sorted({int(unit["pdfPage"]) for unit in selected})


def audit_group(group: dict[str, Any], pages_by_pdf: dict[int, dict[str, Any]]) -> dict[str, Any]:
    units = _units(group, pages_by_pdf)
    markers = _markers(units)
    accepted: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []

    # First classify numbered markers by looking only until the next numbered
    # marker.  Table rows (一、二、...) do not contain a question punctuation or
    # an explicit answer marker and therefore cannot become FAQ records.
    for index, marker in enumerate(markers):
        if _is_scope_break(marker):
            # These are document headings (consultation line / form revision
            # notes), not FAQ questions.  Ignore punctuation that may appear
            # much later in the following table.
            continue
        next_marker = markers[index + 1] if index + 1 < len(markers) else None
        end_unit = next_marker["unitIndex"] if next_marker else None
        segment = units[marker["unitIndex"]]["text"][marker["offset"]:]
        if end_unit is not None:
            segment += "\n" + _slice_units(units, marker["unitIndex"] + 1, end_unit)
        else:
            segment += "\n" + _slice_units(units, marker["unitIndex"] + 1, None)
        is_candidate, answer = _candidate_status(segment)
        if not is_candidate:
            continue
        marker["candidate"] = True
        marker["answerInLocalSegment"] = bool(answer)
        marker["segment"] = segment
        accepted.append(marker)

    for accepted_index, marker in enumerate(accepted):
        next_accepted = accepted[accepted_index + 1] if accepted_index + 1 < len(accepted) else None
        # A non-question heading is a deterministic end boundary for the last
        # question in each of the first three FAQ ranges.
        break_marker = next((candidate for candidate in markers if candidate["unitIndex"] >= marker["unitIndex"] and _is_scope_break(candidate)), None)
        boundary_candidates = [candidate for candidate in (next_accepted, break_marker) if candidate and candidate["unitIndex"] > marker["unitIndex"]]
        boundary = min(boundary_candidates, key=lambda candidate: (candidate["unitIndex"], candidate["offset"])) if boundary_candidates else None

        start_unit = marker["unitIndex"]
        end_unit = boundary["unitIndex"] if boundary else None
        segment = units[start_unit]["text"][marker["offset"]:]
        if end_unit is not None:
            segment += "\n" + _slice_units(units, start_unit + 1, end_unit)
        else:
            segment += "\n" + _slice_units(units, start_unit + 1, None)
        answer = ANSWER_RE.search(segment)
        question_part = segment[:answer.start()] if answer else segment
        question_part = question_part.strip()
        question_part = re.sub(r"^[一二三四五六七八九十]+\s*[、．.]\s*", "", question_part, count=1)
        answer_text = None
        range_status = "start-only"
        verification_status = "source-indexed-start-only"
        if answer:
            answer_text = _trim_heading_suffix(segment[answer.end():])
            if answer_text:
                range_status = "exact"
                verification_status = "source-indexed"
            else:
                answer_text = None
        source_pages = _source_pages(units, start_unit, end_unit)
        start_page = int(marker["pdfPage"])
        end_page = source_pages[-1] if source_pages else start_page
        page_by_pdf = pages_by_pdf[start_page]
        record = {
            "id": f"{group['id']}-q{marker['number']:02d}",
            "faqGroupId": group["id"],
            "questionLabel": marker["label"],
            "questionNumber": marker["number"],
            "question": question_part,
            "answerText": answer_text,
            "printedPageStart": page_by_pdf.get("printedPage"),
            "printedPageEnd": pages_by_pdf[end_page].get("printedPage"),
            "pdfPageStart": start_page,
            "pdfPageEnd": end_page,
            "sourcePages": source_pages,
            "originalUrl": f"../downloads/policy-agri-loan-handbook-114.pdf#page={start_page}",
            "evidenceUrl": f"versions/114/pages/page-{start_page:03d}.html",
            "verificationStatus": verification_status,
            "rangeStatus": range_status,
            "indexBasis": "strict-numbered-question-and-answer-marker",
        }
        if answer_text and non_whitespace_characters(answer_text) not in non_whitespace_characters("\n".join(unit["text"] for unit in units)):
            record["verificationStatus"] = "ambiguous"
            record["rangeStatus"] = "ambiguous"
            record["answerText"] = None
            ambiguous.append({"id": record["id"], "reason": "answer text is not traceable in source range"})
        if record["verificationStatus"] == "ambiguous":
            ambiguous.append({"id": record["id"], "reason": "answer boundary could not be verified"})
        accepted[accepted_index] = {**marker, "record": record}

    records = [marker["record"] for marker in accepted if "record" in marker]
    # Keep numbering gaps visible to the audit instead of silently pretending
    # that a missing number was not present in the source.
    labels = [record["questionNumber"] for record in records]
    return {
        "id": group["id"],
        "title": group["title"],
        "sourcePages": list(range(int(group["pdfPageStart"]), int(group["pdfPageEnd"]) + 1)),
        "printedPages": list(range(int(group["printedPageStart"]), int(group["printedPageEnd"]) + 1)),
        "questionMarkers": [
            {"label": marker["label"], "number": marker["number"], "pdfPage": marker["pdfPage"], "candidate": bool(marker.get("candidate")), "scopeBreak": _is_scope_break(marker)}
            for marker in markers
        ],
        "records": records,
        "ambiguousCases": ambiguous,
        "questionCount": len(records),
        "deterministicQuestionCount": sum(record["verificationStatus"] == "source-indexed" for record in records),
        "pageLevelFallbackCount": sum(record["verificationStatus"] != "source-indexed" for record in records),
        "questionNumbers": labels,
        "missingQuestionNumbers": [number for number in range(1, max(labels, default=0) + 1) if number not in labels],
        "falsePositiveRisk": "numbered table rows and numbered non-question headings are excluded unless an explicit question or answer marker is present",
    }


def build_audit() -> dict[str, Any]:
    pages, groups, _ = load_inputs()
    pages_by_pdf = _page_by_pdf(pages)
    audited = [audit_group(group, pages_by_pdf) for group in groups]
    records = [record for group in audited for record in group["records"]]
    return {
        "scope": "data/114/faq.json ranges read from data/114/pages.json rawText",
        "groups": audited,
        "records": records,
        "summary": {
            "groupCount": len(audited),
            "sourcePageCount": sum(len(group["sourcePages"]) for group in audited),
            "questionLevelRecords": sum(group["deterministicQuestionCount"] for group in audited),
            "pageLevelFallbackRecords": sum(group["pageLevelFallbackCount"] for group in audited),
            "ambiguousCases": sum(len(group["ambiguousCases"]) for group in audited),
            "duplicateIds": len(records) - len({record["id"] for record in records}),
            "sourceBoundaryErrors": sum(
                1 for record in records
                if not (record["pdfPageStart"] <= record["pdfPageEnd"] and record["pdfPageStart"] >= 1 and record["pdfPageEnd"] <= 359)
            ),
        },
    }


def faq_items() -> list[dict[str, Any]]:
    return build_audit()["records"]
