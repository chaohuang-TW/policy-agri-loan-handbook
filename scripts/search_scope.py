"""Compatibility wrappers around the single content ownership model."""
from __future__ import annotations

from content_model import (
    scope_group_for_form,
    scope_group_for_interpretation,
    scope_group_for_page as model_scope_group_for_page,
)


def scope_group_for_page(page: dict, loans: list[dict]) -> str | None:
    del loans
    return model_scope_group_for_page(page)


def scope_group_for_item(item: dict, loans: list[dict], kind: str) -> str | None:
    del loans
    if kind == "函釋":
        return scope_group_for_interpretation(item)
    if kind == "書表附件":
        return scope_group_for_form(item)
    return None
