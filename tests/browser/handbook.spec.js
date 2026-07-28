const {test, expect} = require("@playwright/test");
const appendixTitle = require("../../data/114/appendices.json")
  .find((item) => item.id.startsWith("appendix-")).title;

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
  await page.locator("[data-open-search]:visible").first().click();
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
  const opener = page.locator("[data-open-search]:visible").first();
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
    await page.locator("#manual-search-dialog [data-scope=chapter]").click();
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
  await page.locator("#manual-search-dialog [data-scope=chapter]").click();
  await searchDialog(page, "青壯年農民");
  const text = await page.locator("#manual-search-dialog .search-result").allTextContents();
  expect(text.length).toBeGreaterThan(0);
  expect(text.join("\n")).toContain("青壯年農民");

  await page.goto(paths.section);
  await openDialog(page);
  await page.locator("#manual-search-dialog [data-scope=chapter]").click();
  await searchDialog(page, "ZZZ無此詞天然災害");
  await expect(page.locator(".search-search-all")).toBeVisible();
  await page.locator(".search-search-all").click();
  await expect(page.locator("#manual-search-dialog [data-scope=all]")).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#dialog-site-search")).not.toBeFocused();
  const focused = await page.evaluate(() => document.activeElement?.matches(".search-status, .search-result a"));
  expect(focused).toBe(true);
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});

test("page action print and 900px back-to-top threshold", async ({page}) => {
  await page.goto(paths.page);
  await page.evaluate(() => {
    window.__printCalled = false;
    window.print = () => { window.__printCalled = true; };
  });
  await page.locator("[data-print-page]").click();
  expect(await page.evaluate(() => window.__printCalled)).toBe(true);
  await page.goto(paths.home);
  await expect(page.locator("[data-print-page]")).toHaveCount(0);
  await expect(page.locator(".floating-tools")).toHaveCount(0);
  await page.goto(paths.page);
  await page.evaluate(() => window.scrollTo(0, 899));
  await expect(page.locator("[data-back-to-top]")).toBeHidden();
  await page.evaluate(() => window.scrollTo(0, 950));
  await expect(page.locator("[data-back-to-top]")).toBeVisible();
  await page.locator("[data-back-to-top]").click();
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
});

test("homepage common queries and task shortcuts run immediately", async ({page}) => {
  const runtime = observeRuntime(page);
  await page.goto(paths.home);
  await expect(page.locator(".primary-entries .entry")).toHaveCount(4);
  await expect(page.locator(".popular button")).toHaveCount(8);
  for (const label of ["農機", "天然災害"]) {
    await page.locator(".popular button", {hasText: label}).click();
    await expect(page.locator("#home-search")).toHaveValue(label);
    await expect(page.locator(".hero .search-result").first()).toBeVisible();
  }
  await page.locator(".task-shortcuts button", {hasText: "期限與寬緩期"}).click();
  await expect(page.locator("#home-search")).toHaveValue("貸款期限 寬緩期");
  await expect(page.locator(".hero .search-result").first()).toBeVisible();
  await expect(page.locator(".hero .search-results [data-structured-answer]")).toHaveCount(0);
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});

test("390px mobile menu is closed, accessible and restores focus", async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await page.goto(paths.home);
  const menu = page.locator("#mobile-menu");
  const toggle = page.locator("[data-menu-toggle]");
  await expect(menu).toBeHidden();
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator("#home-search")).toBeInViewport();
  await toggle.click();
  await expect(menu).toBeVisible();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("Escape");
  await expect(menu).toBeHidden();
  await expect(toggle).toBeFocused();
  await expect(page.locator(".floating-tools")).toHaveCount(0);
});

test("semantic section hubs keep page lists secondary", async ({page}) => {
  for (const [url, expected] of [
    ["/versions/114/sections/agricultural-development-fund-rules/", null],
    ["/versions/114/sections/loan-programs/", 19],
    ["/versions/114/sections/natural-disaster-rules/", null],
    ["/versions/114/sections/amendment-faq/", null],
    ["/versions/114/sections/attachments/", null]
  ]) {
    await page.goto(url);
    await expect(page.getByText("在本章查規定", {exact: true})).toBeVisible();
    const details = page.locator(".source-page-list");
    await expect(details).not.toHaveAttribute("open");
    await expect(page.locator("text=本篇頁面")).toHaveCount(0);
    if (expected) await expect(page.locator(".hub-primary .loan-grid li")).toHaveCount(expected);
    await details.locator("summary").click();
    await expect(details.locator("a").first()).toBeVisible();
  }
});

for (const loan of ["young-farmer-loan", "farm-machinery-loan", "natural-disaster-low-interest-loan"]) {
  test(`${loan} is a scoped loan work page`, async ({page}) => {
    await page.goto(`/loans/${loan}/`);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.getByText("在本貸款中搜尋", {exact: true})).toBeVisible();
    await expect(page.getByRole("heading", {name: "貸款原文", exact: true})).toBeVisible();
    await expect(page.getByRole("heading", {name: "相關函釋", exact: true})).toBeVisible();
    await expect(page.getByRole("heading", {name: "相關書表", exact: true})).toBeVisible();
    await expect(page.locator(".source-page-list")).not.toHaveAttribute("open");
    await openDialog(page);
    await page.locator("#manual-search-dialog [data-scope=chapter]").click();
    await searchDialog(page, loan === "farm-machinery-loan" ? "農機" : "貸款");
    const groups = await page.locator("#manual-search-dialog .search-result").evaluateAll(
      (cards) => cards.map((card) => card.textContent)
    );
    expect(groups.length).toBeGreaterThan(0);
  });
}

test("search result prioritizes context and fallback uses the real catalog", async ({page}) => {
  await page.goto(paths.home);
  await openDialog(page);
  await searchDialog(page, "寬緩期");
  const first = page.locator("#manual-search-dialog .search-result").first();
  await expect(first.locator(".result-context")).toBeVisible();
  await expect(first.locator(".result-type-badge")).toBeVisible();
  await expect(first.locator(".result-snippet")).toBeVisible();
  await expect(first.locator(".result-pages")).toBeVisible();
  await expect(first.locator(".result-actions a").first()).toBeVisible();

  await page.route("**/assets/data/search-index.json", (route) =>
    route.fulfill({status: 500, body: "failed"})
  );
  await page.reload();
  await openDialog(page);
  await page.locator("#dialog-site-search").fill("農機");
  await page.locator("#manual-search-dialog form button[type=submit]").click();
  await expect(page.locator("#manual-search-dialog .search-status")).toContainText("搜尋索引目前無法載入");
  const catalog = page.getByRole("link", {name: "查看原書完整目錄"});
  await expect(catalog).toHaveAttribute("href", /versions\/114\/(?:index\.html)?$/);
});

for (const loan of ["young-farmer-loan", "farm-machinery-loan", "natural-disaster-low-interest-loan"]) {
  test(`${loan} inline search defaults to the current loan and task restores context`, async ({page}) => {
    await page.goto(`/loans/${loan}/`);
    const panel = page.locator(".loan-context-search [data-search]");
    await expect(panel.locator("[data-scope=chapter]")).toHaveAttribute("aria-pressed", "true");
    await expect(panel.locator("[data-scope=all]")).toHaveAttribute("aria-pressed", "false");
    await panel.locator("input[type=search]").fill("貸款");
    await panel.locator("form button[type=submit]").click();
    await expect(panel.locator(".search-result").first()).toBeVisible();
    expect(await panel.evaluate((element, expected) =>
      element.__manualSearch.state.ranked.every(({record}) => record.scopeGroup === `loan:${expected}`)
    , loan)).toBe(true);

    await panel.locator("[data-scope=all]").click();
    await page.locator(".loan-context-search .task-shortcuts button", {hasText: "申請資格"}).click();
    await expect(panel.locator("[data-scope=chapter]")).toHaveAttribute("aria-pressed", "true");
    await expect(panel.locator("[data-scope=all]")).toHaveAttribute("aria-pressed", "false");
    await expect(panel.locator(".search-result").first()).toBeVisible();
    const taskState = await panel.evaluate((element, expected) => ({
      leaked: element.__manualSearch.state.ranked.filter(
        ({record}) => record.scopeGroup !== `loan:${expected}`
      ).length,
      semantic: element.__manualSearch.state.ranked.slice(0, 10).filter(
        ({record}) => /申請資格條件|申貸資格|貸款對象|本貸款之對象|救助對象/.test(record.text)
      ).length,
      focused: document.activeElement?.matches(".search-result a, .search-status")
    }), loan);
    expect(taskState).toEqual({leaked: 0, semantic: expect.any(Number), focused: true});
    expect(taskState.semantic).toBeGreaterThan(0);
  });
}

for (const section of ["agricultural-development-fund-rules", "natural-disaster-rules"]) {
  test(`${section} inline search defaults to the section and shortcut stays scoped`, async ({page}) => {
    await page.goto(`/versions/114/sections/${section}/`);
    const panel = page.locator(".hub-search [data-search]");
    const scopes = (await page.locator("body").getAttribute("data-search-scopes")).split(",");
    await expect(panel.locator("[data-scope=chapter]")).toHaveAttribute("aria-pressed", "true");
    await expect(panel.locator("[data-scope=all]")).toHaveAttribute("aria-pressed", "false");
    await panel.locator("input[type=search]").fill("貸款");
    await panel.locator("form button[type=submit]").click();
    await expect(panel.locator(".search-result").first()).toBeVisible();
    expect(await panel.evaluate((element, expectedScopes) =>
      element.__manualSearch.state.ranked
        .filter(({record}) => record.type === "原文頁面")
        .every(({record}) => expectedScopes.includes(record.scope))
    , scopes)).toBe(true);
    await panel.locator("[data-scope=all]").click();
    await page.locator(".hub-search .task-shortcuts button", {hasText: "可以貸多少"}).click();
    await expect(panel.locator("[data-scope=chapter]")).toHaveAttribute("aria-pressed", "true");
    await expect(panel.locator("[data-scope=all]")).toHaveAttribute("aria-pressed", "false");
    const state = await panel.evaluate((element, expectedScopes) => ({
      leaked: element.__manualSearch.state.ranked.filter(
        ({record}) => record.type === "原文頁面" && !expectedScopes.includes(record.scope)
      ).length,
      semantic: element.__manualSearch.state.ranked.slice(0, 10).filter(
        ({record}) => /貸款額度|最高貸款額度|最高額度/.test(record.text)
      ).length
    }), scopes);
    expect(state.leaked).toBe(0);
    expect(state.semantic).toBeGreaterThan(0);
  });
}

test("global dialog stays all-scope on a loan page", async ({page}) => {
  await page.goto(paths.loan);
  await openDialog(page);
  const dialog = page.locator("#manual-search-dialog");
  await expect(dialog.locator("[data-scope=all]")).toHaveAttribute("aria-pressed", "true");
  await expect(dialog.locator("[data-scope=chapter]")).toHaveAttribute("aria-pressed", "false");
  expect(await dialog.locator("[data-search]").evaluate(
    (panel) => panel.__manualSearch.state.scope
  )).toBe("all");
});

test("homepage task is semantic, global and moves focus to results", async ({page}) => {
  await page.goto(paths.home);
  await page.locator(".task-shortcuts button", {hasText: "申請資格"}).click();
  const panel = page.locator(".hero [data-search]");
  await expect(panel.locator(".search-result").first()).toBeVisible();
  const state = await panel.evaluate((element) => ({
    scope: element.__manualSearch.state.scope,
    semantic: element.__manualSearch.state.ranked.slice(0, 10).filter(
      ({record}) => /申請資格條件|申貸資格|貸款對象|本貸款之對象|救助對象/.test(record.text)
    ).length,
    focused: document.activeElement?.matches(".search-result a, .search-status")
  }));
  expect(state.scope).toBe("all");
  expect(state.semantic).toBeGreaterThan(0);
  expect(state.focused).toBe(true);
});

test("appendix action and evidence catalog wording are correct", async ({page}) => {
  await page.goto(paths.home);
  await openDialog(page);
  await searchDialog(page, appendixTitle);
  const appendix = page.locator("#manual-search-dialog .search-result")
    .filter({has: page.locator(".result-type-badge", {hasText: "附錄附件"})}).first();
  await expect(appendix.getByRole("link", {name: "查看附錄", exact: true})).toBeVisible();
  await expect(appendix.getByRole("link", {name: "查看書表", exact: true})).toHaveCount(0);

  await page.goto("/versions/114/pages/page-211.html");
  await expect(page.locator(".breadcrumb").getByText("原書完整目錄", {exact: true})).toBeVisible();
  await expect(page.getByRole("link", {name: "回原書完整目錄", exact: true})).toBeVisible();
  await expect(page.getByText("回完整目錄", {exact: true})).toHaveCount(0);
});

test("official update filters load from query and keep a shareable URL", async ({page}) => {
  const runtime = observeRuntime(page);
  await page.goto("/updates/?type=faq");
  const filters = page.locator("[data-update-filters]");
  await expect(filters.locator('select[name="type"]')).toHaveValue("faq");
  await expect(filters.locator(".update-filter-status")).toHaveText("顯示 3 筆官方更新");
  await expect(page.locator(".official-update-item:visible")).toHaveCount(3);

  await filters.locator('select[name="relation"]').selectOption("farmer-relief-loan");
  await expect(page).toHaveURL(/type=faq&relation=farmer-relief-loan$/);
  await expect(filters.locator(".update-filter-status")).toHaveText("顯示 1 筆官方更新");
  await expect(page.locator(".official-update-item:visible")).toHaveCount(1);
  await expect(page.locator(".official-update-item:visible")).toContainText("115年「農民紓困貸款」公告事項常見問答");
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});

test("official update layer preserves explicit matched and no-match states", async ({page}) => {
  await page.goto("/loans/young-farmer-loan/");
  const matched = page.locator(".loan-current-updates");
  await expect(matched.getByRole("heading", {name: "手冊出版後官方更新"})).toBeVisible();
  await expect(matched).toContainText("辦理政策性農業專案貸款辦法");
  await expect(matched).toContainText("農業發展基金貸款作業規範");

  await page.goto("/loans/agricultural-rooting-loan/");
  await expect(page.locator(".loan-current-updates")).toContainText(
    "在目前已檢核的官方更新索引中，尚未建立與本貸款明確對應的手冊出版後更新。"
  );

  await page.goto(paths.disaster);
  await expect(page.locator(".loan-current-updates")).toContainText("8 筆明確對應紀錄");
  await expect(page.locator(".loan-current-updates")).toContainText("農業天然災害救助辦法");
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
  expect(urls).toHaveLength(398);
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
