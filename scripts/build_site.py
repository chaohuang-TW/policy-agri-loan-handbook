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

from display_text import normalize_display_text

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
FORMS = json.loads((DATA / "forms.json").read_text(encoding="utf-8"))
APPENDICES = json.loads((DATA / "appendices.json").read_text(encoding="utf-8"))
RULES = json.loads((DATA / "page-rendering-rules.json").read_text(encoding="utf-8"))
RENDERING = {p["pdfPage"]: p for p in RULES["pages"]}
MANUAL = json.loads((DATA / "manual.json").read_text(encoding="utf-8"))
INTERPRETATION_GROUPS = {
    "農業發展基金貸款共同規定": "common-rules", "農機貸款": "farm-machinery-loan",
    "輔導農糧業經營貸款": "agri-food-business-loan", "輔導漁業經營貸款": "fishery-business-loan",
    "提升畜禽產業經營貸款": "livestock-poultry-loan", "農民經營及產銷班貸款": "farmer-production-group-loan",
    "農業科技園區進駐業者優惠貸款": "agri-tech-park-loan", "農家綜合貸款": "farm-household-loan",
    "農漁會事業發展貸款": "association-development-loan", "造林貸款": "afforestation-loan",
    "農業節能減碳貸款": "agri-energy-saving-loan", "青壯年農民從農貸款": "young-farmer-loan",
    "農民組織及農企業產銷經營及研發創新貸款": "agri-enterprise-innovation-loan",
    "擴大家庭農場經營規模協助農民購買耕地貸款": "farmland-purchase-loan",
    "農業天然災害低利貸款": "natural-disaster-loan",
}
TOC_INTERPRETATION_GROUPS = {"fund-operating-rules": "common-rules", "agri-organization-enterprise-innovation-loan": "agri-enterprise-innovation-loan"}
TOC_INTERPRETATION_GROUPS.update({loan["id"]: INTERPRETATION_GROUPS[loan["title"]] for loan in LOANS if loan["title"] in INTERPRETATION_GROUPS})


def interpretation_target(loan_program: str) -> str:
    return f"interpretations/index.html#group-{INTERPRETATION_GROUPS[loan_program]}"
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
                    CANONICAL=e(canonical(relative)), ROOT=e(rel_root(relative)), MAIN=main, BODY_ATTRS=body_attrs)
    path.write_text("\n".join(line.rstrip() for line in document.splitlines()) + "\n", encoding="utf-8")


def wrap(template: str, **values: str) -> str:
    return fill(TEMPLATES[template], **values)


def breadcrumb(relative: str, pairs: list[tuple[str, str | None]], current: str) -> str:
    result = []
    for label, target in pairs:
        result.append(f'<a href="{e(rel(relative, target))}">{e(label)}</a>' if target else f"<span>{e(label)}</span>")
    result.append(f'<span aria-current="page">{e(current)}</span>')
    return '<nav class="breadcrumb" aria-label="麵包屑">' + '<span aria-hidden="true">›</span>'.join(result) + "</nav>"


def search_box() -> str:
    return '''<div class="search-panel" data-search><form role="search" novalidate><label for="site-search">全文搜尋</label><div class="search-row"><input id="site-search" name="q" type="search" autocomplete="off" placeholder="搜尋貸款名稱、資格、用途、額度、期限、函釋或常見問題……"><button type="submit">搜尋</button></div></form><div class="search-filters" aria-label="搜尋類型"></div><p class="search-status" aria-live="polite">請輸入搜尋文字。</p><div class="search-results"></div><button class="search-more" type="button" hidden>顯示更多結果</button></div>'''


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


def loan_nav(relative: str) -> str:
    items = "".join(f'<li><a href="{e(rel(relative, "loans/" + item["id"] + "/index.html"))}">{e(item["title"])}</a></li>' for item in LOANS)
    return f"<details open><summary>23項貸款索引</summary><ol>{items}</ol></details>"


def build_home() -> None:
    relative = "index.html"
    keywords = ["青壯年農民", "農機", "週轉金", "資本支出", "寬緩期", "天然災害", "農企業", "購買耕地", "補正期限", "貸後查驗"]
    popular = "".join(f'<button type="button" data-keyword="{e(word)}">{e(word)}</button>' for word in keywords)
    counts = MANUAL["counts"]
    revision = MANUAL["digitalRevision"]
    hero = f'<div class="current-version">目前版本 <strong>114年度 Beta</strong></div><h1>政策性農業專案貸款業務手冊</h1><p class="subtitle">公開資料數位閱讀與實務索引版</p><p class="beta-note">本網站目前為數位測試版。原文閱讀、完整目錄及全文搜尋已建置；函釋範圍、書表內容及全文仍在持續人工覆核。</p>{search_box()}<div class="popular" aria-label="熱門關鍵字"><span>熱門關鍵字</span>{popular}</div>'
    links = [
        ("原書完整目錄", "versions/114/index.html"), ("讀者快速索引", "quick-index/index.html"),
        ("農業發展基金作業規範", "versions/114/sections/agricultural-development-fund-rules/index.html"),
        ("23項貸款索引", "loans/index.html"), ("函釋來源索引", "interpretations/index.html"),
        ("常見問題", "faq/index.html"), ("書表與附件來源索引", "forms/index.html"),
    ]
    disaster = next((loan for loan in LOANS if loan["id"] == "natural-disaster-low-interest-loan"), None)
    if disaster:
        links.append((disaster["title"], disaster["detailUrl"]))
    quick = '<div class="entry-grid">' + "".join(f'<a class="entry{(" primary" if i < 4 else "")}" href="{e(url)}"><strong>{e(label)}</strong><span>開啟資料</span></a>' for i, (label, url) in enumerate(links)) + "</div>"
    review = f'''<h2 id="review-title">內容覆核狀態</h2><p>原始閱讀頁：{MANUAL["pdfPages"]}頁；原書完整目錄：{counts["tocEntries"]}項；函釋來源索引：{counts["interpretationsSourceIndexed"]}筆；函釋候選庫：{counts["interpretationCandidateInventoryTotal"]}筆；函釋未決候選：{counts["interpretationCandidatesPending"]}筆；書表來源索引：{counts["formsSourceIndexed"]}筆；書表未分類候選：{counts["formCandidatesPending"]}筆。</p><p>書表逐頁人工覆核：尚未完成；函釋結束頁確認：尚未完成；全文逐頁人工校讀：尚未完成。</p><p class="layout-note">來源索引依嚴格頁面與欄位規則建立；候選庫總量僅為偵測庫存，不等同待覆核數。全文逐頁校讀、函釋涵蓋範圍及書表內容仍需人工確認。</p>'''
    version = f'''<h2 id="version-title">版本資訊</h2><dl><div><dt>資料版本</dt><dd>114年度 Beta</dd></div><div><dt>PDF實體頁數</dt><dd>359頁</dd></div><div><dt>數位版本</dt><dd>{e(revision)}</dd></div><div><dt>來源文件</dt><dd>114年度政策性農業專案貸款業務手冊</dd></div></dl><div class="version-actions"><a class="button-link" href="versions/114/index.html">開啟原書完整目錄</a><a class="button-link secondary" href="downloads/{PDF_NAME}">開啟／下載原始PDF</a><a href="versions/index.html">查看版本紀錄與更新說明</a></div>'''
    write(relative, "政策性農業專案貸款業務手冊｜114年度數位閱讀版", wrap("home", HERO=hero, QUICK=quick, REVIEW=review, VERSION=version))


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
            target = "interpretations/index.html#group-" + TOC_INTERPRETATION_GROUPS[item["id"].removesuffix("-interpretations")]
        elif item["id"] == "natural-disaster-rules":
            target = "versions/114/sections/natural-disaster-rules/index.html"
        elif item["kind"] == "faq":
            target = "faq/index.html#item-" + item["id"]
        elif item["kind"] in {"appendix", "attachment"}:
            target = "forms/index.html#item-" + item["id"]
        label = f'<a href="{e(rel(relative, target))}">{e(item["title"])}</a>' if target else f'<strong>{e(item["title"])}</strong>'
        page = f'<span>手冊頁 {item["printedPage"]}</span>' if item["printedPage"] is not None else ""
        rows.append(f'<li class="toc-level-{item["level"]}">{label}{page}</li>')
    content = breadcrumb(relative, [("首頁", "index.html")], "完整目錄") + f'<h1>114年度原書完整目錄</h1><p class="source-meta">逐項轉錄原始PDF第1–2頁，共 {len(TOC["items"])} 個目錄項目；層級、函釋、常見問答、附錄與附件均與原書分列。</p><p><a href="{e(rel(relative, "quick-index/index.html"))}">需要較精簡的入口？前往讀者快速索引</a></p>' + search_box() + '<ol class="index-rows faithful-toc">' + "".join(rows) + "</ol>"
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
    content = breadcrumb(relative, [("首頁", "index.html")], "快速索引") + '<h1>讀者快速索引</h1><p class="source-meta">依常用閱讀入口整理，不取代原書目錄。</p><p><a href="../versions/114/index.html">查看忠實轉錄的原書完整目錄</a></p><div class="toc-layout">' + "".join(groups) + '</div>'
    write(relative, "讀者快速索引｜政策性農業專案貸款業務手冊", wrap("manual-index", CONTENT=content))


def build_sections() -> None:
    sections = [
        ("policy-loan-regulations", "辦理政策性農業專案貸款辦法", 1, 29),
        ("agricultural-development-fund-rules", "農業發展基金貸款作業規範及相關函釋", 30, 93),
        ("loan-programs", "各項貸款規定", 94, 269),
        ("bank-operating-rules-appendices", "全國農業金庫作業規範附錄", 309, 312),
        ("amendment-faq", "政策性農業專案貸款增修正規定常見問題", 313, 347),
        ("attachments", "附件", 348, 357),
        ("natural-disaster-rules", "農業天然災害救助辦法及低利貸款相關規定", 270, 299),
    ]
    for slug, title, start, end in sections:
        relative = f"versions/114/sections/{slug}/index.html"
        nav = '<details open><summary>本篇頁面</summary><ol>' + "".join(f'<li><a href="#pdf-page-{p["pdfPage"]}">手冊頁 {p["printedPage"]}</a></li>' for p in page_range(start, end)) + "</ol></details>"
        related = f'<p><a class="button-link" href="{e(rel(relative, "interpretations/index.html#group-natural-disaster-loan"))}">查看農業天然災害低利貸款相關函釋</a></p>' if slug == "natural-disaster-rules" else ""
        content = f'<h1>{e(title)}</h1><p class="source-meta">手冊印刷頁 {start}–{end}｜資料版本：114年度</p>{related}' + "".join(page_card(p, relative) for p in page_range(start, end))
        main = wrap("reading-page", BREADCRUMB=breadcrumb(relative, [("首頁", "index.html"), ("114年度完整目錄", "versions/114/index.html")], title), NAV=nav, CONTENT=content)
        write(relative, f"{title}｜114年度", main, body_attrs=f'data-printable="true" data-search-scope="section:{slug}"')


def build_physical_pages() -> None:
    for page in PAGES:
        number = page["pdfPage"]
        relative = f"versions/114/pages/page-{number:03d}.html"
        previous = f'<a href="page-{number-1:03d}.html">上一頁</a>' if number > 1 else "<span>已是第一頁</span>"
        following = f'<a href="page-{number+1:03d}.html">下一頁</a>' if number < 359 else "<span>已是最後一頁</span>"
        nav = f'<details open><summary>逐頁閱讀</summary><p>{previous}　{following}</p><p><a href="../index.html">回完整目錄</a></p></details>'
        printed = page["printedPage"] if page["printedPage"] is not None else "目錄"
        content = f'<h1>{e(page["title"])}</h1><p class="source-meta">手冊頁：{e(printed)}｜PDF實體頁：{number}／359｜資料版本：114年度</p>' + page_card(page, relative)
        main = wrap("reading-page", BREADCRUMB=breadcrumb(relative, [("首頁", "index.html"), ("完整目錄", "versions/114/index.html")], f"PDF頁碼 {number}"), NAV=nav, CONTENT=content)
        write(relative, f"PDF頁碼 {number}｜{page['title']}", main, body_attrs=f'data-printable="true" data-search-scope="section:{page["chapterId"]}"')


def build_loans() -> None:
    relative = "loans/index.html"
    policy = [loan for loan in LOANS if loan["category"] == "政策性農業專案貸款"]
    bank = [loan for loan in LOANS if loan["category"] == "全國農業金庫貸款"]
    def rows(items: list[dict]) -> str:
        return '<ol class="loan-grid">' + "".join(f'<li><a href="{e(loan["id"] + "/index.html")}"><strong>{e(loan["title"])}</strong><span>{e(loan["category"])}｜手冊頁 {loan["sourceStartPage"]}–{loan["sourceEndPage"]}{"｜含函釋" if loan["hasInterpretations"] else ""}</span><em>前往原文閱讀</em></a></li>' for loan in items) + "</ol>"
    content = breadcrumb(relative, [("首頁", "index.html")], "貸款索引") + '<h1>政策農貸專用貸款索引</h1><p class="layout-note">本索引只提供貸款名稱、類別、原始頁碼、函釋標記與原文入口，不提供資格判斷或貸款推薦。</p><section id="policy-loans"><h2>20項政策性貸款</h2>' + rows(policy) + '</section><section id="bank-loans"><h2>3項全國農業金庫貸款</h2>' + rows(bank) + "</section>"
    write(relative, "貸款索引｜政策性農業專案貸款業務手冊", wrap("loan-index", CONTENT=content))
    for loan in LOANS:
        relative = f'loans/{loan["id"]}/index.html'
        pages = page_range(loan["sourceStartPage"], loan["sourceEndPage"])
        interpretation_link = f'<p><a class="button-link" href="{e(rel(relative, interpretation_target(loan["title"])))}">查看本貸款相關函釋</a></p>' if loan["hasInterpretations"] and loan["title"] in INTERPRETATION_GROUPS else ""
        content = f'<h1>{e(loan["title"])}</h1><p class="source-meta">{e(loan["category"])}｜手冊印刷頁 {loan["sourceStartPage"]}–{loan["sourceEndPage"]}｜{"包含相關函釋" if loan["hasInterpretations"] else "原手冊目錄未另列函釋"}</p>{interpretation_link}<p class="layout-note">本頁忠實呈現原文，不提供資格摘要、額度摘要、利率摘要或核貸判斷。</p>' + "".join(page_card(page, relative) for page in pages)
        main = wrap("loan-detail", BREADCRUMB=breadcrumb(relative, [("首頁", "index.html"), ("貸款索引", "loans/index.html")], loan["title"]), NAV=loan_nav(relative), CONTENT=content)
        write(relative, f"{loan['title']}｜貸款索引", main, body_attrs=f'data-printable="true" data-search-scope="loan:{loan["id"]}"')


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


def build_indexes() -> None:
    relative = "interpretations/index.html"
    counts = MANUAL["counts"]
    groups = []
    for loan_program, slug in INTERPRETATION_GROUPS.items():
        items = [item for item in INTERPRETATIONS if item["loanProgram"] == loan_program]
        groups.append(f'<section id="group-{slug}" class="interpretation-group"><h2>{e(loan_program)}</h2><p class="source-meta">{len(items)} 筆函釋</p>{index_items(relative, items, "函釋")}<p><a href="#main-content">返回函釋頁頂端</a></p></section>')
    quick_links = '<nav class="index-rows" aria-label="依類別快速前往"><h2>依類別快速前往</h2><ul>' + ''.join(f'<li><a href="#group-{slug}">{e(program)}</a></li>' for program, slug in INTERPRETATION_GROUPS.items()) + '</ul></nav>'
    content = breadcrumb(relative, [("首頁", "index.html")], "函釋來源索引") + f'<h1>函釋來源索引</h1><p class="source-meta">依同頁完整標頭、日期、完整文號與主旨起始建立，共 {counts["interpretationsSourceIndexed"]} 筆。候選庫共 {counts["interpretationCandidateInventoryTotal"]} 筆，其中未決候選 {counts["interpretationCandidatesPending"]} 筆；候選庫總量不等於待覆核數。結束頁尚待人工確認。</p>' + quick_links + ''.join(groups) + '<p><a href="../faq/index.html">前往常見問答</a></p>'
    write(relative, "相關函釋索引｜政策性農業專案貸款業務手冊", wrap("interpretations", CONTENT=content))
    relative = "faq/index.html"
    content = breadcrumb(relative, [("首頁", "index.html")], "常見問答") + '<h1>增修規定常見問答</h1><p class="layout-note">本頁依原手冊目錄建立入口，不提供AI摘要。</p>' + index_items(relative, FAQ, "FAQ")
    write(relative, "增修規定常見問答｜政策性農業專案貸款業務手冊", wrap("faq", CONTENT=content))
    relative = "forms/index.html"
    content = breadcrumb(relative, [("首頁", "index.html")], "書表與附件來源索引") + f'<h1>書表與附件來源索引</h1><p class="source-meta">書表來源索引 {counts["formsSourceIndexed"]} 筆；候選庫 {counts["formCandidateInventoryTotal"]} 筆，其中已納入 {counts["formCandidatesPromoted"]} 筆、排除 {counts["formCandidatesExcluded"]} 筆、真正待人工覆核 {counts["formCandidatesPending"]} 筆。另列 {len(APPENDICES)} 項原手冊附錄／附件。</p><h2>附錄與附件</h2>' + index_items(relative, APPENDICES, "附錄／附件") + '<h2>書表來源索引</h2>' + index_items(relative, FORMS, "書表")
    write(relative, "附件與書表索引｜政策性農業專案貸款業務手冊", wrap("forms", CONTENT=content))


def build_versions() -> None:
    relative = "versions/index.html"
    revision = MANUAL["digitalRevision"]
    content = breadcrumb(relative, [("首頁", "index.html")], "版本紀錄") + f'''<h1>版本紀錄與資料來源</h1><article class="version-record"><div class="version-record-head"><div><h2>114年度</h2><p>數位版本：{e(revision)}</p></div><span class="version-status">Beta</span></div><dl class="version-meta"><div><dt>來源文件</dt><dd>114年度政策性農業專案貸款業務手冊</dd></div><div><dt>PDF實體頁數</dt><dd>359頁</dd></div><div class="version-sha"><dt>SHA-256</dt><dd><code>0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54</code></dd></div></dl><div class="version-actions"><a class="button-link" href="114/index.html">開啟完整目錄</a><a class="button-link secondary" href="../downloads/{PDF_NAME}">開啟／下載原始PDF</a></div><div class="version-update"><h3>Beta.2.1 緊急資料校正</h3><p>函釋改採嚴格完整標頭解析，區分來源索引、候選庫、重複偵測與真正待人工覆核；書表候選同步標示納入、排除或待覆核。</p></div></article><section class="version-policy"><h2>版本保存原則</h2><p>來源索引是依既定來源規則可定位的資料；候選庫為自動偵測庫存，並不等同待覆核數。新版PDF不得覆蓋舊版；新版本使用新version ID，重新計算頁數、SHA-256、頁碼映射、文字擷取、目錄、呈現規則與搜尋索引。正式內容始終以原始PDF為準。</p></section>'''
    write(relative, "版本紀錄與資料來源｜政策性農業專案貸款業務手冊", wrap("versions", CONTENT=content))


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    shutil.copytree(ROOT / "assets/css", SITE / "assets/css", dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets/js", SITE / "assets/js", dirs_exist_ok=True)
    (SITE / "assets/data").mkdir(parents=True, exist_ok=True)
    for data_file in ("search-concepts.json", "search-intents.json"):
        shutil.copy2(DATA / data_file, SITE / "assets/data" / data_file)
    shutil.copytree(ROOT / "assets/page-previews", SITE / "assets/page-previews", dirs_exist_ok=True)
    shutil.copy2(ROOT / "assets/favicon.svg", SITE / "assets/favicon.svg")
    (SITE / "downloads").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "source" / PDF_NAME, SITE / "downloads" / PDF_NAME)
    build_home(); build_version_index(); build_quick_index(); build_sections(); build_physical_pages(); build_loans(); build_indexes(); build_versions()
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    html_files = sorted(SITE.rglob("*.html"))
    sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n" + "".join(f"  <url><loc>{e(canonical(str(p.relative_to(SITE))))}</loc></url>\n" for p in html_files) + "</urlset>\n"
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (SITE / "robots.txt").write_text("User-agent: *\nAllow: /policy-agri-loan-handbook/\nSitemap: " + ORIGIN + "sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(html_files)} HTML pages")


if __name__ == "__main__":
    main()
