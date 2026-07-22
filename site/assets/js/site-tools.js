(function () {
  "use strict";
  const dialog = document.getElementById("manual-search-dialog");
  const page = document.body;
  const opener = document.querySelector("[data-open-search]");
  const tools = document.querySelector(".floating-tools");
  const searchPanel = dialog?.querySelector("[data-search]");
  let lastTrigger = null;
  function openSearch(trigger) { if (!dialog) return; lastTrigger = trigger || opener; if (!dialog.open) dialog.showModal(); searchPanel?.querySelector("input[type=search]")?.focus(); }
  function closeSearch() { if (!dialog) return; dialog.close(); window.setTimeout(() => lastTrigger?.focus(), 0); }
  opener?.addEventListener("click", () => openSearch(opener));
  dialog?.querySelector("[data-close-search]")?.addEventListener("click", closeSearch);
  dialog?.addEventListener("click", (event) => { if (event.target === dialog) closeSearch(); });
  document.addEventListener("keydown", (event) => { if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "k") return; const target = event.target; if (target.matches?.("input, textarea, select, [contenteditable=true]") && !dialog?.open) return; event.preventDefault(); if (dialog?.open) searchPanel?.querySelector("input[type=search]")?.focus(); else openSearch(opener); });
  dialog?.addEventListener("keydown", (event) => { if (event.key === "Escape") { event.preventDefault(); closeSearch(); } });
  const topButton = document.querySelector("[data-back-to-top]");
  const printButton = document.querySelector("[data-print-section]");
  if (printButton && page.dataset.printable !== "true") printButton.hidden = true;
  const sentinel = document.querySelector(".top-sentinel");
  if (topButton && sentinel && "IntersectionObserver" in window) new IntersectionObserver(([entry]) => { topButton.hidden = entry.isIntersecting; }).observe(sentinel);
  topButton?.addEventListener("click", () => { document.documentElement.scrollTo({top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"}); topButton.focus(); });
  document.querySelector("[data-print-section]")?.addEventListener("click", () => window.print());
  if (tools) tools.hidden = false;
})();
