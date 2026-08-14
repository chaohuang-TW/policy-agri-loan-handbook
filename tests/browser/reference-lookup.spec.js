const {test, expect} = require("@playwright/test");

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

async function faq(page) {
  await page.goto("/faq/");
  return page.locator('[data-reference-lookup="faq"]');
}

async function interpretations(page) {
  await page.goto("/interpretations/");
  return page.locator('[data-reference-lookup="interpretations"]');
}

test("FAQ opens with all deterministic question-level records", async ({page}) => {
  const tool = await faq(page);
  await expect(tool.locator("[data-lookup-status]")).toHaveText("找到 52 筆FAQ。");
  await expect(page.locator(".faq-lookup-result:visible")).toHaveCount(52);
  await expect(tool.getByText("以下結果來自114年度手冊底本")).toBeVisible();
});

test("FAQ keyword search returns source questions", async ({page}) => {
  const tool = await faq(page);
  await tool.locator("input[type=search]").fill("寬緩期");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-lookup-status]")).toHaveText("找到 2 筆FAQ。");
  await expect(page.locator(".faq-lookup-result:visible").first()).toContainText("寬緩期");
});

test("FAQ group filter exposes the four real source groups", async ({page}) => {
  const tool = await faq(page);
  await expect(tool.locator("[data-lookup-group-filter]")).toHaveCount(5);
  await tool.locator('[data-lookup-group-filter="faq-114-10"]').click();
  await expect(tool.locator("[data-lookup-status]")).toHaveText("找到 7 筆FAQ。");
  await expect(page.locator(".faq-lookup-result:visible")).toHaveCount(7);
});

test("FAQ combined query and source filter are deterministic", async ({page}) => {
  const tool = await faq(page);
  await tool.locator("input[type=search]").fill("青壯年農民");
  await tool.locator('[data-lookup-group-filter="faq-young-farmer-114-10"]').click();
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-lookup-status]")).toContainText("筆FAQ");
  expect(await page.locator(".faq-lookup-result:visible").count()).toBeGreaterThan(0);
});

test("FAQ clear resets filters and URL", async ({page}) => {
  const tool = await faq(page);
  await tool.locator("input[type=search]").fill("寬緩期");
  await tool.locator("button[type=submit]").click();
  await tool.locator(".lookup-clear").click();
  await expect(page).toHaveURL(/\/faq\/$/);
  await expect(tool.locator("[data-lookup-status]")).toHaveText("找到 52 筆FAQ。");
});

test("FAQ result count has aria-live semantics", async ({page}) => {
  const tool = await faq(page);
  await expect(tool.locator("[data-lookup-status]")).toHaveAttribute("aria-live", "polite");
  await tool.locator("input[type=search]").fill("不存在的FAQ詞");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-lookup-status]")).toHaveText("目前找不到符合條件的114年度手冊底本資料。");
});

test("FAQ query state survives reload", async ({page}) => {
  const tool = await faq(page);
  await tool.locator("input[type=search]").fill("寬緩期");
  await tool.locator("button[type=submit]").click();
  await page.reload();
  await expect(page.locator('[data-reference-lookup="faq"] input[type=search]')).toHaveValue("寬緩期");
  await expect(page.locator(".faq-lookup-result:visible")).toHaveCount(2);
});

test("FAQ browser back and forward restore URL state", async ({page}) => {
  const tool = await faq(page);
  await tool.locator("input[type=search]").fill("寬緩期");
  await tool.locator("button[type=submit]").click();
  await tool.locator('[data-lookup-group-filter="faq-young-farmer-114-10"]').click();
  await page.goBack();
  await expect(page).toHaveURL(/q=%E5%AF%AC%E7%B7%A9%E6%9C%9F/);
  await expect(page.locator(".faq-lookup-result:visible")).toHaveCount(2);
  await page.goForward();
  await expect(page).toHaveURL(/group=faq-young-farmer-114-10/);
});

test("FAQ cards expose Evidence and PDF links", async ({page}) => {
  await faq(page);
  const card = page.locator(".faq-lookup-result:visible").first();
  await expect(card.getByRole("link", {name: "在手冊中開啟", exact: true})).toHaveAttribute("href", /versions\/114\/pages\/page-\d{3}\.html/);
  await expect(card.getByRole("link", {name: "開啟PDF原文", exact: true})).toHaveAttribute("href", /downloads\/policy-agri-loan-handbook-114\.pdf#page=\d+/);
});

test("FAQ answer details is native and keyboard usable", async ({page}) => {
  await faq(page);
  const details = page.locator(".faq-lookup-result:visible details").first();
  await details.locator("summary").focus();
  await page.keyboard.press("Enter");
  await expect(details).toHaveAttribute("open", "");
  await expect(details.locator(".lookup-source-text p").first()).toBeVisible();
});

test("FAQ source group links preserve all four ranges", async ({page}) => {
  await faq(page);
  await expect(page.locator(".lookup-source-groups li")).toHaveCount(4);
  await expect(page.locator(".lookup-source-groups")).toContainText("315");
  await expect(page.locator(".lookup-source-groups")).toContainText("349");
});

test("FAQ search form has an accessible label and preserves group URL state", async ({page}) => {
  const tool = await faq(page);
  await expect(tool.getByRole("searchbox", {name: "搜尋FAQ問題或關鍵字"})).toBeVisible();
  await tool.locator('[data-lookup-group-filter="faq-114-10"]').click();
  await expect(page).toHaveURL(/group=faq-114-10/);
});

test("FAQ first record evidence starts at its declared source page", async ({page}) => {
  await faq(page);
  const card = page.locator(".faq-lookup-result:visible").first();
  await expect(card).toHaveAttribute("data-lookup-id", "faq-112-12-q01");
  await expect(card.getByRole("link", {name: "在手冊中開啟", exact: true})).toHaveAttribute("href", /page-315\.html$/);
});

test("FAQ group filter exposes selected state to assistive technology", async ({page}) => {
  const tool = await faq(page);
  const filter = tool.locator('[data-lookup-group-filter="faq-young-farmer-114-10"]');
  await filter.click();
  await expect(filter).toHaveAttribute("aria-pressed", "true");
  await expect(tool.locator('[data-lookup-group-filter=""]')).toHaveAttribute("aria-pressed", "false");
});

test("FAQ group URL state survives reload without changing the record set", async ({page}) => {
  const tool = await faq(page);
  await tool.locator('[data-lookup-group-filter="faq-114-10"]').click();
  await page.reload();
  await expect(page).toHaveURL(/group=faq-114-10/);
  await expect(tool.locator("[data-lookup-status]")).toHaveText("找到 7 筆FAQ。");
});

test("interpretations opens with all 87 records", async ({page}) => {
  const tool = await interpretations(page);
  await expect(tool.locator("[data-lookup-status]")).toHaveText("找到 87 筆函釋。");
  await expect(page.locator(".interpretation-lookup-result:visible")).toHaveCount(87);
});

test("interpretation full document number ranks interpretation-001 first", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("農授金字第0955080181號");
  await tool.locator("button[type=submit]").click();
  await expect(page.locator(".interpretation-lookup-result:visible").first()).toHaveAttribute("data-lookup-id", "interpretation-001");
});

test("interpretation numeric document number ranks interpretation-001 first", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("0955080181");
  await tool.locator("button[type=submit]").click();
  await expect(page.locator(".interpretation-lookup-result:visible").first()).toHaveAttribute("data-lookup-id", "interpretation-001");
});

for (const query of ["借新還舊", "支付憑證", "動用期限"]) {
  test(`interpretation subject query ${query} returns source records`, async ({page}) => {
    const tool = await interpretations(page);
    await tool.locator("input[type=search]").fill(query);
    await tool.locator("button[type=submit]").click();
    await expect(tool.locator("[data-lookup-status]")).toContainText("筆函釋");
    expect(await page.locator(".interpretation-lookup-result:visible").count()).toBeGreaterThan(0);
  });
}

test("interpretation program filter is built from data", async ({page}) => {
  const tool = await interpretations(page);
  const select = tool.locator("select[data-lookup-program]");
  expect(await select.locator("option").count()).toBeGreaterThan(1);
  await select.selectOption({index: 1});
  await expect(tool.locator("[data-lookup-status]")).toContainText("筆函釋");
  expect(await page.locator(".interpretation-lookup-result:visible").count()).toBeGreaterThan(0);
});

test("interpretation year filter is built from data", async ({page}) => {
  const tool = await interpretations(page);
  const select = tool.locator("select[data-lookup-year]");
  expect(await select.locator("option").count()).toBeGreaterThan(1);
  await select.selectOption({index: 1});
  await expect(tool.locator("[data-lookup-status]")).toContainText("筆函釋");
});

test("interpretation combined query and filters keep the record in scope", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("借新還舊");
  await tool.locator("select[data-lookup-program]").selectOption("common-rules");
  await tool.locator("button[type=submit]").click();
  await expect(page.locator(".interpretation-lookup-result:visible").first()).toHaveAttribute("data-lookup-program", "common-rules");
});

test("interpretation clear removes query and filters", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("借新還舊");
  await tool.locator("select[data-lookup-year]").selectOption({index: 1});
  await tool.locator(".lookup-clear").click();
  await expect(page).toHaveURL(/\/interpretations\/$/);
  await expect(tool.locator("[data-lookup-status]")).toHaveText("找到 87 筆函釋。");
});

test("interpretation URL state survives reload", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("0955080181");
  await tool.locator("button[type=submit]").click();
  await page.reload();
  await expect(page.locator('[data-reference-lookup="interpretations"] input[type=search]')).toHaveValue("0955080181");
  await expect(page.locator(".interpretation-lookup-result:visible").first()).toHaveAttribute("data-lookup-id", "interpretation-001");
});

test("interpretation browser back restores previous query", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("0955080181");
  await tool.locator("button[type=submit]").click();
  await tool.locator("input[type=search]").fill("借新還舊");
  await tool.locator("button[type=submit]").click();
  await page.goBack();
  await expect(page).toHaveURL(/q=0955080181/);
  await expect(page.locator(".interpretation-lookup-result:visible").first()).toHaveAttribute("data-lookup-id", "interpretation-001");
});

test("interpretation cards expose Evidence and PDF links", async ({page}) => {
  await interpretations(page);
  const card = page.locator(".interpretation-lookup-result:visible").first();
  await expect(card.getByRole("link", {name: "在手冊中開啟", exact: true})).toHaveAttribute("href", /versions\/114\/pages\/page-\d{3}\.html/);
  await expect(card.getByRole("link", {name: "開啟PDF原文", exact: true})).toHaveAttribute("href", /downloads\/policy-agri-loan-handbook-114\.pdf#page=\d+/);
});

test("interpretation empty result is explicit", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("不存在的函釋詞");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-lookup-status]")).toHaveText("目前找不到符合條件的114年度手冊底本資料。");
  await expect(page.locator(".interpretation-lookup-result:visible")).toHaveCount(0);
});

test("interpretation filters preserve program and year in the shareable URL", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("select[data-lookup-program]").selectOption("common-rules");
  await tool.locator("select[data-lookup-year]").selectOption({index: 1});
  await expect(page).toHaveURL(/program=common-rules/);
  await expect(page).toHaveURL(/year=/);
});

test("interpretation result keeps start-only evidence semantics", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("0955080181");
  await tool.locator("button[type=submit]").click();
  const card = page.locator(".interpretation-lookup-result:visible").first();
  await expect(card).toContainText("頁碼範圍：start-only");
  await expect(card.getByRole("link", {name: "開啟PDF原文", exact: true})).toHaveAttribute("href", /#page=\d+$/);
});

test("interpretation loan-program filter keeps every visible result in scope", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("select[data-lookup-program]").selectOption("common-rules");
  const values = await page.locator(".interpretation-lookup-result:visible").evaluateAll(cards => cards.map(card => card.getAttribute("data-lookup-program")));
  expect(values.length).toBeGreaterThan(0);
  expect(new Set(values)).toEqual(new Set(["common-rules"]));
});

test("interpretation document number search keeps the result heading and source link together", async ({page}) => {
  const tool = await interpretations(page);
  await tool.locator("input[type=search]").fill("0955080181");
  await tool.locator("button[type=submit]").click();
  const card = page.locator(".interpretation-lookup-result:visible").first();
  await expect(card.locator("h3")).not.toBeEmpty();
  await expect(card.getByRole("link", {name: "在手冊中開啟", exact: true})).toHaveAttribute("href", /versions\/114\/pages\/page-\d{3}\.html/);
});

for (const width of [375, 390, 430]) {
  test(`FAQ and interpretation have no overflow at ${width}px`, async ({page}) => {
    await page.setViewportSize({width, height: 844});
    await faq(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await interpretations(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
}

test("FAQ and interpretation have no overflow at the requested 393px width", async ({page}) => {
  await page.setViewportSize({width: 393, height: 852});
  await faq(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await interpretations(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("FAQ and interpretation lookup are usable at desktop width", async ({page}) => {
  await page.setViewportSize({width: 1440, height: 1000});
  await faq(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await interpretations(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("global search, loan reading and official updates remain separate", async ({page}) => {
  await page.goto("/");
  await page.locator("[data-open-search]:visible").first().click();
  await page.locator("#dialog-site-search").fill("0955080181");
  await page.locator("#manual-search-dialog form button[type=submit]").click();
  await expect(page.locator("#manual-search-dialog .search-result").first()).toBeVisible();
  await page.goto("/loans/young-farmer-loan/");
  await expect(page.locator("#loan-task-navigation")).toBeVisible();
  await page.goto("/versions/114/sections/loan-programs/");
  await expect(page.locator("details.page-toc")).toBeVisible();
  await page.goto("/updates/");
  await expect(page.locator(".official-update-item")).toHaveCount(20);
});

test("lookup pages report no console, page, 404 or external errors", async ({page}) => {
  const runtime = observeRuntime(page);
  await faq(page);
  await interpretations(page);
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});
