"""Single-source scope-group derivation from the version's loan index."""
from __future__ import annotations

def loan_map(loans: list[dict]) -> dict[str, str]:
    return {loan["title"]: loan["id"] for loan in loans}

def loan_id_for_text(value: str, loans: list[dict]) -> str | None:
    text = str(value or "")
    matches = [loan for loan in loans if loan["title"] in text]
    return max(matches, key=lambda loan: len(loan["title"]))["id"] if matches else None

def scope_group_for_page(page: dict, loans: list[dict]) -> str | None:
    return f"loan:{loan_id_for_text(page.get('title'), loans)}" if loan_id_for_text(page.get('title'), loans) else None

def scope_group_for_item(item: dict, loans: list[dict], kind: str) -> str | None:
    if kind == "函釋":
        loan_id = loan_map(loans).get(item.get("loanProgram"))
    else:
        loan_id = loan_id_for_text(item.get("title"), loans)
    return f"loan:{loan_id}" if loan_id else None
