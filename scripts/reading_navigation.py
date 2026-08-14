"""Deterministic reading-navigation mappings derived from the existing source pages.

This module deliberately uses only exact, source-visible markers from pages.json.
It contains no runtime fuzzy matching, semantic inference, or generated ordering.
"""
from __future__ import annotations

from dataclasses import dataclass

from display_text import normalize_display_text


@dataclass(frozen=True)
class TaskDefinition:
    key: str
    label: str
    markers: tuple[str, ...]


TASK_DEFINITIONS: tuple[TaskDefinition, ...] = (
    TaskDefinition("eligibility", "申請資格", ("貸款對象", "申貸資格", "申請資格")),
    TaskDefinition("purpose", "貸款用途", ("貸款用途", "資金用途")),
    TaskDefinition("amount", "貸款額度", ("貸款額度", "最高貸款額度")),
    TaskDefinition("term", "貸款期限／寬緩期", ("貸款期限", "貸款期間", "寬緩期", "寬限期")),
    TaskDefinition("interest", "利率", ("貸款利率", "利率依", "利率如下")),
    TaskDefinition("documents", "應備文件", ("應檢具", "應檢附")),
    TaskDefinition("post-loan-management", "貸放後管理", ("貸放後", "貸後", "用途查驗", "經營狀況查驗")),
)

TASK_BY_KEY = {task.key: task for task in TASK_DEFINITIONS}


def _compact(value: str) -> str:
    return "".join(value.split())


def page_role(page: dict) -> str:
    """Classify a source page using explicit leading source labels only."""
    raw = page.get("rawText", "")
    compact = _compact(raw)
    if compact.startswith(("函令摘要", "調整農業天然災害低利貸款利率", "有關")):
        return "interpretation"
    if compact.startswith(("申請書", "審查表", "政策性農業專案貸款查驗報告表", "受災證明書", "附件")):
        return "form"
    return "rule"


def task_anchor_id(task_key: str) -> str:
    return f"task-{task_key}"


def loan_source_pages(loan: dict, pages: list[dict]) -> list[dict]:
    return [
        page for page in pages
        if page.get("printedPage") is not None
        and loan["sourceStartPage"] <= page["printedPage"] <= loan["sourceEndPage"]
    ]


def task_mappings(loan: dict, pages: list[dict]) -> list[dict]:
    """Return at most one exact source paragraph mapping for each available task."""
    candidates = [page for page in loan_source_pages(loan, pages) if page_role(page) == "rule"]
    mappings: list[dict] = []
    for task in TASK_DEFINITIONS:
        found = None
        for page in candidates:
            for paragraph_index, paragraph in enumerate(normalize_display_text(page.get("rawText", ""))):
                compact = _compact(paragraph)
                marker = next((candidate for candidate in task.markers if _compact(candidate) in compact), None)
                if marker:
                    found = {
                        "taskKey": task.key,
                        "label": task.label,
                        "marker": marker,
                        "anchor": task_anchor_id(task.key),
                        "pdfPage": page["pdfPage"],
                        "printedPage": page.get("printedPage"),
                        "paragraphIndex": paragraph_index,
                    }
                    break
            if found:
                break
        if found:
            mappings.append(found)
    return mappings


def mappings_by_page(loan: dict, pages: list[dict]) -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = {}
    for mapping in task_mappings(loan, pages):
        result.setdefault(mapping["pdfPage"], []).append(mapping)
    return result


def deep_link_for_page(loan: dict, page: dict, pages: list[dict]) -> str | None:
    """Return a page fragment only when that source page has one task mapping.

    A page-level result remains the safe fallback whenever a page contains more
    than one navigable task or no deterministic task mapping.
    """
    mappings = mappings_by_page(loan, pages).get(page["pdfPage"], [])
    if len(mappings) != 1:
        return None
    return mappings[0]["anchor"]


def section_anchor_ids(slug: str) -> dict[str, str]:
    return {
        "overview": "section-overview",
        "search": f"section-search-{slug}",
        "content": f"section-content-{slug}",
        "original": "section-original",
        "source": "source-pages",
    }
