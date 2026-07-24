const {test, expect} = require("@playwright/test");

const paths = {
  home: "/",
  page: "/versions/114/pages/page-003.html",
  loan: "/loans/young-farmer-loan/",
  section: "/versions/114/sections/loan-programs/",
  disaster: "/versions/114/sections/natural-disaster-rules/"
};

function observeRuntime(page) {
  const evidence = {consoleErrors: [], pageErrors: [], badResponses: [], external: []};
  page.on("console", (message) => {
    if (message.type() === "error") evidence.consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => evidence.pageErrors.push(String(error)));
  page.on("response", (response) => {
    if (response.status() >= 400) evidence.badResponses.push(`${response.status()} ${response.url()}`);
  });
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (!["127.0.0.1", "localhost"].includes(url.hostname)) evidence.external.push(request.url());
  });
  return evidence;
}

async function openDialog(page) {
  await page.locator("[data-open-search]").click();
  await expect(page.locator("#manual-search-dialog")).toHaveJSProperty("open", true);
  await expect(page.locator("#dialog-site-search")).toBeFocused();
}

async function searchDialog(page, query) {
  const initialized = await page.evaluate(() => ({
    core: typeof window.ManualSearchCore,
    panels: [...document.querySelectorAll("[data-search]")].map((panel) => Boolean(panel.__manualSearch))
  }));
  expect(initialized.core).toBe("object");
  expect(initialized.panels.length).toBeGreaterThan(0);
  expect(initialized.panels.every(Boolean)).toBe(true);
  const input = page.locator("#dialog-site-search");
  await input.fill(query);
  await page.locator("#manual-search-dialog form button[type=submit]").click();
  await expect(page.locator("#manual-search-dialog .search-status")).toContainText(/找到|沒有|過長|條件過多/);
}

test("dialog keyboard, backdrop, Escape and focus restoration", async ({page}) => {
  const runtime = observeRuntime(page);
  await page.goto(paths.home);
  await expect(page.locator("h1")).toHaveCount(1);
  const opener = page.locator("[data-open-search]");
  await openDialog(page);
  await page.locator("#manual-search-dialog").press("Escape");
  await expect(page.locator("#manual-search-dialog")).not.toHaveAttribute("open");
  await expect(opener).toBeFocused();

  await page.keyboard.press("Control+k");
  await expect(page.locator("#manual-search-dialog")).toHaveJSProperty("open", true);
  await page.locator("[data-close-search]").click();
  await page.evaluate(() => document.dispatchEvent(new KeyboardEvent("keydown", {
    key: "k", metaKey: true, bubbles: true
  })));
  await expect(page.locator("#manual-search-dialog")).toHaveJSProperty("open", true);
  await page.evaluate(() => document.querySelector("#manual-search-dialog").click());
  await expect(page.locator("#manual-search-dialog")).not.toHaveAttribute("open");
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});

test("search type filter, more results, overlong input and injection safety", async ({page}) => {
  const runtime = observeRuntime(page);
  await page.goto(paths.home);
  await openDialog(page);
  await searchDialog(page, "申請書");
  await expect(page.locator("#manual-search-dialog .search-result").first()).toBeVisible();
  const formFilter = page.locator("#manual-search-dialog .search-filter-button", {hasText: "書表"});
  await formFilter.click();
  await expect(formFilter).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#manual-search-dialog .search-result")).toHaveCount(20);
  await page.locator("#manual-search-dialog .search-more").click();
  expect(await page.locator("#manual-search-dialog .search-result").count()).toBeGreaterThan(20);

  const input = page.locator("#dialog-site-search");
  await input.evaluate((element) => {
    element.removeAttribute("maxlength");
    element.value = "字".repeat(257);
    element.dispatchEvent(new Event("input", {bubbles: true}));
  });
  await expect(page.locator("#manual-search-dialog .search-status")).toContainText("搜尋文字過長");
  await searchDialog(page, '<img src=x onerror="alert(1)"><script>alert(1)</script><svg></svg>');
  await expect(page.locator("#manual-search-dialog .search-results img")).toHaveCount(0);
  await expect(page.locator("#manual-search-dialog .search-results script")).toHaveCount(0);
  await expect(page.locator("#manual-search-dialog .search-results svg")).toHaveCount(0);
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});

for (const [name, url] of [
  ["loan-programs", paths.section],
  ["natural-disaster-rules", paths.disaster]
]) {
  test(`${name} chapter scope returns only declared source scopes`, async ({page}) => {
    const runtime = observeRuntime(page);
    await page.goto(url);
    const scopes = (await page.locator("body").getAttribute("data-search-scopes")).split(",");
    await openDialog(page);
    await page.locator("[data-scope=chapter]").click();
    await searchDialog(page, "貸款");
    await expect(page.locator("#manual-search-dialog .search-result").first()).toBeVisible();
    const urls = await page.locator("#manual-search-dialog .search-result a").evaluateAll(
      (links) => links.map((link) => link.getAttribute("href"))
    );
    expect(urls.length).toBeGreaterThan(0);
    const index = await page.evaluate(() => window.fetch("/assets/data/search-index.json").then((r) => r.json()));
    const resultPaths = new Set(urls.map((url) => new URL(url).pathname.replace(/^\//, "")));
    const sourceResults = index.filter((record) =>
      record.type === "原文頁面" && resultPaths.has(record.url.split("#")[0])
    );
    expect(sourceResults.every((record) => scopes.includes(record.scope))).toBe(true);
    expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
  });
}

test("loan scope, empty chapter fallback and post-search focus", async ({page}) => {
  const runtime = observeRuntime(page);
  await page.goto(paths.loan);
  await openDialog(page);
  await page.locator("[data-scope=chapter]").click();
  await searchDialog(page, "青壯年農民");
  const text = await page.locator("#manual-search-dialog .search-result").allTextContents();
  expect(text.length).toBeGreaterThan(0);
  expect(text.join("\n")).toContain("青壯年農民");

  await page.goto(paths.section);
  await openDialog(page);
  await page.locator("[data-scope=chapter]").click();
  await searchDialog(page, "ZZZ無此詞天然災害");
  await expect(page.locator(".search-search-all")).toBeVisible();
  await page.locator(".search-search-all").click();
  await expect(page.locator("[data-scope=all]")).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#dialog-site-search")).not.toBeFocused();
  const focused = await page.evaluate(() => document.activeElement?.matches(".search-status, .search-result a"));
  expect(focused).toBe(true);
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});

test("back to top and print labels/calls", async ({page}) => {
  for (const [url, label] of [
    [paths.page, "列印本頁"],
    [paths.loan, "列印本貸款"],
    [paths.section, "列印本章"]
  ]) {
    await page.goto(url);
    await expect(page.locator("[data-print-section]")).toHaveAttribute("aria-label", label);
    await page.evaluate(() => {
      window.__printCalled = false;
      window.print = () => { window.__printCalled = true; };
    });
    await page.locator("[data-print-section]").click();
    expect(await page.evaluate(() => window.__printCalled)).toBe(true);
  }
  await page.goto(paths.home);
  await expect(page.locator("[data-print-section]")).toBeHidden();
  await page.goto(paths.page);
  await page.evaluate(() => window.scrollTo(0, 649));
  await expect(page.locator("[data-back-to-top]")).toBeHidden();
  await page.evaluate(() => window.scrollTo(0, 700));
  await expect(page.locator("[data-back-to-top]")).toBeVisible();
  await page.locator("[data-back-to-top]").click();
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
});

for (const width of [390, 768, 1024, 1440]) {
  test(`${width}px has no horizontal or dialog overflow`, async ({page}) => {
    const runtime = observeRuntime(page);
    await page.setViewportSize({width, height: 900});
    for (const url of [paths.home, paths.page, paths.loan, paths.section, paths.disaster]) {
      await page.goto(url);
      const layout = await page.evaluate(() => ({
        documentWidth: document.documentElement.scrollWidth,
        viewportWidth: document.documentElement.clientWidth,
        h1: document.querySelectorAll("h1").length,
        duplicateIds: [...document.querySelectorAll("[id]")]
          .map((element) => element.id)
          .filter((id, index, values) => values.indexOf(id) !== index)
      }));
      expect(layout.documentWidth).toBeLessThanOrEqual(layout.viewportWidth);
      expect(layout.h1).toBe(1);
      expect(layout.duplicateIds).toEqual([]);
      await openDialog(page);
      const box = await page.locator("#manual-search-dialog").boundingBox();
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.y).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(width);
      expect(box.y + box.height).toBeLessThanOrEqual(900);
      await page.locator("[data-close-search]").click();
    }
    expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
  });
}

test("all HTML has one H1, unique IDs and no external runtime request", async ({page}) => {
  const runtime = observeRuntime(page);
  const sitemap = await (await page.request.get("/sitemap.xml")).text();
  const urls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) =>
    new URL(match[1]).pathname.replace(/^\/policy-agri-loan-handbook/, "") || "/"
  );
  expect(urls).toHaveLength(397);
  for (const url of urls) {
    await page.goto(url);
    await page.evaluate(() => Promise.all([...document.images].map((image) => {
      image.loading = "eager";
      if (image.complete) return Promise.resolve();
      return new Promise((resolve) => {
        image.addEventListener("load", resolve, {once: true});
        image.addEventListener("error", resolve, {once: true});
      });
    })));
    const result = await page.evaluate(() => {
      const ids = [...document.querySelectorAll("[id]")].map((element) => element.id);
      return {
        h1: document.querySelectorAll("h1").length,
        duplicates: ids.filter((id, index) => ids.indexOf(id) !== index),
        brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length
      };
    });
    expect(result).toEqual({h1: 1, duplicates: [], brokenImages: 0});
  }
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});
