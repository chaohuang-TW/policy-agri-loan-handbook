(function () {
  "use strict";

  const TYPES = ["原文頁面", "貸款索引", "函釋", "常見問答", "書表附件", "附錄附件"];
  const TYPE_LABELS = {"書表附件": "書表"};
  const LIMIT = 20;
  const WEIGHTS = {exactNumber: 1200, exactTitle: 1000, phraseTitle: 650, title: 180, heading: 320, breadcrumb: 100, body: 45, conceptTitle: 110, conceptBody: 25, allTerms: 220, proximity: 120, loanTitle: 500, formTitle: 500};
  const root = document.body;
  const siteRoot = new URL(root.dataset.siteRoot || "./", document.baseURI);
  const dataUrl = (name) => new URL(`assets/data/${name}`, siteRoot);
  let dataPromise;

  function normalizeLineSpaces(value) { return String(value || "").replace(/\s+/g, " ").trim(); }
  function normalize(value) { return normalizeLineSpaces(value).normalize("NFKC").toLocaleLowerCase("zh-Hant"); }
  function tokenizeQuery(value) { return [...new Set(normalize(value).split(/[\s,，、;；]+/).filter(Boolean))]; }
  function loadData() {
    if (!dataPromise) {
      dataPromise = Promise.all(["search-index.json", "search-concepts.json", "search-intents.json"].map((name) => fetch(dataUrl(name)).then((r) => { if (!r.ok) throw new Error("搜尋資料載入失敗"); return r.json(); })))
        .then(([records, concepts, intents]) => ({records, concepts, intents}));
    }
    return dataPromise;
  }
  function activeIntents(query, intents) {
    const q = normalize(query);
    return intents.filter((intent) => intent.triggers.some((term) => q.includes(normalize(term))));
  }
  function prepareConcepts(query, concepts) {
    const tokens = tokenizeQuery(query);
    return concepts.filter((concept) => concept.terms.some((term) => tokens.some((token) => normalize(term).includes(token) || token.includes(normalize(term)))))
      .flatMap((concept) => concept.terms.map(normalize));
  }
  function fieldMatches(record, terms) {
    const fields = {title: normalize(record.title), headings: normalize((record.headings || []).join(" ")), breadcrumb: normalize((record.breadcrumb || []).join(" ")), body: normalize(record.text)};
    return {fields, title: terms.filter((term) => fields.title.includes(term)), headings: terms.filter((term) => fields.headings.includes(term)), breadcrumb: terms.filter((term) => fields.breadcrumb.includes(term)), body: terms.filter((term) => fields.body.includes(term))};
  }
  function proximityScore(text, terms) {
    const source = normalize(text); const positions = terms.map((term) => source.indexOf(term)).filter((position) => position >= 0);
    if (positions.length < 2) return 0;
    const distance = Math.max(...positions) - Math.min(...positions);
    return distance <= 180 ? Math.max(0, WEIGHTS.proximity - Math.floor(distance / 3)) : 0;
  }
  function scoreRecord(record, query, concepts, intents) {
    const terms = tokenizeQuery(query); const matches = fieldMatches(record, terms); const q = normalize(query); let score = 0;
    score += matches.title.length * WEIGHTS.title + matches.headings.length * WEIGHTS.heading + matches.breadcrumb.length * WEIGHTS.breadcrumb + matches.body.length * WEIGHTS.body;
    if (matches.title.length === terms.length && terms.length) score += WEIGHTS.exactTitle;
    if (matches.title.length && matches.title.join(" ") === q) score += WEIGHTS.phraseTitle;
    if (q.length >= 8 && normalize(record.text).includes(q)) score += WEIGHTS.phraseTitle;
    if (/^(農授金字|農金字|農金三字)/.test(q) || /農授金字第\d+號/.test(q)) score += normalize(record.text).includes(q) ? WEIGHTS.exactNumber : 0;
    const conceptTerms = prepareConcepts(query, concepts).filter((term) => !terms.includes(term));
    score += conceptTerms.filter((term) => normalize(record.title).includes(term)).length * WEIGHTS.conceptTitle;
    score += conceptTerms.filter((term) => normalize(record.text).includes(term)).length * WEIGHTS.conceptBody;
    if (terms.length > 1 && matches.body.length === terms.length) score += WEIGHTS.allTerms;
    score += proximityScore(record.text, terms);
    if (record.type === "貸款索引" && matches.title.length) score += WEIGHTS.loanTitle;
    if (record.type === "書表附件" && matches.title.length) score += WEIGHTS.formTitle;
    for (const intent of activeIntents(query, intents)) if (intent.preferredTypes.includes(record.type)) score += intent.boost;
    return {score, terms: terms.concat(conceptTerms), matchedTerms: matches.body.concat(matches.title, matches.headings)};
  }
  function diversifyResults(scored) {
    const counts = new Map();
    return scored.map((item) => { const count = counts.get(item.record.scope) || 0; counts.set(item.record.scope, count + 1); return {...item, score: item.score - (count > 1 ? (count - 1) * 18 : 0)}; })
      .sort((a, b) => b.score - a.score || Number(b.record.pdfPage || 0) - Number(a.record.pdfPage || 0) || a.record.id.localeCompare(b.record.id));
  }
  function filterByType(items, type) { return type === "all" ? items : items.filter((item) => item.record.type === type || (type === "書表附件" && item.record.type === "書表附件")); }
  function filterByScope(items, scope) { return scope && scope !== "all" ? items.filter((item) => item.record.scope === scope || (scope.startsWith("loan:") && item.record.scope === scope)) : items; }
  function searchRecords(records, query, concepts, intents, type = "all", scope = "all") {
    const q = normalize(query); if (!q) return [];
    const ranked = diversifyResults(records.map((record, index) => ({record, index, ...scoreRecord(record, q, concepts, intents)})).filter((item) => item.score > 0));
    return filterByScope(filterByType(ranked, type), scope);
  }
  function createSnippet(original, terms) {
    const text = String(original || ""); const lower = normalize(text); const positions = terms.map((term) => lower.indexOf(normalize(term))).filter((n) => n >= 0); const position = positions.length ? Math.min(...positions) : 0;
    const start = Math.max(0, position - 65); const end = Math.min(text.length, position + 105); return {text: text.slice(start, end), offset: start};
  }
  function appendHighlighted(parent, text, terms) {
    const source = String(text || ""); const matches = []; const lowered = normalize(source);
    terms.sort((a, b) => b.length - a.length).forEach((term) => { let at = lowered.indexOf(normalize(term)); let guard = 0; while (at >= 0 && guard++ < 8) { matches.push([at, at + term.length]); at = lowered.indexOf(normalize(term), at + term.length); } });
    matches.sort((a, b) => a[0] - b[0]); let cursor = 0;
    for (const [start, end] of matches) { if (start < cursor) continue; parent.append(document.createTextNode(source.slice(cursor, start))); const mark = document.createElement("mark"); mark.className = "search-highlight"; mark.textContent = source.slice(start, end); parent.append(mark); cursor = end; }
    parent.append(document.createTextNode(source.slice(cursor)));
  }
  function createResult(item) {
    const record = item.record; const article = document.createElement("article"); article.className = "search-result";
    const h3 = document.createElement("h3"); const link = document.createElement("a"); link.href = new URL(record.url, siteRoot).href; link.textContent = record.title; h3.append(link); article.append(h3);
    const meta = document.createElement("p"); meta.className = "result-match-meta"; meta.textContent = `${TYPE_LABELS[record.type] || record.type}｜${(record.breadcrumb || []).join(" › ")}`; article.append(meta);
    const snippet = createSnippet(record.text, item.terms); const p = document.createElement("p"); p.className = "result-snippet"; if (snippet.offset) p.append(document.createTextNode("…")); appendHighlighted(p, snippet.text, item.terms); if (snippet.offset + snippet.text.length < record.text.length) p.append(document.createTextNode("…")); article.append(p);
    const pages = document.createElement("p"); pages.className = "result-pages"; pages.textContent = `版本：${record.version}｜手冊頁：${record.printedPage || "目錄"}｜PDF頁：${record.pdfPage}／359`; article.append(pages);
    if (record.documentNumber || record.date || record.loanProgram) { const extra = document.createElement("p"); extra.className = "result-pages"; extra.textContent = [record.date, record.documentNumber, record.loanProgram].filter(Boolean).join("｜"); article.append(extra); }
    return article;
  }
  function renderTypeFilters(panel, ranked, activeType, onChange) {
    const wrap = panel.querySelector(".search-filters"); wrap.replaceChildren(); [["all", "全部"], ...TYPES.map((type) => [type, TYPE_LABELS[type] || type])].forEach(([value, label]) => { const button = document.createElement("button"); button.type = "button"; button.className = "search-filter-button"; button.textContent = `${label} ${value === "all" ? ranked.length : ranked.filter((item) => item.record.type === value).length}`; button.setAttribute("aria-pressed", String(value === activeType)); button.addEventListener("click", () => onChange(value)); wrap.append(button); });
  }
  function attach(panel) {
    const form = panel.querySelector("form"); const input = panel.querySelector("input[type=search]"); const status = panel.querySelector(".search-status"); const results = panel.querySelector(".search-results"); const more = panel.querySelector(".search-more"); const scopeOptions = panel.querySelector(".search-scope-options"); let timer; let state = {ranked: [], shown: 0, type: "all", scope: "all"};
    const pageScope = root.dataset.searchScope || "";
    if (pageScope && scopeOptions) { scopeOptions.hidden = false; scopeOptions.querySelector("[data-scope=chapter]").textContent = pageScope.startsWith("loan:") ? "本貸款" : "本章"; }
    function render() { results.replaceChildren(...state.ranked.filter((item) => state.type === "all" || item.record.type === state.type).slice(0, state.shown).map(createResult)); const count = state.ranked.filter((item) => state.type === "all" || item.record.type === state.type).length; status.textContent = `找到 ${count} 筆結果，目前顯示 ${Math.min(state.shown, count)} 筆。`; more.hidden = state.shown >= count; renderTypeFilters(panel, state.ranked, state.type, (type) => { state.type = type; state.shown = LIMIT; render(); }); }
    async function run() { const query = normalize(input.value); if (!query) { state.ranked = []; state.shown = 0; results.replaceChildren(); more.hidden = true; status.textContent = "請輸入搜尋文字。"; return; } status.textContent = "搜尋中…"; try { const data = await loadData(); state.ranked = searchRecords(data.records, query, data.concepts, data.intents, "all", state.scope); state.type = "all"; state.shown = LIMIT; render(); } catch (error) { state.ranked = []; results.replaceChildren(); more.hidden = true; status.textContent = "搜尋索引目前無法載入；請查看完整目錄或開啟完整PDF。"; } }
    form.addEventListener("submit", (event) => { event.preventDefault(); window.clearTimeout(timer); run(); }); input.addEventListener("input", () => { window.clearTimeout(timer); timer = window.setTimeout(run, 250); }); more.addEventListener("click", () => { state.shown += LIMIT; render(); more.focus(); });
    scopeOptions?.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => { scopeOptions.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b === button))); state.scope = button.dataset.scope === "chapter" ? pageScope : "all"; if (input.value.trim()) run(); }));
    panel.__manualSearch = {run, input, state};
    panel.querySelectorAll("[data-keyword]").forEach((button) => button.addEventListener("click", () => { input.value = button.dataset.keyword; input.focus(); run(); }));
  }
  function init() { document.querySelectorAll("[data-search]").forEach(attach); }
  globalThis.ManualSearch = {normalize, tokenizeQuery, prepareConcepts, scoreRecord, searchRecords, createSnippet, loadData};
  init();
})();
