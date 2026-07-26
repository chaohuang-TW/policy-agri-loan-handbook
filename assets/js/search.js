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
    const context = document.createElement("p");
    context.className = "result-context";
    context.textContent = record.contextTitle || (record.breadcrumb || [record.category])[0];
    article.append(context);
    const badge = document.createElement("span");
    badge.className = "result-type-badge";
    badge.textContent = TYPE_LABELS[record.type] || record.type;
    article.append(badge);
    const h3 = document.createElement("h3");
    h3.textContent = record.title;
    article.append(h3);

    const meta = document.createElement("p");
    meta.className = "result-match-meta";
    meta.textContent = item.originalTerms?.length ? "直接命中查詢文字" : "相關詞命中";
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

    const pages = document.createElement("p");
    pages.className = "result-pages";
    pages.textContent = `出處：${record.version}｜手冊頁 ${record.printedPage || "目錄"}｜PDF頁 ${record.pdfPage}／359`;
    article.append(pages);
    if (record.documentNumber || record.date || record.loanProgram) {
      const extra = document.createElement("p");
      extra.className = "result-pages";
      extra.textContent = [record.date, record.documentNumber, record.loanProgram].filter(Boolean).join("｜");
      article.append(extra);
    }
    const actions = document.createElement("p");
    actions.className = "result-actions";
    const primary = document.createElement("a");
    primary.href = new URL(record.url, siteRoot).href;
    primary.textContent = record.type === "貸款索引" ? "查看貸款" :
      record.type === "函釋" ? "查看函釋" :
      record.type === "書表附件" ? "查看書表" :
      record.type === "附錄附件" ? "查看附錄" :
      record.type === "常見問答" ? "查看問答" : "查看原文";
    actions.append(primary);
    if (record.pdfPage) {
      const pdf = document.createElement("a");
      pdf.className = "secondary-action";
      pdf.href = new URL(`downloads/policy-agri-loan-handbook-114.pdf#page=${record.pdfPage}`, siteRoot).href;
      pdf.textContent = "開啟PDF頁面";
      actions.append(pdf);
    }
    article.append(actions);
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
    const contextScope = pageGroup || (pageScopes.includes("all") ? "all" : pageScopes);
    const defaultScope = panel.dataset.searchDefaultScope === "context" && contextScope !== "all"
      ? "context"
      : "all";
    let timer;
    const state = {
      allRanked: [], ranked: [], shown: 0, type: "all", scope: "all",
      query: "", prepared: null
    };

    if ((pageGroup || !pageScopes.includes("all")) && scopeOptions) {
      scopeOptions.hidden = false;
      scopeOptions.querySelector("[data-scope=chapter]").textContent = pageGroup ? "本貸款" : "本章";
    }

    function setScope(mode, rerun = false) {
      const resolvedMode = mode === "context" && contextScope !== "all" ? "context" : "all";
      state.scope = resolvedMode === "context" ? contextScope : "all";
      scopeOptions?.querySelectorAll("button").forEach((button) => {
        const buttonMode = button.dataset.scope === "chapter" ? "context" : "all";
        button.setAttribute("aria-pressed", String(buttonMode === resolvedMode));
      });
      if (rerun && input.value.trim()) return run(true);
      return Promise.resolve();
    }

    setScope(defaultScope);

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
      status.hidden = false;
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
        setScope("all");
        run(true);
      });
      paragraph.append(button);
      results.append(paragraph);
      more.hidden = true;
      status.textContent = "沒有符合目前搜尋範圍的結果。";
      status.hidden = false;
      if (focusAfter) status.focus();
    }

    function renderFallback() {
      results.replaceChildren();
      const paragraph = document.createElement("p");
      paragraph.className = "search-empty-guidance";
      paragraph.append(document.createTextNode("搜尋索引目前無法載入。您仍可"));
      const catalog = document.createElement("a");
      catalog.href = new URL("versions/114/index.html", siteRoot).href;
      catalog.textContent = "查看原書完整目錄";
      const pdf = document.createElement("a");
      pdf.href = new URL("downloads/policy-agri-loan-handbook-114.pdf", siteRoot).href;
      pdf.textContent = "開啟完整 PDF";
      paragraph.append(catalog, document.createTextNode("或"), pdf, document.createTextNode("。"));
      results.append(paragraph);
      more.hidden = true;
      status.textContent = "搜尋索引目前無法載入。";
      status.hidden = false;
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
        status.hidden = false;
        if (focusAfter) status.focus();
        return;
      }
      if (validation.empty) {
        state.allRanked = [];
        state.ranked = [];
        state.shown = 0;
        results.replaceChildren();
        more.hidden = true;
        status.textContent = "";
        status.hidden = true;
        return;
      }

      status.textContent = "搜尋中…";
      status.hidden = false;
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
        setScope(button.dataset.scope === "chapter" ? "context" : "all", true);
      })
    );
    panel.__manualSearch = { run, input, state, setScope };
  }

  document.querySelectorAll("[data-search]").forEach(attach);
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-keyword], button[data-query]");
    if (!button) return;
    const selector = button.dataset.searchTarget || "#home-search";
    const panel = document.querySelector(selector)?.closest("[data-search]") ||
      button.closest("main")?.querySelector("[data-search]") ||
      document.querySelector("[data-search]");
    const api = panel?.__manualSearch;
    if (!api) return;
    await api.setScope(button.dataset.searchScope || "all");
    api.input.value = button.dataset.query || button.dataset.keyword || "";
    const bounds = panel.getBoundingClientRect();
    const fullyVisible = bounds.top >= 0 && bounds.bottom <= window.innerHeight;
    if (!fullyVisible) {
      panel.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start"
      });
    }
    await api.run(true);
  });
})();
