(function () {
  "use strict";
  const dialog = document.getElementById("manual-search-dialog");
  const searchPanel = dialog?.querySelector("[data-search]");
  const menuToggle = document.querySelector("[data-menu-toggle]");
  const mobileMenu = document.getElementById("mobile-menu");
  let lastTrigger = null;

  function openSearch(trigger) {
    if (!dialog) return;
    lastTrigger = trigger || document.activeElement;
    if (!dialog.open) dialog.showModal();
    searchPanel?.querySelector("input[type=search]")?.focus();
  }
  function closeSearch() {
    if (!dialog) return;
    dialog.close();
    window.setTimeout(() => lastTrigger?.focus(), 0);
  }
  function closeMenu(returnFocus = false) {
    if (!mobileMenu || !menuToggle) return;
    mobileMenu.hidden = true;
    menuToggle.setAttribute("aria-expanded", "false");
    if (returnFocus) menuToggle.focus();
  }

  document.querySelectorAll("[data-open-search]").forEach((button) =>
    button.addEventListener("click", () => openSearch(button))
  );
  dialog?.querySelector("[data-close-search]")?.addEventListener("click", closeSearch);
  dialog?.addEventListener("click", (event) => {
    if (event.target === dialog) closeSearch();
  });
  menuToggle?.addEventListener("click", () => {
    const expanded = menuToggle.getAttribute("aria-expanded") === "true";
    mobileMenu.hidden = expanded;
    menuToggle.setAttribute("aria-expanded", String(!expanded));
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !mobileMenu?.hidden) {
      event.preventDefault();
      closeMenu(true);
      return;
    }
    if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "k") return;
    const target = event.target;
    if (target.matches?.("input, textarea, select, [contenteditable=true]") && !dialog?.open) return;
    event.preventDefault();
    if (dialog?.open) searchPanel?.querySelector("input[type=search]")?.focus();
    else openSearch(document.activeElement);
  });
  dialog?.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeSearch();
    }
  });

  const topButton = document.querySelector("[data-back-to-top]");
  const sentinel = document.querySelector(".top-sentinel");
  if (topButton && sentinel && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(([entry]) => {
      topButton.hidden = !(entry.boundingClientRect.top < 0);
    });
    observer.observe(sentinel);
  }
  topButton?.addEventListener("click", () => {
    document.documentElement.scrollTo({
      top: 0,
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"
    });
    topButton.focus();
  });
  document.querySelectorAll("[data-print-page]").forEach((button) =>
    button.addEventListener("click", () => window.print())
  );
  if (window.matchMedia("(min-width: 601px)").matches) {
    document.querySelectorAll(".search-filter-disclosure").forEach((details) => {
      details.open = true;
    });
  }

  const updateFilters = document.querySelector("[data-update-filters]");
  if (updateFilters) {
    const items = [...document.querySelectorAll(".updates-index .official-update-item")];
    const status = updateFilters.querySelector(".update-filter-status");
    const applyUpdateFilters = () => {
      const values = new FormData(updateFilters);
      const type = String(values.get("type") || "");
      const year = String(values.get("year") || "");
      const relation = String(values.get("relation") || "");
      let visible = 0;
      items.forEach((item) => {
        const match = (!type || item.dataset.updateType === type)
          && (!year || item.dataset.updateYear === year)
          && (!relation || item.dataset.updateRelations.split(" ").includes(relation));
        item.hidden = !match;
        if (match) visible += 1;
      });
      status.textContent = `顯示 ${visible} 筆官方更新`;
      const params = new URLSearchParams();
      if (type) params.set("type", type);
      if (year) params.set("year", year);
      if (relation) params.set("relation", relation);
      history.replaceState(null, "", `${location.pathname}${params.size ? `?${params}` : ""}`);
    };
    const params = new URLSearchParams(location.search);
    ["type", "year", "relation"].forEach((name) => {
      const control = updateFilters.elements.namedItem(name);
      if (control && [...control.options].some((option) => option.value === params.get(name))) {
        control.value = params.get(name);
      }
    });
    updateFilters.addEventListener("change", applyUpdateFilters);
    updateFilters.addEventListener("reset", () => window.setTimeout(applyUpdateFilters, 0));
    applyUpdateFilters();
  }
  const disasterFilters = document.querySelector("[data-disaster-filters]");
  if (disasterFilters) {
    const items = [...document.querySelectorAll(".disaster-announcement")];
    const status = disasterFilters.querySelector(".update-filter-status");
    const apply = () => {
      const values = new FormData(disasterFilters);
      const year = String(values.get("year") || "");
      const keyword = String(values.get("q") || "").trim().toLocaleLowerCase();
      let visible = 0;
      items.forEach((item) => {
        const match = (!year || item.dataset.disasterYear === year) && (!keyword || item.dataset.disasterSearch.toLocaleLowerCase().includes(keyword));
        item.hidden = !match;
        if (match) visible += 1;
      });
      status.textContent = `顯示 ${visible} 筆天然災害低利貸款公告`;
    };
    disasterFilters.addEventListener("input", apply);
    disasterFilters.addEventListener("change", apply);
    disasterFilters.addEventListener("reset", () => window.setTimeout(apply, 0));
    apply();
  }
})();
