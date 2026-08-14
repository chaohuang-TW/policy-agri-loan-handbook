#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the static Project Pages site using only relative internal paths."""

from __future__ import annotations

import html
import json
import posixpath
import re
import shutil
from pathlib import Path, PurePosixPath

from content_model import (
    interpretation_group_slug,
    interpretation_programs,
    loan_for_form,
    loan_for_printed_page,
    section_by_id,
    section_scopes,
    sections,
    toc_interpretation_group_slug,
)
from display_text import normalize_display_text
from reading_navigation import (
    deep_link_for_page,
    mappings_by_page,
    section_anchor_ids,
    task_anchor_id,
    task_mappings,
)
from faq_lookup import faq_items

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"
SITE = ROOT / "site"
TEMPLATES = {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "templates").glob("*.html")}
PAGES = json.loads((DATA / "pages.json").read_text(encoding="utf-8"))
TOC = json.loads((DATA / "toc.json").read_text(encoding="utf-8"))
QUICK_INDEX = json.loads((DATA / "quick-index.json").read_text(encoding="utf-8"))
LOANS = json.loads((DATA / "loan-programs.json").read_text(encoding="utf-8"))
INTERPRETATIONS = json.loads((DATA / "interpretations.json").read_text(encoding="utf-8"))
FAQ = json.loads((DATA / "faq.json").read_text(encoding="utf-8"))
FAQ_ITEMS = json.loads((DATA / "faq-items.json").read_text(encoding="utf-8"))
FORMS = json.loads((DATA / "forms.json").read_text(encoding="utf-8"))
APPENDICES = json.loads((DATA / "appendices.json").read_text(encoding="utf-8"))
RULES = json.loads((DATA / "page-rendering-rules.json").read_text(encoding="utf-8"))
RENDERING = {p["pdfPage"]: p for p in RULES["pages"]}
MANUAL = json.loads((DATA / "manual.json").read_text(encoding="utf-8"))
SHORTCUTS = json.loads((DATA / "navigation-shortcuts.json").read_text(encoding="utf-8"))
CURRENT = ROOT / "data" / "current"
COVERAGE = json.loads((CURRENT / "coverage.json").read_text(encoding="utf-8"))
OFFICIAL_UPDATES = json.loads((CURRENT / "official-updates.json").read_text(encoding="utf-8"))
DECISIONS = json.loads((ROOT / "curation/current/official-update-decisions.json").read_text(encoding="utf-8"))
LOAN_TITLES = {item["id"]: item["title"] for item in LOANS}
def interpretation_target(loan_program: str) -> str:
    return f"interpretations/index.html#group-{interpretation_group_slug(loan_program)}"
MANIFEST = {p["pdfPage"]: p for p in json.loads((ROOT / "assets/page-previews/114/manifest.json").read_text(encoding="utf-8"))}
ORIGIN = "https://chaohuang-tw.github.io/policy-agri-loan-handbook/"
PDF_NAME = "policy-agri-loan-handbook-114.pdf"
DESCRIPTION = "忠實呈現114年度政策性農業專案貸款業務手冊，提供全文搜尋、完整目錄、貸款索引、函釋、常見問答、附件及原始PDF頁面查閱。"


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def fill(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def rel_root(relative: str) -> str:
    directory = str(PurePosixPath(relative).parent)
    result = posixpath.relpath(".", directory)
    return "./" if result == "." else result.rstrip("/") + "/"


def rel(relative: str, target: str) -> str:
    directory = str(PurePosixPath(relative).parent)
    return posixpath.relpath(target, directory)


def canonical(relative: str) -> str:
    return ORIGIN + (relative[:-10] if relative.endswith("index.html") else relative)


def write(relative: str, title: str, main: str, description: str = DESCRIPTION, body_attrs: str = "") -> None:
    path = SITE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    document = fill(TEMPLATES["base"], TITLE=e(title), DESCRIPTION=e(description),
                    CANONICAL=e(canonical(relative)), ROOT=e(rel_root(relative)), MAIN=main, BODY_ATTRS=body_attrs,
                    DIGITAL_REVISION=e(MANUAL["digitalRevision"]))
    path.write_text("\n".join(line.rstrip() for line in document.splitlines()) + "\n", encoding="utf-8")


def wrap(template: str, **values: str) -> str:
    return fill(TEMPLATES[template], **values)


def breadcrumb(relative: str, pairs: list[tuple[str, str | None]], current: str) -> str:
    result = []
    for label, target in pairs:
        result.append(f'<a href="{e(rel(relative, target))}">{e(label)}</a>' if target else f"<span>{e(label)}</span>")
    result.append(f'<span aria-current="page">{e(current)}</span>')
    return '<nav class="breadcrumb" aria-label="麵包屑">' + '<span aria-hidden="true">›</span>'.join(result) + "</nav>"


def search_box(
    input_id: str = "site-search",
    label: str = "你想查什麼？",
    default_scope: str = "all",
) -> str:
    return f'''<div class="search-panel" data-search data-search-default-scope="{e(default_scope)}"><form role="search" novalidate><label for="{e(input_id)}">{e(label)}</label><div class="search-row"><input id="{e(input_id)}" name="q" type="search" maxlength="256" autocomplete="off" placeholder="搜尋貸款名稱、資格、用途、額度、期限、函釋或常見問題……"><button type="submit">搜尋</button></div></form><p class="search-scope-note">目前全文搜尋範圍：114年度手冊底本。手冊出版後資料請查看「官方更新」。</p><div class="search-scope-options" hidden aria-label="搜尋範圍"><span>搜尋範圍</span><button type="button" data-scope="all" aria-pressed="true">全手冊</button><button type="button" data-scope="chapter" aria-pressed="false">本章</button></div><details class="search-filter-disclosure"><summary>篩選結果</summary><div class="search-filters" aria-label="搜尋類型"></div></details><p class="search-status" aria-live="polite" tabindex="-1" hidden></p><div class="search-results"></div><button class="search-more" type="button" hidden>顯示更多結果</button></div>'''


TYPE_LABELS = {
    "regulation": "法規", "administrative-rule": "行政規則",
    "interpretation": "函示", "announcement": "公告", "faq": "FAQ",
    "form": "表單／附件", "disaster-measure": "災害措施", "other-official": "其他官方資料",
}


def roc_date(value: str | None) -> str:
    if not value:
        return ""
    year, month, day = (int(part) for part in value.split("-"))
    return f"{year - 1911}/{month:02d}/{day:02d}"


def roc_time(value: str) -> str:
    return f'<time datetime="{e(value)}">{e(roc_date(value))}</time>'


def application_period(item: dict) -> str:
    start, end = item["applicationPeriod"]["start"], item["applicationPeriod"]["end"]
    if start and end:
        return f'<p class="update-period">官方資料所載受理期間：{roc_time(start)}－{roc_time(end)}</p>'
    if end:
        return f'<p class="update-period">官方資料所載受理期限：至 {roc_time(end)}</p>'
    if start:
        return f'<p class="update-period">官方資料所載受理期間：自 {roc_time(start)} 起</p>'
    return ""


DISASTER_GATEWAY_URL = "https://www.afna.gov.tw/list.php?theme=natural_disaster&subtheme="


def update_relation(item: dict) -> str:
    loans = [LOAN_TITLES[loan_id] for loan_id in item["relatedLoanIds"]]
    if loans:
        return "、".join(loans)
    if "natural-disaster-rules" in item["relatedSectionIds"]:
        return "天然災害"
    if any(section in item["relatedSectionIds"] for section in ("policy-loan-regulations", "agricultural-development-fund-rules")):
        return "共同規定"
    return "政策農貸"


def update_rows(relative: str, items: list[dict], compact: bool = False) -> str:
    rows = []
    ordered = sorted(
        items,
        key=lambda record: (-int(event_sort_date(record).replace("-", "")), record["id"]),
    )
    for item in ordered:
        metadata = []
        for field, label in (("publishedDate", "發布"), ("effectiveDate", "生效"), ("versionDate", "版本")):
            if item.get(field):
                metadata.append(f"{label} {roc_date(item[field])}")
        metadata.extend([TYPE_LABELS[item["sourceType"]], item["officialAgency"]])
        if not compact and item.get("documentNumber"):
            metadata.append(item["documentNumber"])
        period_text = "" if compact else application_period(item)
        rows.append(
            f'<li class="official-update-item" data-update-type="{e(item["sourceType"])}" '
            f'data-update-year="{e(event_sort_date(item)[:4])}" data-update-relations="{e(" ".join(item["relatedLoanIds"] + item["relatedSectionIds"]))}">'
            f'<p class="update-meta">{"｜".join(e(value) for value in metadata)}</p>'
            f'<h3>{e(item["officialTitle"])}</h3>'
            f'{"" if compact else f"<p>關聯：{e(update_relation(item))}</p>"}{period_text}'
            f'<a href="{e(item["sourceUrl"])}" target="_blank" rel="noopener noreferrer">查看官方來源<span class="visually-hidden">（另開新視窗）</span></a></li>'
        )
    return '<ol class="official-update-list">' + "".join(rows) + "</ol>"


def official_update_lookup_records(items: list[dict]) -> list[dict]:
    section_titles = {section["id"]: section["title"] for section in sections()}
    return [
        {
            "id": item["id"],
            "officialTitle": item["officialTitle"],
            "sourceType": item["sourceType"],
            "sourceTypeLabel": TYPE_LABELS[item["sourceType"]],
            "officialAgency": item["officialAgency"],
            "documentNumber": item.get("documentNumber") or "",
            "publishedDate": item.get("publishedDate"),
            "effectiveDate": item.get("effectiveDate"),
            "versionDate": item.get("versionDate"),
            "lookupYear": event_sort_date(item)[:4],
            "sourceUrl": item["sourceUrl"],
            "relatedLoanIds": list(item["relatedLoanIds"]),
            "relatedLoanTitles": [LOAN_TITLES[loan_id] for loan_id in item["relatedLoanIds"]],
            "relatedSectionIds": list(item["relatedSectionIds"]),
            "relatedSectionTitles": [section_titles[section_id] for section_id in item["relatedSectionIds"] if section_id in section_titles],
            "relationEvidence": item.get("relationEvidence", ""),
        }
        for item in items
    ]


def official_update_lookup_cards(relative: str, items: list[dict]) -> str:
    rows = []
    section_titles = {section["id"]: section["title"] for section in sections()}
    for item in items:
        metadata = []
        for field, label in (("publishedDate", "發布"), ("effectiveDate", "生效"), ("versionDate", "版本")):
            if item.get(field):
                metadata.append(f"{label} {roc_date(item[field])}")
        metadata.extend([TYPE_LABELS[item["sourceType"]], item["officialAgency"]])
        if item.get("documentNumber"):
            metadata.append(item["documentNumber"])
        relation_values = " ".join(item["relatedLoanIds"] + item["relatedSectionIds"])
        loans = [
            f'<a href="{e(rel(relative, f"loans/{loan_id}/index.html"))}">查看114年手冊原貸款：{e(LOAN_TITLES[loan_id])}</a>'
            for loan_id in item["relatedLoanIds"]
        ]
        relation_text = "、".join(LOAN_TITLES[loan_id] for loan_id in item["relatedLoanIds"])
        if not relation_text:
            relation_text = "、".join(section_titles.get(section_id, "") for section_id in item["relatedSectionIds"] if section_titles.get(section_id))
        relation_html = f'<p class="update-relations">涉及貸款／章節：{e(relation_text or "未指定")}</p>'
        handbook_links = f'<p class="update-handbook-links">{"｜".join(loans)}</p>' if loans else ""
        rows.append(
            f'<li class="official-update-item official-update-result" data-official-update-result data-official-update-id="{e(item["id"])}" '
            f'data-update-type="{e(item["sourceType"])}" data-update-year="{e(event_sort_date(item)[:4])}" '
            f'data-update-relations="{e(relation_values)}">'
            '<span class="official-update-badge">官方更新</span>'
            f'<p class="update-meta">{"｜".join(e(value) for value in metadata)}</p>'
            f'<h3>{e(item["officialTitle"])}</h3>{relation_html}{application_period(item)}{handbook_links}'
            f'<p class="official-update-actions"><a class="button-link" href="{e(item["sourceUrl"])}" target="_blank" rel="noopener noreferrer">查看官方來源<span class="visually-hidden">（另開新視窗）</span></a></p>'
            '</li>'
        )
    return '<ol class="official-update-list">' + "".join(rows) + "</ol>"


def event_sort_date(item: dict) -> str:
    return item.get("publishedDate") or item.get("effectiveDate") or item.get("versionDate")


def current_update_block(relative: str, items: list[dict], empty_context: str = "") -> str:
    if items:
        body = f'<p>{len(items)} 筆明確對應紀錄。</p>{update_rows(relative, items)}'
    else:
        body = f'<p>在目前已檢核的官方更新索引中，尚未建立與{e(empty_context)}明確對應的手冊出版後更新。</p>'
    return f'<section class="loan-current-updates"><h2>手冊出版後官方更新</h2>{body}<p><a href="{e(rel(relative, "updates/index.html"))}">查看全部官方更新</a></p></section>'


def paragraphize(text: str) -> str:
    blocks = normalize_display_text(text)
    return "".join(f"<p>{e(block)}</p>" for block in blocks)


def page_card(page: dict, relative: str, heading_level: int = 2) -> str:
    number = page["pdfPage"]
    printed = page["printedPage"] if page["printedPage"] is not None else "目錄"
    pdf = rel(relative, f"downloads/{PDF_NAME}") + f"#page={number}"
    mode = page["renderMode"]
    preview = ""
    if mode in {"preview", "hybrid"}:
        item = MANIFEST[number]
        image_url = rel(relative, f"assets/page-previews/114/{item['file']}")
        preview = f'''<figure class="source-preview"><a class="source-preview-link" href="{e(image_url)}" aria-label="放大查看原始PDF第{number}頁預覽"><img class="source-preview-image" src="{e(image_url)}" alt="114年度政策性農業專案貸款業務手冊原始PDF第{number}頁預覽" width="{item['width']}" height="{item['height']}" loading="lazy" decoding="async"></a><figcaption>本頁保留原始PDF版面；正式內容請以原始PDF為準。</figcaption></figure><nav class="preview-actions" aria-label="PDF第{number}頁預覽操作"><a href="{e(image_url)}">放大查看原頁預覽</a><a href="{e(pdf)}">開啟原始PDF此頁</a><a href="{e(rel(relative, 'downloads/' + PDF_NAME))}">開啟／下載完整PDF</a></nav>'''
    if page["hasTextLayer"]:
        if mode == "text":
            body = f'<div class="display-text">{paragraphize(page["rawText"])}</div><details class="raw-text-details"><summary>查看PDF原始文字層</summary><div class="layout-note" role="note">文字取自PDF既有文字層，僅移除固定行寬造成的假換行顯示；正式內容以原始PDF為準。</div><pre class="source-text source-text-raw">{e(page["rawText"])}</pre></details>'
        else:
            body = f'{preview}<details class="extracted-text-details"><summary>展開查看PDF原始文字層</summary><div class="layout-note" role="note">複雜表格欄列可能因文字層順序失真，請搭配原頁預覽查閱。</div><pre class="source-text source-text-secondary">{e(page["rawText"])}</pre></details>'
    else:
        body = preview + '<p class="layout-note">本頁以原始PDF頁面預覽呈現，未使用OCR重建內容。</p>'
    actions = "" if mode in {"preview", "hybrid"} else f'<div class="page-actions"><a href="{e(pdf)}">開啟原始PDF此頁</a></div>'
    return f'''<section class="page-card" id="pdf-page-{number}"><h{heading_level}>手冊頁：{e(printed)} <small>PDF頁：{number}／359</small></h{heading_level}>{actions}{body}</section>'''


def page_range(start: int, end: int) -> list[dict]:
    return [page for page in PAGES if start + 2 <= page["pdfPage"] <= end + 2]


def shortcut_buttons(context: str, target: str) -> str:
    items = [
        item for item in SHORTCUTS
        if item["kind"].startswith("task:") and context in item["kind"].split(":", 1)[1].split(",")
    ]
    scope = "all" if context == "home" else "context"
    return '<div class="task-shortcuts">' + "".join(
        f'<button type="button" data-query="{e(item["query"])}" data-search-target="#{e(target)}" data-search-scope="{scope}">{e(item["label"])}</button>'
        for item in sorted(items, key=lambda item: item["order"])
    ) + "</div>"


def source_page_details(relative: str, pages: list[dict]) -> str:
    links = []
    for page in pages:
        target = f'versions/114/pages/page-{page["pdfPage"]:03d}.html'
        links.append(f'<li><a href="{e(rel(relative, target))}">手冊頁 {e(page["printedPage"])}</a></li>')
    return f'<details id="source-pages" class="source-page-list"><summary>來源與原始頁面（{len(pages)}頁）</summary><ol>{"".join(links)}</ol></details>'


def loan_task_navigation(mappings: list[dict]) -> str:
    if not mappings:
        return '<section id="loan-task-navigation" class="loan-task-navigation"><h2>本頁快速導覽</h2><p class="layout-note">本頁沒有可由既有來源結構明確定位的任務區塊。</p></section>'
    items = "".join(
        f'<li><a data-reading-task="{e(mapping["taskKey"])}" href="#{e(mapping["anchor"])}">{e(mapping["label"])}</a></li>'
        for mapping in mappings
    )
    return f'<nav id="loan-task-navigation" class="loan-task-navigation" aria-labelledby="loan-task-navigation-title"><h2 id="loan-task-navigation-title">本頁快速導覽</h2><ul>{items}</ul></nav>'


def continuous_source(relative: str, pages: list[dict], task_page_mappings: dict[int, list[dict]]) -> str:
    blocks = []
    for page_index, page in enumerate(pages):
        page_mappings = task_page_mappings.get(page["pdfPage"], [])
        anchors_by_paragraph: dict[int, list[dict]] = {}
        for mapping in page_mappings:
            anchors_by_paragraph.setdefault(mapping["paragraphIndex"], []).append(mapping)
        paragraphs = normalize_display_text(page.get("rawText", ""))
        body_blocks = []
        for paragraph_index, paragraph in enumerate(paragraphs):
            headings = "".join(
                f'<h3 id="{e(mapping["anchor"])}" class="reading-anchor-heading" data-reading-anchor="{e(mapping["taskKey"])}" tabindex="-1">{e(mapping["label"])}</h3>'
                for mapping in anchors_by_paragraph.get(paragraph_index, [])
            )
            body_blocks.append(headings + f"<p>{e(paragraph)}</p>")
        evidence_target = f'versions/114/pages/page-{page["pdfPage"]:03d}.html'
        sequence_links = []
        if page_index > 0:
            previous = pages[page_index - 1]
            previous_anchor = f"source-page-{previous['pdfPage']}"
            sequence_links.append(f'<a data-reading-prev href="#{e(previous_anchor)}">上一項：手冊頁 {e(previous["printedPage"])}</a>')
        if page_index + 1 < len(pages):
            following = pages[page_index + 1]
            following_anchor = f"source-page-{following['pdfPage']}"
            sequence_links.append(f'<a data-reading-next href="#{e(following_anchor)}">下一項：手冊頁 {e(following["printedPage"])}</a>')
        sequence = f'<nav class="reading-sequence" aria-label="貸款原文連續閱讀">{"".join(sequence_links)}</nav>' if sequence_links else ""
        blocks.append(
            f'<div class="loan-source-page" id="source-page-{page["pdfPage"]}"><p class="source-boundary">手冊頁 {e(page["printedPage"])}｜PDF頁 {page["pdfPage"]}｜<a class="evidence-link" href="{e(rel(relative, evidence_target))}">查看原始頁面</a></p>{"".join(body_blocks)}{sequence}</div>'
        )
    return '<section class="loan-source-text" aria-labelledby="loan-source-title"><h2 id="loan-source-title">貸款原文</h2>' + "".join(blocks) + "</section>"


def section_toc(items: list[tuple[str, str]]) -> str:
    links = "".join(f'<li><a href="{e(target)}">{e(label)}</a></li>' for label, target in items)
    return f'<details class="page-toc" open><summary>本頁內容</summary><nav aria-label="本頁內容"><ol>{links}</ol></nav></details>'


def loan_cards(relative: str, items: list[dict]) -> str:
    cards = []
    for loan in items:
        interpretation_count = sum(item["loanProgram"] == loan["title"] for item in INTERPRETATIONS)
        form_count = sum(bool((owner := loan_for_form(item)) and owner["id"] == loan["id"]) for item in FORMS)
        url = rel(relative, f'loans/{loan["id"]}/index.html')
        cards.append(
            f'<li><article><h3>{e(loan["title"])}</h3><p>{e(loan["category"])}</p>'
            f'<p>手冊頁 {loan["sourceStartPage"]}-{loan["sourceEndPage"]}｜函釋 {interpretation_count}｜書表 {form_count}</p>'
            f'<a href="{e(url)}">查看貸款</a></article></li>'
        )
    return '<ol class="loan-grid">' + "".join(cards) + "</ol>"


def loan_nav(relative: str) -> str:
    items = "".join(f'<li><a href="{e(rel(relative, "loans/" + item["id"] + "/index.html"))}">{e(item["title"])}</a></li>' for item in LOANS)
    return f"<details open><summary>23項貸款索引</summary><ol>{items}</ol></details>"


def build_home() -> None:
    relative = "index.html"
    popular_items = sorted((item for item in SHORTCUTS if item["kind"] == "popular"), key=lambda item: item["order"])
    popular = "".join(f'<button type="button" data-keyword="{e(item["query"])}" data-search-target="#home-search" data-search-scope="all">{e(item["label"])}</button>' for item in popular_items)
    counts = MANUAL["counts"]
    revision = MANUAL["digitalRevision"]
    hero = f'<h1>政策性農業專案貸款業務手冊</h1><p class="subtitle">快速找到貸款規定、函釋與書表，並可回到原始手冊核對。</p><p class="version-inline">114年度 Beta</p>{search_box("home-search")}<div class="popular" aria-label="常用查詢"><span>常用查詢</span>{popular}</div>'
    review_info = COVERAGE["officialUpdateReview"]
    recent = sorted(
        OFFICIAL_UPDATES,
        key=lambda item: (-int(event_sort_date(item).replace("-", "")), item["id"]),
    )[:3]
    status = (
        f'<div class="current-status-head"><div><p class="eyebrow">資料狀態</p><h2 id="current-status-title">114手冊底本與後續官方資料分開呈現</h2></div>'
        f'<a class="button-link secondary" href="updates/index.html">查看手冊出版後官方更新</a></div>'
        f'<dl class="current-status-meta"><div><dt>底本</dt><dd>{e(COVERAGE["baseline"]["title"])}</dd></div>'
        f'<div><dt>官方來源檢核</dt><dd>{"指定官方來源已檢核至" + roc_date(review_info["verifiedThrough"]) if review_info["coverageStatus"] == "complete" else "官方來源盤點進行中"}（<a href="updates/index.html#coverage">查看檢核範圍</a>）</dd></div>'
        f'<div><dt>制度與業務更新</dt><dd>{len(OFFICIAL_UPDATES)} 筆</dd></div><div><dt>天然災害低利貸款最新公告</dt><dd><a href="updates/disasters/index.html">農業金融署官方專區</a></dd></div></dl>'
        f'<p class="scope-caveat">114年度手冊原文保持不變；後續官方規定另列於更新索引。實際適用仍以主管機關及貸款經辦機構最新正式資料為準。</p>'
        f'<div class="recent-updates"><h3>最近官方更新</h3>{update_rows(relative, recent, compact=True)}<p><a href="updates/index.html">查看全部制度與業務更新</a></p><p>天然災害低利貸款的地區、品項及申請期間，請查閱農業金融署最新公告。</p><p><a href="updates/disasters/index.html">前往官方公告入口</a></p></div>'
    )
    tasks = '<h2 id="task-title">我想查……</h2><p>選擇常見任務後直接搜尋原始資料。</p>' + shortcut_buttons("home", "home-search")
    links = [
        ("找貸款", "依名稱與類別瀏覽23項貸款", "loans/index.html", "依需求找資料", "quick-index/index.html"),
        ("函釋與 FAQ", "查文號、函釋與常見問題", "interpretations/index.html", "前往 FAQ", "faq/index.html"),
        ("找書表", "查申請書、審核表與附件", "forms/index.html", "依需求找資料", "quick-index/index.html"),
        ("原書完整目錄", "依原始手冊順序瀏覽", "versions/114/index.html", "開啟完整PDF", f"downloads/{PDF_NAME}"),
    ]
    quick = '<div class="entry-grid primary-entries">' + "".join(
        f'<article class="entry"><h3><a href="{e(url)}">{e(label)}</a></h3><p>{e(description)}</p><a class="entry-secondary" href="{e(secondary_url)}">{e(secondary_label)}</a></article>'
        for label, description, url, secondary_label, secondary_url in links
    ) + "</div>"
    review = f'''<h2 id="review-title">內容覆核狀態</h2><p>原始閱讀頁：{MANUAL["pdfPages"]}頁；原書完整目錄：{counts["tocEntries"]}項；函釋來源索引：{counts["interpretationsSourceIndexed"]}筆；函釋候選庫：{counts["interpretationCandidateInventoryTotal"]}筆；函釋未決候選：{counts["interpretationCandidatesPending"]}筆；書表來源索引：{counts["formsSourceIndexed"]}筆；書表未分類候選：{counts["formCandidatesPending"]}筆。</p><p>書表逐頁人工覆核：尚未完成；函釋結束頁確認：尚未完成；全文逐頁人工校讀：尚未完成。</p><p class="layout-note">來源索引依嚴格頁面與欄位規則建立；候選庫總量僅為偵測庫存，不等同待覆核數。全文逐頁校讀、函釋涵蓋範圍及書表內容仍需人工確認。</p>'''
    version = f'''<h2 id="version-title">版本資訊</h2><dl><div><dt>資料版本</dt><dd>114年度 Beta</dd></div><div><dt>PDF實體頁數</dt><dd>359頁</dd></div><div><dt>數位版本</dt><dd>{e(revision)}</dd></div><div><dt>來源文件</dt><dd>114年度政策性農業專案貸款業務手冊</dd></div></dl><div class="version-actions"><a class="button-link" href="versions/114/index.html">開啟原書完整目錄</a><a class="button-link secondary" href="downloads/{PDF_NAME}">開啟／下載原始PDF</a><a href="versions/index.html">查看版本紀錄與更新說明</a></div>'''
    write(relative, "政策性農業專案貸款業務手冊｜114年度數位閱讀版", wrap("home", HERO=hero, STATUS=status, TASKS=tasks, QUICK=quick, REVIEW=review, VERSION=version))


def build_version_index() -> None:
    relative = "versions/114/index.html"
    loan_ids = {loan["id"] for loan in LOANS}
    section_targets = {"policy-loan-regulations": "versions/114/sections/policy-loan-regulations/index.html", "fund-operating-rules": "versions/114/sections/agricultural-development-fund-rules/index.html", "loan-program-rules": "versions/114/sections/loan-programs/index.html"}
    rows = []
    for item in TOC["items"]:
        target = None
        if item["id"] in loan_ids:
            target = f'loans/{item["id"]}/index.html'
        elif item["id"] in section_targets:
            target = section_targets[item["id"]]
        elif item["kind"] == "interpretation":
            target = "interpretations/index.html#group-" + toc_interpretation_group_slug(item["id"].removesuffix("-interpretations"))
        elif item["id"] == "natural-disaster-rules":
            target = "versions/114/sections/natural-disaster-rules/index.html"
        elif item["kind"] == "faq":
            target = "faq/index.html#item-" + item["id"]
        elif item["kind"] in {"appendix", "attachment"}:
            target = "forms/index.html#item-" + item["id"]
        label = f'<a href="{e(rel(relative, target))}">{e(item["title"])}</a>' if target else f'<strong>{e(item["title"])}</strong>'
        page = f'<span>手冊頁 {item["printedPage"]}</span>' if item["printedPage"] is not None else ""
        rows.append(f'<li class="toc-level-{item["level"]}">{label}{page}</li>')
    content = breadcrumb(relative, [("首頁", "index.html")], "原書完整目錄") + f'<h1>114年度原書完整目錄</h1><p class="source-meta">本目錄忠實對應114年度手冊，不因後續官方更新重新編排。逐項轉錄原始PDF第1–2頁，共 {len(TOC["items"])} 個目錄項目。</p><p><a href="{e(rel(relative, "quick-index/index.html"))}">需要較精簡的入口？前往依需求找資料</a>｜<a href="{e(rel(relative, "updates/index.html"))}">查看手冊出版後官方更新</a></p>' + search_box("toc-search") + '<ol class="index-rows faithful-toc">' + "".join(rows) + "</ol>"
    write(relative, "114年度完整目錄｜政策性農業專案貸款業務手冊", wrap("manual-index", CONTENT=content))


def build_quick_index() -> None:
    relative = "quick-index/index.html"
    groups = []
    loan_ids = {loan["id"] for loan in LOANS}
    for group in QUICK_INDEX["groups"]:
        rows = []
        for item in group["items"]:
            if item["id"] in loan_ids:
                target = f'loans/{item["id"]}/index.html'
            elif item["id"] in {"interpretations", "faq", "forms"}:
                target = f'{item["id"]}/index.html'
            elif item["id"] == "appendices":
                target = "forms/index.html"
            else:
                section_id = {"fund-operating-rules": "agricultural-development-fund-rules"}.get(item["id"], item["id"])
                target = f'versions/114/sections/{section_id}/index.html'
            rows.append(f'<li><a href="{e(rel(relative, target))}">{e(item["title"])}</a><span>手冊頁 {item["printedPage"]}</span></li>')
        groups.append(f'<section class="toc-group"><h2>{e(group["title"])}</h2><ol class="index-rows">{"".join(rows)}</ol></section>')
    content = breadcrumb(relative, [("首頁", "index.html")], "依需求找資料") + '<h1>依需求找資料</h1><p class="source-meta">依常用閱讀需求整理，不取代原書目錄。</p><p><a href="../versions/114/index.html">查看原書完整目錄</a></p><div class="toc-layout">' + "".join(groups) + '</div>'
    write(relative, "依需求找資料｜政策性農業專案貸款業務手冊", wrap("manual-index", CONTENT=content))


def build_sections() -> None:
    for section in sections():
        slug, title = section["id"], section["title"]
        start, end = section["printedPageStart"], section["printedPageEnd"]
        relative = f"versions/114/sections/{slug}/index.html"
        pages = page_range(start, end)
        search_id = f"section-search-input-{slug}"
        anchors = section_anchor_ids(slug)
        context = "common" if slug == "agricultural-development-fund-rules" else "disaster" if slug == "natural-disaster-rules" else ""
        search = f'<section id="{e(anchors["search"])}" class="hub-search"><h2>在本章查規定</h2>{search_box(search_id, default_scope="context")}{shortcut_buttons(context, search_id) if context else ""}</section>'
        section_updates = [item for item in OFFICIAL_UPDATES if slug in item["relatedSectionIds"]]
        if slug in {"policy-loan-regulations", "agricultural-development-fund-rules", "natural-disaster-rules"}:
            current = current_update_block(relative, section_updates, "本章")
            if slug == "natural-disaster-rules":
                current += f'<section class="loan-current-updates"><h2>最新天然災害低利貸款公告</h2><p class="layout-note">最新地區、品項及申請期間請以農業金融署公告為準。</p><p><a href="{e(rel(relative, "updates/disasters/index.html"))}">查詢最新官方公告</a></p></section>'
        elif slug == "loan-programs":
            current = f'<section class="loan-current-updates"><h2>手冊出版後官方更新</h2><p><a href="{e(rel(relative, "updates/index.html"))}">查看手冊出版後各貸款官方更新</a></p></section>'
        elif slug == "amendment-faq":
            current = f'<section class="loan-current-updates"><h2>資料範圍</h2><p>114年度手冊收錄FAQ如下；手冊出版後之官方問答另見官方更新。</p><p><a href="{e(rel(relative, "updates/index.html?type=faq"))}">查看手冊出版後官方問答</a></p></section>'
        elif slug == "attachments":
            current = f'<section class="loan-current-updates"><h2>手冊出版後官方表單／附件</h2><p><a href="{e(rel(relative, "updates/index.html?type=form"))}">查看官方更新中的表單／附件</a></p></section>'
        else:
            current = ""
        first_page = f'versions/114/pages/page-{pages[0]["pdfPage"]:03d}.html'
        original = f'<section class="hub-original"><h2>原文</h2><p>依本章原始頁次閱讀，條文內容以正式資料為準。</p><a class="button-link secondary" href="{e(rel(relative, first_page))}">從本章第一頁開始</a></section>'
        primary = ""
        if slug == "loan-programs":
            items = [loan for loan in LOANS if 94 <= loan["sourceStartPage"] <= 269]
            primary = f'<section id="{e(anchors["content"])}" class="hub-primary"><h2>19項貸款</h2>' + loan_cards(relative, items) + "</section>"
        elif slug == "amendment-faq":
            primary = f'<section id="{e(anchors["content"])}" class="hub-primary faq-hub"><h2>4組 FAQ</h2>' + index_items(relative, FAQ, "FAQ") + "</section>"
        elif slug == "attachments":
            items = [item for item in APPENDICES if item["id"].startswith("attachment-")]
            primary = f'<section id="{e(anchors["content"])}" class="hub-primary attachment-hub"><h2>附件資料</h2>' + index_items(relative, items, "附件") + "</section>"
        elif slug == "bank-operating-rules-appendices":
            items = [item for item in APPENDICES if item["id"].startswith("appendix-")][:2]
            primary = f'<section id="{e(anchors["content"])}" class="hub-primary appendix-hub"><h2>作業規範附錄</h2>' + index_items(relative, items, "附錄") + "</section>"
        elif slug == "natural-disaster-rules":
            disaster = next(loan for loan in LOANS if loan["id"] == "natural-disaster-low-interest-loan")
            forms = [item for item in FORMS if loan_for_form(item) and loan_for_form(item)["id"] == disaster["id"]]
            primary = f'<section id="{e(anchors["content"])}" class="hub-primary"><h2>相關資料</h2><div class="hub-links"><a href="{e(rel(relative, disaster["detailUrl"]))}">農業天然災害低利貸款</a><a href="{e(rel(relative, interpretation_target(disaster["title"])))}">相關函釋</a><a href="{e(rel(relative, "forms/index.html"))}">相關書表（{len(forms)}）</a></div></section>'
        elif slug == "agricultural-development-fund-rules":
            common_target = interpretation_target(interpretation_programs()[0])
            primary = f'<section id="{e(anchors["content"])}" class="hub-primary"><h2>相關函釋與書表</h2><div class="hub-links"><a href="{e(rel(relative, common_target))}">共同規定函釋</a><a href="{e(rel(relative, "forms/index.html"))}">共通書表</a></div></section>'
        else:
            primary = f'<section id="{e(anchors["content"])}" class="hub-primary"><h2>下一步</h2><div class="hub-links"><a href="{e(rel(relative, "loans/index.html"))}">找貸款</a><a href="{e(rel(relative, "interpretations/index.html"))}">查函釋</a><a href="{e(rel(relative, "forms/index.html"))}">找書表</a></div></section>'
        original = original.replace('<section class="hub-original">', f'<section id="{e(anchors["original"])}" class="hub-original">', 1)
        content = f'<h1 id="{e(anchors["overview"])}">{e(title)}</h1><p class="source-meta">手冊印刷頁 {start}-{end}｜資料版本：114年度</p>{current}{search}{primary}{original}{source_page_details(relative, pages)}'
        nav = section_toc([
            ("本章概覽", f"#{anchors['overview']}"),
            ("本章搜尋", f"#{anchors['search']}"),
            ("章節內容", f"#{anchors['content']}"),
            ("原文頁面", f"#{anchors['source']}"),
        ])
        main = wrap("reading-page", BREADCRUMB=breadcrumb(relative, [("首頁", "index.html"), ("原書完整目錄", "versions/114/index.html")], title), NAV=nav, CONTENT=content)
        scopes = ",".join(section_scopes(slug))
        write(relative, f"{title}｜114年度", main, body_attrs=f'data-search-scopes="{e(scopes)}"')


def build_physical_pages() -> None:
    for page in PAGES:
        number = page["pdfPage"]
        relative = f"versions/114/pages/page-{number:03d}.html"
        previous = f'<a href="page-{number-1:03d}.html">上一頁</a>' if number > 1 else "<span>已是第一頁</span>"
        following = f'<a href="page-{number+1:03d}.html">下一頁</a>' if number < 359 else "<span>已是最後一頁</span>"
        nav = f'<details open><summary>逐頁閱讀</summary><p>{previous}　{following}</p><p><a href="../index.html">回原書完整目錄</a></p></details>'
        printed = page["printedPage"] if page["printedPage"] is not None else "目錄"
        owner = loan_for_printed_page(page.get("printedPage"))
        section = section_by_id(page["chapterId"])
        context_links = []
        if owner:
            context_links.append(f'<a href="{e(rel(relative, owner["detailUrl"]))}">回到{e(owner["title"])}</a>')
        if section:
            section_target = f'versions/114/sections/{section["id"]}/index.html'
            context_links.append(f'<a href="{e(rel(relative, section_target))}">回到本章</a>')
        tools = '<div class="page-actions"><button type="button" data-print-page>列印本頁</button>' + "".join(context_links) + "</div>"
        content = f'<h1>{e(page["title"])}</h1><p class="source-meta">手冊頁：{e(printed)}｜PDF實體頁：{number}／359｜資料版本：114年度</p>{tools}' + page_card(page, relative)
        main = wrap("reading-page", BREADCRUMB=breadcrumb(relative, [("首頁", "index.html"), ("原書完整目錄", "versions/114/index.html")], f"PDF頁碼 {number}"), NAV=nav, CONTENT=content)
        write(relative, f"PDF頁碼 {number}｜{page['title']}", main, body_attrs=f'data-printable="true" data-print-label="列印本頁" data-search-scope="section:{page["chapterId"]}"')


def build_loans() -> None:
    relative = "loans/index.html"
    policy = [loan for loan in LOANS if loan["category"] == "政策性農業專案貸款"]
    bank = [loan for loan in LOANS if loan["category"] == "全國農業金庫貸款"]
    content = breadcrumb(relative, [("首頁", "index.html")], "找貸款") + '<h1>找貸款</h1><p class="source-meta">依貸款名稱與類別瀏覽23項貸款，查看原文、相關函釋、書表與來源頁面。</p><p class="layout-note">本頁不提供資格判斷或貸款推薦。</p><section id="policy-loans"><h2>20項政策性農業專案貸款</h2>' + loan_cards(relative, policy) + '</section><section id="bank-loans"><h2>3項全國農業金庫貸款</h2>' + loan_cards(relative, bank) + "</section>"
    write(relative, "貸款索引｜政策性農業專案貸款業務手冊", wrap("loan-index", CONTENT=content))
    for loan in LOANS:
        relative = f'loans/{loan["id"]}/index.html'
        pages = page_range(loan["sourceStartPage"], loan["sourceEndPage"])
        search_id = f'loan-search-{loan["id"]}'
        search_section_id = f'loan-search-section-{loan["id"]}'
        mappings = task_mappings(loan, PAGES)
        page_mappings = mappings_by_page(loan, PAGES)
        related_interpretations = [item for item in INTERPRETATIONS if item["loanProgram"] == loan["title"]]
        related_forms = [item for item in FORMS if (owner := loan_for_form(item)) and owner["id"] == loan["id"]]
        related_updates = [item for item in OFFICIAL_UPDATES if loan["id"] in item["relatedLoanIds"]]
        disaster_block = ""
        if loan["id"] == "natural-disaster-low-interest-loan":
            disaster_block = f'<section class="loan-current-updates"><h2>最新地區及品項公告</h2><p class="layout-note">天然災害低利貸款之公告地區、品項及申請期間可能持續更新，本站不另行同步，請以農業金融署正式公告為準。</p><p><a href="{e(rel(relative, "updates/disasters/index.html"))}">前往農業金融署天然災害低利貸款專區</a></p></section>'
        if related_interpretations:
            interpretation_block = f'<p>{len(related_interpretations)}筆來源索引。</p><a href="{e(rel(relative, interpretation_target(loan["title"])))}">查看本貸款相關函釋</a>'
        else:
            interpretation_block = "<p>目前來源索引沒有另列本貸款函釋。</p>"
        forms_block = index_items(relative, related_forms, "書表") if related_forms else "<p>目前來源索引沒有歸屬本貸款的書表。</p>"
        content = (
            f'<h1>{e(loan["title"])}</h1><p class="source-meta">{e(loan["category"])}｜手冊印刷頁 {loan["sourceStartPage"]}-{loan["sourceEndPage"]}</p>'
            f'<p class="layout-note">本頁忠實呈現原文，不提供資格摘要、額度摘要、利率摘要或核貸判斷。</p>'
            f'{current_update_block(relative, related_updates, "本貸款")}{disaster_block}'
            f'{loan_task_navigation(mappings)}'
            f'<section id="{e(search_section_id)}" class="loan-context-search"><h2>在本貸款中搜尋</h2>{search_box(search_id, default_scope="context")}{shortcut_buttons("loan", search_id)}</section>'
            f'{continuous_source(relative, pages, page_mappings)}'
            f'<section class="loan-related"><h2>相關函釋</h2>{interpretation_block}</section>'
            f'<section class="loan-related"><h2>相關書表</h2>{forms_block}</section>'
            f'{source_page_details(relative, pages)}'
        )
        task_link = '<a href="#loan-task-navigation">本頁快速導覽</a>'
        nav = f'<nav class="hub-nav" aria-label="貸款頁導覽">{task_link}<a href="#{e(search_section_id)}">本貸款搜尋</a><a href="#loan-source-title">貸款原文</a><a href="{e(rel(relative, "loans/index.html"))}">回找貸款</a></nav>'
        main = wrap("loan-detail", BREADCRUMB=breadcrumb(relative, [("首頁", "index.html"), ("找貸款", "loans/index.html")], loan["title"]), NAV=nav, CONTENT=content)
        write(relative, f"{loan['title']}｜貸款索引", main, body_attrs=f'data-search-scope="section:{loan["id"]}" data-search-scope-group="loan:{loan["id"]}"')


def index_items(relative: str, items: list[dict], kind: str) -> str:
    blocks = []
    for item in items:
        printed = item.get("printedPage", item.get("printedPageStart"))
        pdf = item.get("pdfPage", item.get("pdfPageStart"))
        extra = ""
        if item.get("documentNumber"):
            extra += f'<span>文號：{e(item["documentNumber"])}</span>'
        if item.get("date"):
            extra += f'<span>日期：{e(item["date"])}</span>'
        if item.get("rangeStatus"):
            extra += f'<span>頁碼範圍：{e(item["rangeStatus"])}（結束頁待人工確認）</span>'
        url = rel(relative, f"downloads/{PDF_NAME}") + f"#page={pdf}"
        blocks.append(f'<li id="item-{e(item["id"])}"><div><strong>{e(item["title"])}</strong><span>{e(kind)}｜手冊頁 {e(printed)}｜PDF頁 {e(pdf)}</span>{extra}</div><a href="{e(url)}">開啟原文</a></li>')
    return '<ol class="index-rows index-detail">' + "".join(blocks) + "</ol>"


def embedded_lookup_data(items: list[dict]) -> str:
    payload = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'<script type="application/json" data-lookup-data>{payload}</script>'


def lookup_actions(relative: str, pdf_page: int, evidence_target: str) -> str:
    pdf = rel(relative, f"downloads/{PDF_NAME}") + f"#page={pdf_page}"
    evidence = rel(relative, evidence_target)
    return f'<p class="lookup-actions"><a class="button-link" href="{e(evidence)}">在手冊中開啟</a><a class="button-link secondary" href="{e(pdf)}">開啟PDF原文</a></p>'


def faq_answer_html(answer_text: str | None) -> str:
    if not answer_text:
        return '<p class="layout-note">本題僅建立來源起始頁索引；答案範圍待人工確認。</p>'
    return '<div class="lookup-source-text">' + "".join(f"<p>{e(line)}</p>" for line in answer_text.splitlines() if line.strip()) + "</div>"


def faq_group_source_list(relative: str) -> str:
    rows = []
    for group in FAQ:
        pdf = rel(relative, f"downloads/{PDF_NAME}") + f"#page={group['pdfPageStart']}"
        evidence = rel(relative, f"versions/114/pages/page-{group['pdfPageStart']:03d}.html")
        rows.append(
            f'<li id="item-{e(group["id"])}"><div><strong>{e(group["title"])}</strong><span>手冊頁 {e(group["printedPageStart"])}–{e(group["printedPageEnd"])}｜PDF頁 {group["pdfPageStart"]}–{group["pdfPageEnd"]}</span></div><a href="{e(evidence)}">開啟來源頁</a><a href="{e(pdf)}">開啟PDF原文</a></li>'
        )
    return '<section class="lookup-source-groups"><h2>四組手冊 FAQ 來源</h2><ol class="index-rows index-detail">' + "".join(rows) + '</ol></section>'


def faq_result_cards(relative: str) -> str:
    cards = []
    group_titles = {group["id"]: group["title"] for group in FAQ}
    for item in FAQ_ITEMS:
        lookup_key = item["id"]
        search_text = " ".join((item["question"], item.get("answerText") or "", group_titles[item["faqGroupId"]]))
        cards.append(
            f'<article id="item-{e(lookup_key)}" class="lookup-result faq-lookup-result" data-lookup-result data-lookup-id="{e(item["id"])}" data-lookup-key="{e(lookup_key)}" data-lookup-group="{e(item["faqGroupId"])}" data-lookup-search="{e(search_text)}">'
            f'<p class="lookup-kicker">{e(group_titles[item["faqGroupId"]])}</p><h3>{e(item["question"])}</h3>'
            f'<p class="lookup-meta">FAQ第{e(item["questionLabel"])}題｜手冊頁 {e(item["printedPageStart"])}–{e(item["printedPageEnd"])}｜PDF頁 {item["pdfPageStart"]}–{item["pdfPageEnd"]}</p>'
            f'<details><summary>查看原文回答</summary>{faq_answer_html(item.get("answerText"))}</details>'
            f'{lookup_actions(relative, item["pdfPageStart"], item["evidenceUrl"])}'
            '</article>'
        )
    return '<div class="lookup-results" data-lookup-results>' + "".join(cards) + '</div>'


def faq_lookup_tool(relative: str) -> str:
    def filter_label(group: dict) -> str:
        if group["id"] == "faq-young-farmer-114-10":
            return "青壯年農民"
        match = re.search(r"\d+年\d+月", group["title"])
        return match.group(0) if match else group["title"]

    groups = ''.join(
        f'<button type="button" data-lookup-group-filter="{e(group["id"])}" aria-pressed="false">{e(filter_label(group))}</button>'
        for group in FAQ
    )
    return (
        '<section class="reference-lookup" data-reference-lookup="faq" aria-labelledby="faq-lookup-title">'
        '<h2 id="faq-lookup-title">FAQ實務查閱</h2>'
        '<p class="layout-note">以下結果來自114年度手冊底本；搜尋只在本頁資料中進行，不包含手冊出版後官方更新。</p>'
        '<form class="lookup-search-form" data-lookup-form role="search" novalidate><label for="faq-lookup-q">搜尋FAQ問題或關鍵字</label><div class="lookup-search-row"><input id="faq-lookup-q" name="q" type="search" maxlength="256" autocomplete="off" placeholder="例如：寬緩期、青壯年農民、補正登記證"><button type="submit">搜尋</button><button type="reset" class="lookup-clear">清除</button></div></form>'
        f'<fieldset class="lookup-filter-group"><legend>FAQ來源</legend><div class="lookup-filter-options"><button type="button" data-lookup-group-filter="" aria-pressed="true">全部</button>{groups}</div></fieldset>'
        '<p class="lookup-status" data-lookup-status aria-live="polite"></p>'
        f'{embedded_lookup_data(FAQ_ITEMS)}'
        '</section>'
    )


def interpretation_year(item: dict) -> str:
    match = re.search(r"(\d+)年", item.get("date", ""))
    return match.group(1) if match else ""


def interpretation_result_cards(relative: str) -> str:
    groups_data = [(program, interpretation_group_slug(program)) for program in interpretation_programs()]
    by_program = {program: slug for program, slug in groups_data}
    cards_by_slug: dict[str, list[str]] = {slug: [] for _, slug in groups_data}
    records = []
    source_id_occurrences: dict[str, int] = {}
    for item in INTERPRETATIONS:
        slug = by_program.get(item["loanProgram"], interpretation_group_slug(item["loanProgram"]))
        year = interpretation_year(item)
        source_id_occurrences[item["id"]] = source_id_occurrences.get(item["id"], 0) + 1
        occurrence = source_id_occurrences[item["id"]]
        lookup_key = item["id"] if occurrence == 1 else f"{item['id']}-duplicate-{occurrence}"
        dom_id = f"item-{lookup_key}"
        record = {**item, "lookupKey": lookup_key, "programSlug": slug, "year": year, "evidenceUrl": f"versions/114/pages/page-{item['pdfPageStart']:03d}.html"}
        records.append(record)
        range_note = f'頁碼範圍：{e(item["rangeStatus"])}（結束頁待人工確認）' if item.get("rangeStatus") else ""
        search_text = " ".join((item["title"], item.get("sourceHeader", ""), item.get("documentNumber", ""), item.get("canonicalDocumentNumber", ""), item.get("loanProgram", "")))
        cards_by_slug.setdefault(slug, []).append(
            f'<article id="{e(dom_id)}" class="lookup-result interpretation-lookup-result" data-lookup-result data-lookup-id="{e(item["id"])}" data-lookup-key="{e(lookup_key)}" data-lookup-program="{e(slug)}" data-lookup-year="{e(year)}" data-lookup-search="{e(search_text)}">'
            f'<p class="lookup-kicker">函釋｜{e(item["date"])}｜{e(item["loanProgram"])}</p><h3>{e(item["title"])}</h3>'
            f'<p class="lookup-doc-number">文號：{e(item["documentNumber"])}</p><p class="lookup-meta">{e(item["sourceHeader"])}｜手冊頁 {e(item["printedPageStart"])}｜PDF頁 {item["pdfPageStart"]}–{item.get("pdfPageEnd") or item["pdfPageStart"]}｜{range_note}</p>'
            f'{lookup_actions(relative, item["pdfPageStart"], record["evidenceUrl"])}'
            '</article>'
        )
    sections_html = []
    for program, slug in groups_data:
        items = cards_by_slug.get(slug, [])
        sections_html.append(f'<section id="group-{e(slug)}" class="interpretation-group lookup-group"><h2>{e(program)}</h2><p class="source-meta">{len(items)} 筆函釋</p><div class="lookup-group-results">{"".join(items)}</div><p><a href="#main-content">返回函釋頁頂端</a></p></section>')
    return ''.join(sections_html), records


def interpretation_lookup_tool(relative: str, records: list[dict]) -> str:
    programs = {}
    years = set()
    for item in records:
        programs[item["programSlug"]] = item["loanProgram"]
        if item["year"]:
            years.add(item["year"])
    program_options = ''.join(f'<option value="{e(slug)}">{e(title)}</option>' for slug, title in sorted(programs.items(), key=lambda pair: pair[1]))
    year_options = ''.join(f'<option value="{e(year)}">民國{e(year)}年</option>' for year in sorted(years, key=lambda value: int(value), reverse=True))
    return (
        '<section class="reference-lookup" data-reference-lookup="interpretations" aria-labelledby="interpretation-lookup-title">'
        '<h2 id="interpretation-lookup-title">函釋實務查閱</h2>'
        '<p class="layout-note">以下結果來自114年度手冊底本；結束頁仍依現有資料的 <code>start-only</code> 狀態呈現，不自行推算。</p>'
        '<form class="lookup-search-form" data-lookup-form role="search" novalidate><label for="interpretation-lookup-q">搜尋函釋主旨、文號或關鍵字</label><div class="lookup-search-row"><input id="interpretation-lookup-q" name="q" type="search" maxlength="256" autocomplete="off" placeholder="例如：0955080181、借新還舊、支付憑證"><button type="submit">搜尋</button><button type="reset" class="lookup-clear">清除</button></div>'
        '<div class="lookup-select-row"><label>貸款類別<select name="program" data-lookup-program><option value="">全部貸款類別</option>' + program_options + '</select></label><label>年份<select name="year" data-lookup-year><option value="">全部年份</option>' + year_options + '</select></label></div></form>'
        '<p class="lookup-status" data-lookup-status aria-live="polite"></p>'
        f'{embedded_lookup_data(records)}'
        '</section>'
    )


def build_indexes() -> None:
    relative = "interpretations/index.html"
    counts = MANUAL["counts"]
    groups, interpretation_records = interpretation_result_cards(relative)
    groups_data = [(program, interpretation_group_slug(program)) for program in interpretation_programs()]
    quick_links = '<nav class="index-rows" aria-label="依類別快速前往"><h2>依類別快速前往</h2><ul>' + ''.join(f'<li><a href="#group-{slug}">{e(program)}</a></li>' for program, slug in groups_data) + '</ul></nav>'
    content = breadcrumb(relative, [("首頁", "index.html")], "函釋來源索引") + f'<h1>函釋來源索引</h1><p class="source-meta">本頁為114年度手冊所收錄函釋查閱工具；依同頁完整標頭、日期、完整文號與主旨起始建立，共 {counts["interpretationsSourceIndexed"]} 筆。候選庫共 {counts["interpretationCandidateInventoryTotal"]} 筆，其中未決候選 {counts["interpretationCandidatesPending"]} 筆；候選庫總量不等於待覆核數。結束頁尚待人工確認。</p><p><a href="../updates/index.html?type=interpretation">查看手冊出版後官方函示</a></p>' + interpretation_lookup_tool(relative, interpretation_records) + quick_links + groups + '<p><a href="../faq/index.html">前往常見問答</a></p>'
    write(relative, "相關函釋索引｜政策性農業專案貸款業務手冊", wrap("interpretations", CONTENT=content))
    relative = "faq/index.html"
    content = breadcrumb(relative, [("首頁", "index.html")], "常見問答") + '<h1>增修規定常見問答</h1><p class="layout-note">本頁列示114年度手冊內收錄之FAQ；手冊出版後官方發布之問答，請查看「官方更新」。本頁不提供AI摘要。</p><p><a href="../updates/index.html?type=faq">查看手冊出版後官方問答</a></p>' + faq_lookup_tool(relative) + faq_group_source_list(relative) + faq_result_cards(relative)
    write(relative, "增修規定常見問答｜政策性農業專案貸款業務手冊", wrap("faq", CONTENT=content))
    relative = "forms/index.html"
    content = breadcrumb(relative, [("首頁", "index.html")], "書表與附件來源索引") + f'<h1>書表與附件來源索引</h1><p class="source-meta">本頁列示114手冊收錄書表。書表來源索引 {counts["formsSourceIndexed"]} 筆；候選庫 {counts["formCandidateInventoryTotal"]} 筆，其中已納入 {counts["formCandidatesPromoted"]} 筆、排除 {counts["formCandidatesExcluded"]} 筆、真正待人工覆核 {counts["formCandidatesPending"]} 筆。另列 {len(APPENDICES)} 項原手冊附錄／附件。</p><section class="loan-current-updates"><h2>手冊出版後官方表單／附件</h2><p>後續官方表單不改寫114手冊書表。</p><p><a href="../updates/index.html?type=form">查看官方更新中的表單／附件</a></p></section><h2>附錄與附件</h2>' + index_items(relative, APPENDICES, "附錄／附件") + '<h2>書表來源索引</h2>' + index_items(relative, FORMS, "書表")
    write(relative, "附件與書表索引｜政策性農業專案貸款業務手冊", wrap("forms", CONTENT=content))


def build_updates() -> None:
    relative = "updates/index.html"
    review = COVERAGE["officialUpdateReview"]
    lookup_records = official_update_lookup_records(OFFICIAL_UPDATES)
    years = sorted({item["lookupYear"] for item in lookup_records}, reverse=True)
    source_types = sorted({item["sourceType"] for item in lookup_records}, key=lambda value: TYPE_LABELS[value])
    program_ids = {
        loan_id
        for item in lookup_records
        for loan_id in item["relatedLoanIds"]
    }
    loan_options = "".join(
        f'<option value="{e(item["id"])}">{e(item["title"])}</option>'
        for item in LOANS if item["id"] in program_ids
    )
    type_options = "".join(f'<option value="{e(value)}">{e(TYPE_LABELS[value])}</option>' for value in source_types)
    section_ids = sorted({section_id for item in lookup_records for section_id in item["relatedSectionIds"]})
    section_options = "".join(
        f'<option value="{e(section_id)}">{e(next((section["title"] for section in sections() if section["id"] == section_id), section_id))}</option>'
        for section_id in section_ids
    )
    lookup_payload = json.dumps(lookup_records, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    filters = (
        '<form class="update-filters" data-update-filters data-official-updates-lookup data-official-updates-form role="search" novalidate>'
        '<label for="official-updates-q">搜尋文號、標題、內容關鍵詞或貸款名稱</label>'
        '<div class="official-updates-search-row"><input id="official-updates-q" name="q" type="search" maxlength="256" autocomplete="off" placeholder="搜尋文號、標題、內容關鍵詞或貸款名稱"><button type="submit">搜尋</button><button type="reset">清除篩選</button></div>'
        '<div class="official-updates-filter-row">'
        '<label>貸款類別<select name="program"><option value="">全部貸款類別</option>' + loan_options + '</select></label>'
        '<label>更新類型<select name="type"><option value="">全部更新類型</option>' + type_options + '</select></label>'
        '<label>年份<select name="year"><option value="">全部年份</option>' + "".join(f'<option value="{year}">{int(year)-1911}</option>' for year in years) + '</select></label>'
        '<label>關聯（相容篩選）<select name="relation"><option value="">全部關聯</option>' + section_options + loan_options + '</select></label>'
        '</div><p class="update-filter-status"></p><p class="official-update-status" data-official-update-status aria-live="polite"></p></form>'
    )
    content = (
        breadcrumb(relative, [("首頁", "index.html")], "官方更新")
        + '<h1>手冊出版後官方更新</h1><p class="subtitle">官方更新查閱版：114年度手冊原文保持不變；以下僅列手冊出版後已完成來源核對的官方制度／業務更新。</p>'
        + f'<section id="coverage" class="coverage-panel"><h2>資料基準與檢核範圍</h2><dl><div><dt>底本</dt><dd>{e(COVERAGE["baseline"]["title"])}</dd></div><div><dt>PDF頁數</dt><dd>359頁</dd></div><div><dt>Coverage</dt><dd>{"指定官方來源已檢核至" + roc_date(review["verifiedThrough"]) if review["coverageStatus"] == "complete" else "官方來源盤點進行中"}</dd></div><div><dt>制度與業務更新</dt><dd>{len(OFFICIAL_UPDATES)}筆</dd></div></dl><p>{e(review["statement"])}</p><p>本站僅列已完成來源核對之官方制度／業務更新；收錄範圍仍在持續盤點。天然災害個別地區／品項公告另依農業金融署官方專區為準。</p></section><section class="loan-current-updates"><h2>最新天然災害低利貸款公告</h2><p>本站不另行同步個別地區及品項公告，請直接查閱農業金融署官方專區。</p><p><a href="disasters/index.html">查詢農業金融署最新公告</a></p></section>'
        + '<section class="updates-index" data-official-updates-lookup><h2>官方更新查閱</h2><p class="layout-note">查閱結果來自20筆已收錄官方更新，不會混入114年度手冊507筆全文搜尋。</p>' + filters + official_update_lookup_cards(relative, OFFICIAL_UPDATES) + f'<script type="application/json" data-official-updates-data>{lookup_payload}</script></section>'
    )
    write(relative, "手冊出版後官方更新｜政策性農業專案貸款業務手冊", wrap("manual-index", CONTENT=content), body_attrs='data-update-index="true"')


def build_disaster_updates() -> None:
    relative = "updates/disasters/index.html"
    content = breadcrumb(relative, [("首頁", "index.html"), ("官方更新", "updates/index.html")], "天然災害低利貸款最新公告") + f'<h1>天然災害低利貸款最新公告</h1><p class="subtitle">各地區、品項及申請期間可能持續更新，請直接查閱農業金融署官方專區。</p><section class="loan-current-updates"><h2>農業金融署官方公告入口</h2><p>天然災害低利貸款的公告地區、品項及申請期間，會依災害情形持續更新。本站不另行複製或追蹤個別公告，請以農業金融署正式公告為準。</p><p><a class="button-link" href="{DISASTER_GATEWAY_URL}" target="_blank" rel="noopener noreferrer">前往農業金融署天然災害低利貸款專區<span class="visually-hidden">（外部官方網站，另開新視窗）</span></a></p><p class="layout-note">外部官方網站</p></section>'
    write(relative, "天然災害低利貸款最新公告｜政策性農業專案貸款業務手冊", wrap("manual-index", CONTENT=content))


def build_versions() -> None:
    relative = "versions/index.html"
    revision = MANUAL["digitalRevision"]
    content = breadcrumb(relative, [("首頁", "index.html")], "版本紀錄") + f'''<h1>版本紀錄與資料來源</h1><article class="version-record"><div class="version-record-head"><div><h2>114年度</h2><p>數位版本：{e(revision)}</p></div><span class="version-status">Beta</span></div><dl class="version-meta"><div><dt>來源文件</dt><dd>114年度政策性農業專案貸款業務手冊</dd></div><div><dt>PDF實體頁數</dt><dd>359頁</dd></div><div class="version-sha"><dt>SHA-256</dt><dd><code>0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54</code></dd></div></dl><div class="version-actions"><a class="button-link" href="114/index.html">開啟原書完整目錄</a><a class="button-link secondary" href="../downloads/{PDF_NAME}">開啟／下載原始PDF</a></div><div class="version-update"><h3>Beta.2.7.2 天然災害公告官方導引版</h3><p>114手冊原文保持不變；制度與業務更新由本站整理，地方型天然災害公告統一導向農業金融署官方專區。</p><p><a href="../updates/index.html">查看官方更新</a></p></div></article><section class="version-policy"><h2>版本保存原則</h2><p>來源索引是依既定來源規則可定位的資料；候選庫為自動偵測庫存，並不等同待覆核數。新版PDF不得覆蓋舊版；新版本使用新version ID，重新計算頁數、SHA-256、頁碼映射、文字擷取、目錄、呈現規則與搜尋索引。正式內容始終以原始PDF為準。</p></section>'''
    write(relative, "版本紀錄與資料來源｜政策性農業專案貸款業務手冊", wrap("versions", CONTENT=content))


def build_site(output_dir: Path) -> None:
    global SITE
    SITE = Path(output_dir)
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    shutil.copytree(ROOT / "assets/css", SITE / "assets/css", dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets/js", SITE / "assets/js", dirs_exist_ok=True)
    (SITE / "assets/data").mkdir(parents=True, exist_ok=True)
    for data_file in ("search-concepts.json", "search-intents.json", "navigation-shortcuts.json"):
        shutil.copy2(DATA / data_file, SITE / "assets/data" / data_file)
    shutil.copy2(DATA / "faq-items.json", SITE / "assets/data" / "faq-items.json")
    shutil.copy2(CURRENT / "official-updates.json", SITE / "assets/data" / "official-updates.json")
    shutil.copy2(CURRENT / "coverage.json", SITE / "assets/data" / "current-coverage.json")
    shutil.copytree(ROOT / "assets/page-previews", SITE / "assets/page-previews", dirs_exist_ok=True)
    shutil.copy2(ROOT / "assets/favicon.svg", SITE / "assets/favicon.svg")
    (SITE / "downloads").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "source" / PDF_NAME, SITE / "downloads" / PDF_NAME)
    build_home(); build_version_index(); build_quick_index(); build_sections(); build_physical_pages(); build_loans(); build_indexes(); build_updates(); build_disaster_updates(); build_versions()
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    html_files = sorted(SITE.rglob("*.html"))
    sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n" + "".join(f"  <url><loc>{e(canonical(str(p.relative_to(SITE))))}</loc></url>\n" for p in html_files) + "</urlset>\n"
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (SITE / "robots.txt").write_text("User-agent: *\nAllow: /policy-agri-loan-handbook/\nSitemap: " + ORIGIN + "sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(html_files)} HTML pages")


if __name__ == "__main__":
    from build_all import main
    main()
