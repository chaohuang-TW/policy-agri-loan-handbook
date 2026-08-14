(function () {
  "use strict";

  function normalize(value) {
    return String(value || "")
      .toLocaleLowerCase("zh-Hant")
      .replace(/\s+/g, "")
      .replace(/[，。；：！？、（）「」『』【】《》〈〉／/%％﹪﹖?.,:;()\[\]{}]/g, "");
  }

  function digits(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function readData(root) {
    const script = root.querySelector("script[data-lookup-data]");
    if (!script) return [];
    try {
      const data = JSON.parse(script.textContent || "[]");
      return Array.isArray(data) ? data : [];
    } catch (_error) {
      return [];
    }
  }

  function interpretationScore(record, query) {
    const q = normalize(query);
    if (!q) return 0;
    const canonicalDigits = digits(record.canonicalDocumentNumber);
    const documentDigits = digits(record.documentNumber);
    const queryDigits = digits(query);
    const title = normalize(record.title);
    const sourceHeader = normalize(record.sourceHeader);
    const program = normalize(record.loanProgram);
    const body = normalize(record.title + " " + record.sourceHeader + " " + record.loanProgram);
    if (queryDigits.length >= 4 && queryDigits === canonicalDigits) return 100000;
    if (queryDigits.length >= 4 && queryDigits === documentDigits) return 90000;
    if (q === title) return 80000;
    if (title.includes(q)) return 70000;
    if (program.includes(q)) return 50000;
    if (sourceHeader.includes(q)) return 40000;
    if (body.includes(q)) return 30000;
    const terms = q.split(/\s+/).filter(Boolean);
    const matched = terms.filter((term) => body.includes(term));
    return matched.length === terms.length ? 10000 + matched.length * 100 : 0;
  }

  function faqScore(record, query) {
    const q = normalize(query);
    if (!q) return 0;
    const question = normalize(record.question);
    const body = normalize((record.question || "") + " " + (record.answerText || ""));
    if (question.includes(q)) return 60000;
    if (body.includes(q)) return 40000;
    return 0;
  }

  function lookupKey(record) {
    return record.lookupKey || record.id;
  }

  function updateUrl(state, mode) {
    const params = new URLSearchParams();
    if (state.query) params.set("q", state.query);
    if (state.group) params.set("group", state.group);
    if (state.program) params.set("program", state.program);
    if (state.year) params.set("year", state.year);
    const next = `${window.location.pathname}${params.toString() ? `?${params}` : ""}`;
    if (mode === "replace") window.history.replaceState(null, "", next);
    else window.history.pushState(null, "", next);
  }

  function attach(root) {
    const kind = root.dataset.referenceLookup;
    const form = root.querySelector("[data-lookup-form]");
    const input = root.querySelector("input[type=search]");
    const status = root.querySelector("[data-lookup-status]");
    const resultsRoot = kind === "faq"
      ? (root.parentElement.querySelector("[data-lookup-results]") || document.querySelector("[data-lookup-results]"))
      : root.parentElement;
    const records = readData(root);
    if (!form || !input || !status || !resultsRoot || !records.length) {
      if (status) status.textContent = "目前沒有可供查閱的來源索引。";
      return;
    }
    const cards = [...(kind === "faq"
      ? resultsRoot.querySelectorAll("[data-lookup-result]")
      : resultsRoot.querySelectorAll(".interpretation-lookup-result"))];
    const state = {query: "", group: "", program: "", year: ""};
    const groupButtons = [...root.querySelectorAll("[data-lookup-group-filter]")];
    const programSelect = root.querySelector("[data-lookup-program]");
    const yearSelect = root.querySelector("[data-lookup-year]");

    function score(record) {
      return kind === "faq" ? faqScore(record, state.query) : interpretationScore(record, state.query);
    }

    function matches(record) {
      if (kind === "faq" && state.group && record.faqGroupId !== state.group) return false;
      if (kind === "interpretations" && state.program && record.programSlug !== state.program) return false;
      if (kind === "interpretations" && state.year && record.year !== state.year) return false;
      return !state.query || score(record) > 0;
    }

    function render() {
      const ranked = records
        .map((record, index) => ({record, index, score: score(record)}))
        .filter(({record}) => matches(record))
        .sort((a, b) => b.score - a.score || a.index - b.index);
      const visible = new Set(ranked.map(({record}) => lookupKey(record)));
      const cardById = new Map(cards.map((card) => [card.dataset.lookupKey || card.dataset.lookupId, card]));
      if (kind === "faq") {
        ranked.forEach(({record}) => resultsRoot.append(cardById.get(lookupKey(record))));
      } else {
        const groups = [...resultsRoot.querySelectorAll(".lookup-group")];
        groups.forEach((group) => {
          const groupCards = [...group.querySelectorAll("[data-lookup-result]")];
          const ordered = ranked.filter(({record}) => groupCards.some((card) => (card.dataset.lookupKey || card.dataset.lookupId) === lookupKey(record)));
          const groupRoot = group.querySelector(".lookup-group-results");
          ordered.forEach(({record}) => groupRoot.append(cardById.get(lookupKey(record))));
          group.hidden = !ordered.length;
        });
      }
      cards.forEach((card) => {
        card.hidden = !visible.has(card.dataset.lookupKey || card.dataset.lookupId);
      });
      if (!ranked.length) {
        status.textContent = state.query ? "目前找不到符合條件的114年度手冊底本資料。" : "目前沒有符合篩選條件的資料。";
      } else {
        status.textContent = `找到 ${ranked.length} 筆${kind === "faq" ? "FAQ" : "函釋"}。`;
      }
      groupButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.lookupGroupFilter === state.group)));
    }

    function readUrl() {
      const params = new URLSearchParams(window.location.search);
      state.query = params.get("q") || "";
      state.group = kind === "faq" ? params.get("group") || "" : "";
      state.program = kind === "interpretations" ? params.get("program") || "" : "";
      state.year = kind === "interpretations" ? params.get("year") || "" : "";
      input.value = state.query;
      if (programSelect) programSelect.value = [...programSelect.options].some((option) => option.value === state.program) ? state.program : "";
      if (yearSelect) yearSelect.value = [...yearSelect.options].some((option) => option.value === state.year) ? state.year : "";
      if (state.group && !groupButtons.some((button) => button.dataset.lookupGroupFilter === state.group)) state.group = "";
      render();
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      state.query = input.value.trim();
      updateUrl(state);
      render();
    });
    form.addEventListener("reset", () => {
      window.setTimeout(() => {
        state.query = "";
        state.group = "";
        state.program = "";
        state.year = "";
        updateUrl(state);
        if (programSelect) programSelect.value = "";
        if (yearSelect) yearSelect.value = "";
        render();
        input.focus();
      }, 0);
    });
    groupButtons.forEach((button) => button.addEventListener("click", () => {
      state.group = button.dataset.lookupGroupFilter || "";
      updateUrl(state);
      render();
    }));
    programSelect?.addEventListener("change", () => {
      state.program = programSelect.value;
      updateUrl(state);
      render();
    });
    yearSelect?.addEventListener("change", () => {
      state.year = yearSelect.value;
      updateUrl(state);
      render();
    });
    window.addEventListener("popstate", readUrl);
    readUrl();
  }

  document.querySelectorAll("[data-reference-lookup]").forEach(attach);
})();
