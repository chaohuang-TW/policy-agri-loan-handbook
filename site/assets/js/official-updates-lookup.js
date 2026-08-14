(function () {
  "use strict";

  function normalizeText(value) {
    return String(value || "")
      .toLocaleLowerCase("zh-Hant")
      .replace(/\s+/g, "")
      .replace(/[，。；：！？、（）「」『』【】《》〈〉／/%％﹪﹖?.,:;()\[\]{}]/g, "");
  }

  function normalizeOfficialDocumentNumber(value) {
    return normalizeText(value)
      .replace(/字第/g, "")
      .replace(/號/g, "");
  }

  function dateValue(record) {
    return record.publishedDate || record.effectiveDate || record.versionDate || "";
  }

  function documentQuery(value) {
    const normalized = normalizeOfficialDocumentNumber(value);
    return /\d{6,}/.test(normalized) && normalized.length >= 6 ? normalized : "";
  }

  function score(record, query) {
    const q = normalizeText(query);
    if (!q) return 0;
    if (/^\d+$/.test(q) && q.length < 6) return 0;
    const doc = normalizeOfficialDocumentNumber(record.documentNumber);
    const docQuery = documentQuery(query);
    const title = normalizeText(record.officialTitle);
    const programs = normalizeText((record.relatedLoanTitles || []).join(" "));
    const sections = normalizeText((record.relatedSectionTitles || []).join(" "));
    const body = normalizeText([
      record.officialTitle,
      record.documentNumber,
      record.officialAgency,
      record.sourceTypeLabel,
      record.publishedDate,
      record.effectiveDate,
      record.versionDate,
      record.relationEvidence,
      ...(record.relatedLoanTitles || []),
      ...(record.relatedSectionTitles || [])
    ].join(" "));
    if (docQuery && docQuery === doc) return 100000;
    if (q === title) return 90000;
    if (title.includes(q)) return 80000;
    if (programs.includes(q)) return 70000;
    if (sections.includes(q)) return 65000;
    if (body.includes(q)) return 50000;
    const terms = q.split(/\s+/).filter(Boolean);
    return terms.length && terms.every((term) => body.includes(term)) ? 30000 + terms.length : 0;
  }

  function sortRecords(records, query) {
    return records
      .map((record, index) => ({record, index, score: score(record, query)}))
      .filter(({score: value}) => !query || value > 0)
      .sort((a, b) => b.score - a.score || dateValue(b.record).localeCompare(dateValue(a.record)) || String(a.record.id).localeCompare(String(b.record.id)) || a.index - b.index)
      .map(({record}) => record);
  }

  function updateUrl(state, mode) {
    const params = new URLSearchParams();
    if (state.query) params.set("q", state.query);
    if (state.program) params.set("program", state.program);
    if (state.type) params.set("type", state.type);
    if (state.year) params.set("year", state.year);
    if (state.relation) params.set("relation", state.relation);
    const next = `${window.location.pathname}${params.toString() ? `?${params}` : ""}`;
    if (mode === "replace") window.history.replaceState(null, "", next);
    else window.history.pushState(null, "", next);
  }

  function readData(root) {
    const script = root.querySelector("script[data-official-updates-data]");
    if (!script) return [];
    try {
      const data = JSON.parse(script.textContent || "[]");
      return Array.isArray(data) ? data : [];
    } catch (_error) {
      return [];
    }
  }

  function attach(root) {
    const form = root.querySelector("[data-official-updates-form]");
    const input = root.querySelector("input[name=q]");
    const status = root.querySelector("[data-official-update-status]");
    const legacyStatus = root.querySelector(".update-filter-status");
    const cards = [...root.querySelectorAll("[data-official-update-result]")];
    const records = readData(root);
    const controls = {
      program: root.querySelector("select[name=program]"),
      type: root.querySelector("select[name=type]"),
      year: root.querySelector("select[name=year]"),
      relation: root.querySelector("select[name=relation]")
    };
    if (!form || !input || !status || !records.length || !cards.length) return;
    const state = {query: "", program: "", type: "", year: "", relation: ""};

    function validValue(name, value) {
      const control = controls[name];
      return control && [...control.options].some((option) => option.value === value) ? value : "";
    }

    function render() {
      const filtered = sortRecords(records, state.query).filter((record) => {
        const loans = record.relatedLoanIds || [];
        const sections = record.relatedSectionIds || [];
        return (!state.program || loans.includes(state.program))
          && (!state.type || record.sourceType === state.type)
          && (!state.year || record.lookupYear === state.year)
          && (!state.relation || loans.includes(state.relation) || sections.includes(state.relation));
      });
      const visible = new Set(filtered.map((record) => record.id));
      const cardById = new Map(cards.map((card) => [card.dataset.officialUpdateId, card]));
      filtered.forEach((record) => root.querySelector(".official-update-list").append(cardById.get(record.id)));
      cards.forEach((card) => { card.hidden = !visible.has(card.dataset.officialUpdateId); });
      status.textContent = `目前顯示 ${filtered.length} 筆官方更新`;
      if (legacyStatus) legacyStatus.textContent = `顯示 ${filtered.length} 筆官方更新`;
      ["program", "type", "year", "relation"].forEach((name) => {
        if (controls[name]) controls[name].value = state[name];
      });
    }

    function readUrl() {
      const params = new URLSearchParams(window.location.search);
      state.query = params.get("q") || "";
      state.program = validValue("program", params.get("program") || "");
      state.type = validValue("type", params.get("type") || "");
      state.year = validValue("year", params.get("year") || "");
      state.relation = validValue("relation", params.get("relation") || "");
      input.value = state.query;
      render();
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      state.query = input.value.trim();
      updateUrl(state);
      render();
    });
    form.addEventListener("change", (event) => {
      const name = event.target.name;
      if (!(name in state)) return;
      state[name] = event.target.value;
      updateUrl(state);
      render();
    });
    form.addEventListener("reset", () => {
      window.setTimeout(() => {
        state.query = "";
        state.program = "";
        state.type = "";
        state.year = "";
        state.relation = "";
        updateUrl(state);
        render();
        input.focus();
      }, 0);
    });
    window.addEventListener("popstate", readUrl);
    readUrl();
  }

  window.OfficialUpdatesLookup = {normalizeOfficialDocumentNumber, sortRecords};
  document.querySelectorAll(".updates-index[data-official-updates-lookup]").forEach(attach);
})();
