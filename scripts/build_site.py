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

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "114"
SITE = ROOT / "site"
TEMPLATES = {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "templates").glob("*.html")}
PAGES = json.loads((DATA / "pages.json").read_text(encoding="utf-8"))
TOC = json.loads((DATA / "toc.json").read_text(encoding="utf-8"))
LOANS = json.loads((DATA / "loan-programs.json").read_text(encoding="utf-8"))
INTERPRETATIONS = json.loads((DATA / "interpretations.json").read_text(encoding="utf-8"))
FAQ = json.loads((DATA / "faq.json").read_text(encoding="utf-8"))
FORMS = json.loads((DATA / "forms.json").read_text(encoding="utf-8"))
APPENDICES = json.loads((DATA / "appendices.json").read_text(encoding="utf-8"))
RULES = json.loads((DATA / "page-rendering-rules.json").read_text(encoding="utf-8"))
RENDERING = {p["pdfPage"]: p for p in RULES["pages"]}
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


def write(relative: str, title: str, main: str, description: str = DESCRIPTION) -> None:
    path = SITE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    document = fill(TEMPLATES["base"], TITLE=e(title), DESCRIPTION=e(description),
                    CANONICAL=e(canonical(relative)), ROOT=e(rel_root(relative)), MAIN=main)
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
    return '''<div class="search-panel" data-search><form role="search" novalidate><label for="site-search">全文搜尋</label><div class="search-row"><input id="site-search" name="q" type="search" autocomplete="off" placeholder="搜尋貸款名稱、資格、用途、額度、期限、函釋或常見問題……"><button type="submit">搜尋</button></div></form><p class="search-status" aria-live="polite"></p><div class="search-results"></div></div>'''


def paragraphize(text: str) -> str:
    blocks = re.split(r"\n\s*\n", text.strip()) if text.strip() else []
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
    hero = f'<div class="current-version">目前版本 <strong>114年度</strong></div><h1>政策性農業專案貸款業務手冊</h1><p class="subtitle">公開資料數位閱讀與實務索引版</p>{search_box()}<div class="popular" aria-label="熱門關鍵字"><span>熱門關鍵字</span>{popular}</div>'
    links = [
        ("政策農貸共同規定", "versions/114/sections/policy-loan-regulations/index.html"),
        ("20項政策性貸款", "loans/index.html#policy-loans"),
        ("農業發展基金作業規範", "versions/114/sections/agricultural-development-fund-rules/index.html"),
        ("相關函釋", "interpretations/index.html"), ("天然災害低利貸款", "loans/natural-disaster-low-interest-loan/index.html"),
        ("全國農業金庫貸款", "loans/index.html#bank-loans"), ("增修問答", "faq/index.html"), ("附件與書表", "forms/index.html"),
    ]
    quick = '<div class="entry-grid">' + "".join(f'<a class="entry{(" primary" if i < 4 else "")}" href="{e(url)}"><strong>{e(label)}</strong><span>開啟資料</span></a>' for i, (label, url) in enumerate(links)) + "</div>"
    version = f'''<h2 id="version-title">版本資訊</h2><dl><div><dt>資料版本</dt><dd>114年度</dd></div><div><dt>PDF實體頁數</dt><dd>359頁</dd></div><div><dt>數位版本</dt><dd>114.0.0</dd></div><div><dt>來源文件</dt><dd>114年度政策性農業專案貸款業務手冊</dd></div></dl><div class="version-actions"><a class="button-link" href="versions/114/index.html">開啟本版本完整目錄</a><a class="button-link secondary" href="downloads/{PDF_NAME}">開啟／下載原始PDF</a><a href="versions/index.html">查看版本紀錄與更新說明</a></div>'''
    write(relative, "政策性農業專案貸款業務手冊｜114年度數位閱讀版", wrap("home", HERO=hero, QUICK=quick, VERSION=version))


def build_version_index() -> None:
    relative = "versions/114/index.html"
    groups = []
    for group in TOC["groups"]:
        items = []
        for item in group["items"]:
            target = f'versions/114/sections/{item["id"]}/index.html'
            if item["id"] in {loan["id"] for loan in LOANS}:
                target = f'loans/{item["id"]}/index.html'
            elif item["id"] in {"appendix-1", "appendix-2", "appendix-3", "attachment-1", "attachment-2", "attachment-3"}:
                target = "forms/index.html#item-" + item["id"]
            badge = " <small>含函釋</small>" if item.get("hasInterpretations") else ""
            children = ""
            if item.get("children"):
                children = '<ol class="nested-toc">' + "".join(f'<li><a href="{e(rel(relative, "loans/" + child["id"] + "/index.html"))}">{e(child["title"])}</a> <span>手冊頁 {child["printedPage"]}</span>{(" <small>含函釋</small>" if child.get("hasInterpretations") else "")}</li>' for child in item["children"]) + "</ol>"
            items.append(f'<li><a href="{e(rel(relative, target))}">{e(item["title"])}</a> <span>手冊頁 {item["printedPage"]}</span>{badge}{children}</li>')
        groups.append(f'<section class="toc-group"><h2>{e(group["title"])}</h2><ol class="index-rows">{"".join(items)}</ol></section>')
    content = breadcrumb(relative, [("首頁", "index.html")], "完整目錄") + '<h1>114年度完整目錄</h1><p class="source-meta">忠實依原手冊目錄分組，顯示印刷頁碼、函釋、FAQ與附件入口。</p>' + search_box() + '<div class="toc-layout">' + "".join(groups) + "</div>"
    write(relative, "114年度完整目錄｜政策性農業專案貸款業務手冊", wrap("manual-index", CONTENT=content))


def build_sections() -> None:
    sections = [
        ("policy-loan-regulations", "辦理政策性農業專案貸款辦法", 1, 29),
        ("agricultural-development-fund-rules", "農業發展基金貸款作業規範及相關函釋", 30, 93),
        ("loan-programs", "各項貸款規定", 94, 269),
        ("bank-operating-rules-appendices", "全國農業金庫作業規範附錄", 309, 312),
        ("amendment-faq", "政策性農業專案貸款增修正規定常見問題", 313, 347),
        ("attachments", "附件", 348, 357),
    ]
    for slug, title, start, end in sections:
        relative = f"versions/114/sections/{slug}/index.html"
        nav = '<details open><summary>本篇頁面</summary><ol>' + "".join(f'<li><a href="#pdf-page-{p["pdfPage"]}">手冊頁 {p["printedPage"]}</a></li>' for p in page_range(start, end)) + "</ol></details>"
        content = f'<h1>{e(title)}</h1><p class="source-meta">手冊印刷頁 {start}–{end}｜資料版本：114年度</p>' + "".join(page_card(p, relative) for p in page_range(start, end))
        main = wrap("reading-page", BREADCRUMB=breadcrumb(relative, [("首頁", "index.html"), ("114年度完整目錄", "versions/114/index.html")], title), NAV=nav, CONTENT=content)
        write(relative, f"{title}｜114年度", main)


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
        write(relative, f"PDF頁碼 {number}｜{page['title']}", main)


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
        content = f'<h1>{e(loan["title"])}</h1><p class="source-meta">{e(loan["category"])}｜手冊印刷頁 {loan["sourceStartPage"]}–{loan["sourceEndPage"]}｜{"包含相關函釋" if loan["hasInterpretations"] else "原手冊目錄未另列函釋"}</p><p class="layout-note">本頁忠實呈現原文，不提供資格摘要、額度摘要、利率摘要或核貸判斷。</p>' + "".join(page_card(page, relative) for page in pages)
        main = wrap("loan-detail", BREADCRUMB=breadcrumb(relative, [("首頁", "index.html"), ("貸款索引", "loans/index.html")], loan["title"]), NAV=loan_nav(relative), CONTENT=content)
        write(relative, f"{loan['title']}｜貸款索引", main)


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
        url = rel(relative, f"downloads/{PDF_NAME}") + f"#page={pdf}"
        blocks.append(f'<li id="item-{e(item["id"])}"><div><strong>{e(item["title"])}</strong><span>{e(kind)}｜手冊頁 {e(printed)}｜PDF頁 {e(pdf)}</span>{extra}</div><a href="{e(url)}">開啟原文</a></li>')
    return '<ol class="index-rows index-detail">' + "".join(blocks) + "</ol>"


def build_indexes() -> None:
    relative = "interpretations/index.html"
    content = breadcrumb(relative, [("首頁", "index.html")], "函釋索引") + f'<h1>相關函釋索引</h1><p class="source-meta">共 {len(INTERPRETATIONS)} 筆來源索引；未可靠辨識欄位維持待覆核，不自行猜測。</p>' + index_items(relative, INTERPRETATIONS, "函釋") + '<p><a href="../faq/index.html">前往常見問答</a></p>'
    write(relative, "相關函釋索引｜政策性農業專案貸款業務手冊", wrap("interpretations", CONTENT=content))
    relative = "faq/index.html"
    content = breadcrumb(relative, [("首頁", "index.html")], "常見問答") + '<h1>增修規定常見問答</h1><p class="layout-note">本頁依原手冊目錄建立入口，不提供AI摘要。</p>' + index_items(relative, FAQ, "FAQ")
    write(relative, "增修規定常見問答｜政策性農業專案貸款業務手冊", wrap("faq", CONTENT=content))
    relative = "forms/index.html"
    content = breadcrumb(relative, [("首頁", "index.html")], "附件與書表") + f'<h1>附件與書表索引</h1><p class="source-meta">{len(APPENDICES)} 項正式附錄／附件，另有 {len(FORMS)} 筆書表與附件文字層入口。複雜版面請以原頁預覽及PDF為準。</p><h2>正式附錄與附件</h2>' + index_items(relative, APPENDICES, "附錄／附件") + '<h2>書表索引</h2>' + index_items(relative, FORMS, "書表／附件")
    write(relative, "附件與書表索引｜政策性農業專案貸款業務手冊", wrap("forms", CONTENT=content))


def build_versions() -> None:
    relative = "versions/index.html"
    content = breadcrumb(relative, [("首頁", "index.html")], "版本紀錄") + f'''<h1>版本紀錄與資料來源</h1><article class="version-record"><div class="version-record-head"><div><h2>114年度</h2><p>初始數位版本：114.0.0</p></div><span class="version-status">目前版本</span></div><dl class="version-meta"><div><dt>來源文件</dt><dd>114年度政策性農業專案貸款業務手冊</dd></div><div><dt>PDF實體頁數</dt><dd>359頁</dd></div><div class="version-sha"><dt>SHA-256</dt><dd><code>0bcb266d2f1860c6038a5bc2eaad69dc6700d999770f5b40642f875c3343ed54</code></dd></div></dl><div class="version-actions"><a class="button-link" href="114/index.html">開啟完整目錄</a><a class="button-link secondary" href="../downloads/{PDF_NAME}">開啟／下載原始PDF</a></div></article><section class="version-policy"><h2>版本保存原則</h2><p>新版PDF不得覆蓋舊版；新版本使用新version ID，重新計算頁數、SHA-256、頁碼映射、文字擷取、目錄、呈現規則與搜尋索引。舊版本永久保留。</p><p>本輪不建立Git tag或Release，待人工內容抽查後另案處理。</p></section>'''
    write(relative, "版本紀錄與資料來源｜政策性農業專案貸款業務手冊", wrap("versions", CONTENT=content))


def main() -> None:
    shutil.copytree(ROOT / "assets/css", SITE / "assets/css", dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets/js", SITE / "assets/js", dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets/page-previews", SITE / "assets/page-previews", dirs_exist_ok=True)
    shutil.copy2(ROOT / "assets/favicon.svg", SITE / "assets/favicon.svg")
    shutil.copy2(ROOT / "source" / PDF_NAME, SITE / "downloads" / PDF_NAME)
    build_home(); build_version_index(); build_sections(); build_physical_pages(); build_loans(); build_indexes(); build_versions()
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    html_files = sorted(SITE.rglob("*.html"))
    sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n" + "".join(f"  <url><loc>{e(canonical(str(p.relative_to(SITE))))}</loc></url>\n" for p in html_files) + "</urlset>\n"
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (SITE / "robots.txt").write_text("User-agent: *\nAllow: /policy-agri-loan-handbook/\nSitemap: " + ORIGIN + "sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(html_files)} HTML pages")


if __name__ == "__main__":
    main()
