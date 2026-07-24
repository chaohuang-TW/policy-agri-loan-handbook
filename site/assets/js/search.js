(function () {
  "use strict";

  const Core = globalThis.ManualSearchCore;
  const TYPE_LABELS = { "書表附件": "書表" };
  const LIMIT = 20;
  const page = document.body;
  const siteRoot = new URL(page.dataset.siteRoot || "./", document.baseURI);
  const dataUrl = (name) => new URL(`assets/data/${name}`, siteRoot);
  let dataPromise;

  function loadData() {
    if (!dataPromise) {
      dataPromise = Promise.all(
        ["search-index.json", "search-concepts.json", "search-intents.json"].map((name) =>
          fetch(dataUrl(name)).then((response) => {
            if (!response.ok) throw new Error("搜尋資料載入失敗");
            return response.json();
          })
        )
      ).then(([records, concepts, intents]) => Core.prepareSearchData(records, concepts, intents));
    }
    return dataPromise;
  }

  function appendHighlighted(parent, text, ranges) {
    let cursor = 0;
    for (const range of ranges) {
      if (range.start < cursor) continue;
      parent.append(document.createTextNode(text.slice(cursor, range.start)));
      const mark = document.createElement("mark");
      mark.className = range.kind === "related"
        ? "search-highlight search-highlight-related"
        : "search-highlight";
      mark.textContent = text.slice(range.start, range.end);
      parent.append(mark);
      cursor = range.end;
    }
    parent.append(document.createTextNode(text.slice(cursor)));
  }

  function createResult(item) {
    const record = item.record;
    const article = document.createElement("article");
    article.className = "search-result";
    const h3 = document.createElement("h3");
    const link = document.createElement("a");
    link.href = new URL(record.url, siteRoot).href;
    link.textContent = record.title;
    h3.append(link);
    article.append(h3);

    const meta = document.createElement("p");
    meta.className = "result-match-meta";
    meta.textContent = `${TYPE_LABELS[record.type] || record.type}｜${(record.breadcrumb || []).join(" › ")}`;
    article.append(meta);

    const snippet = Core.createSnippetRange(record.text, item.originalTerms, item.relatedTerms);
    const snippetText = record.text.slice(snippet.start, snippet.end);
    const snippetRanges = snippet.matches.map((range) => ({
      start: range.start - snippet.start,
      end: range.end - snippet.start,
      kind: range.kind
    }));
    const paragraph = document.createElement("p");
    paragraph.className = "result-snippet";
    if (snippet.start > 0) paragraph.append(document.createTextNode("…"));
    appendHighlighted(paragraph, snippetText, snippetRanges);
    if (snippet.end < record.text.length) paragraph.append(document.createTextNode("…"));
    article.append(paragraph);

    if (snippet.matches.some((range) => range.kind === "related")) {
      const related = document.createElement("p");
      related.className = "result-related-meta";
      related.textContent = "包含相關詞命中";
      article.append(related);
    }

    const pages = document.createElement("p");
    pages.className = "result-pages";
    pages.textContent = `版本：${record.version}｜手冊頁：${record.printedPage || "目錄"}｜PDF頁：${record.pdfPage}／359`;
    article.append(pages);
    if (record.documentNumber || record.date || record.loanProgram) {
      const extra = document.createElement("p");
      extra.className = "result-pages";
      extra.textContent = [record.date, record.documentNumber, record.loanProgram].filter(Boolean).join("｜");
      article.append(extra);
    }
    return article;
  }

  function attach(panel) {
    const form = panel.querySelector("form");
    const input = panel.querySelector("input[type=search]");
    const status = panel.querySelector(".search-status");
    const results = panel.querySelector(".search-results");
    const more = panel.querySelector(".search-more");
    const filters = panel.querySelector(".search-filters");
    const scopeOptions = panel.querySelector(".search-scope-options");
    const pageScopes = (page.dataset.searchScopes || page.dataset.searchScope || "all")
      .split(",").map((value) => value.trim()).filter(Boolean);
    const pageGroup = page.dataset.searchScopeGroup || "";
    let timer;
    const state = {
      allRanked: [], ranked: [], shown: 0, type: "all", scope: "all",
      query: "", prepared: null
    };

    if ((pageGroup || !pageScopes.includes("all")) && scopeOptions) {
      scopeOptions.hidden = false;
      scopeOptions.querySelector("[data-scope=chapter]").textContent = pageGroup ? "本貸款" : "本章";
    }

    function focusResults() {
      (results.querySelector("a") || status).focus();
    }

    function countForType(type) {
      return type === "all"
        ? state.allRanked.length
        : state.allRanked.filter((item) => item.record.type === type).length;
    }

    function renderFilters() {
      filters.replaceChildren();
      [["all", "全部"], ...Core.TYPES.map((type) => [type, TYPE_LABELS[type] || type])]
        .forEach(([value, label]) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "search-filter-button";
          button.setAttribute("aria-pressed", String(value === state.type));
          button.textContent = `${label} ${countForType(value)}`;
          button.addEventListener("click", () => applyType(value));
          filters.append(button);
        });
    }

    function render(focusAfter = false) {
      results.replaceChildren(...state.ranked.slice(0, state.shown).map(createResult));
      status.textContent = `找到 ${state.ranked.length} 筆結果，目前顯示 ${Math.min(state.shown, state.ranked.length)} 筆。`;
      more.hidden = state.shown >= state.ranked.length;
      renderFilters();
      if (focusAfter) focusResults();
    }

    function applyType(type, focusAfter = false) {
      state.type = type;
      state.shown = LIMIT;
      state.ranked = type === "all"
        ? state.allRanked
        : Core.searchRecords(
          state.prepared.records, state.query, state.prepared.concepts,
          state.prepared.intents, type, state.scope
        );
      render(focusAfter);
    }

    function noScopeResult(focusAfter = false) {
      results.replaceChildren();
      const paragraph = document.createElement("p");
      paragraph.className = "search-empty-guidance";
      paragraph.append(document.createTextNode(pageGroup ? "本貸款沒有找到結果。" : "本章沒有找到結果。"));
      const button = document.createElement("button");
      button.type = "button";
      button.className = "search-search-all";
      button.textContent = "改查全手冊";
      button.addEventListener("click", () => {
        state.scope = "all";
        scopeOptions?.querySelectorAll("button").forEach((item) =>
          item.setAttribute("aria-pressed", String(item.dataset.scope === "all"))
        );
        run(true);
      });
      paragraph.append(button);
      results.append(paragraph);
      more.hidden = true;
      status.textContent = "沒有符合目前搜尋範圍的結果。";
      if (focusAfter) status.focus();
    }

    function renderFallback() {
      results.replaceChildren();
      const paragraph = document.createElement("p");
      paragraph.className = "search-empty-guidance";
      paragraph.append(document.createTextNode("搜尋索引目前無法載入。您仍可"));
      const catalog = document.createElement("a");
      catalog.href = new URL("manual/index.html", siteRoot).href;
      catalog.textContent = "查看完整目錄";
      const pdf = document.createElement("a");
      pdf.href = new URL("downloads/policy-agri-loan-handbook-114.pdf", siteRoot).href;
      pdf.textContent = "開啟完整 PDF";
      paragraph.append(catalog, document.createTextNode("或"), pdf, document.createTextNode("。"));
      results.append(paragraph);
      more.hidden = true;
      status.textContent = "搜尋索引目前無法載入。";
    }

    async function run(focusAfter = false) {
      const validation = Core.validateQuery(input.value);
      if (!validation.ok) {
        clearTimeout(timer);
        state.allRanked = [];
        state.ranked = [];
        results.replaceChildren();
        more.hidden = true;
        status.textContent = validation.error;
        if (focusAfter) status.focus();
        return;
      }
      if (validation.empty) {
        state.allRanked = [];
        state.ranked = [];
        state.shown = 0;
        results.replaceChildren();
        more.hidden = true;
        status.textContent = "請輸入搜尋文字。";
        return;
      }

      status.textContent = "搜尋中…";
      try {
        state.prepared = await loadData();
        state.query = validation.normalized;
        state.allRanked = Core.searchRecords(
          state.prepared.records, state.query, state.prepared.concepts,
          state.prepared.intents, "all", state.scope
        );
        state.type = "all";
        state.ranked = state.allRanked;
        state.shown = LIMIT;
        if (!state.ranked.length && state.scope !== "all") noScopeResult(focusAfter);
        else render(focusAfter);
      } catch (_error) {
        renderFallback();
        if (focusAfter) status.focus();
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      clearTimeout(timer);
      run(true);
    });
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => run(false), 250);
    });
    more.addEventListener("click", () => {
      state.shown += LIMIT;
      render();
      more.focus();
    });
    scopeOptions?.querySelectorAll("button").forEach((button) =>
      button.addEventListener("click", () => {
        scopeOptions.querySelectorAll("button").forEach((item) =>
          item.setAttribute("aria-pressed", String(item === button))
        );
        state.scope = button.dataset.scope === "chapter" ? (pageGroup || pageScopes) : "all";
        if (input.value.trim()) run(true);
      })
    );
    panel.__manualSearch = { run, input, state };
  }

  document.querySelectorAll("[data-search]").forEach(attach);
})();
