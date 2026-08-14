const {test, expect} = require("@playwright/test");

function observeRuntime(page) {
  const evidence = {consoleErrors: [], pageErrors: [], badResponses: [], external: []};
  page.on("console", (message) => { if (message.type() === "error") evidence.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => evidence.pageErrors.push(String(error)));
  page.on("response", (response) => { if (response.status() >= 400) evidence.badResponses.push(`${response.status()} ${response.url()}`); });
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (!["127.0.0.1", "localhost"].includes(url.hostname)) evidence.external.push(request.url());
  });
  return evidence;
}

async function updates(page) {
  await page.goto("/updates/");
  return page.locator("[data-official-updates-lookup]").first();
}

test("Official Updates lookup loads 20 formal records", async ({page}) => {
  const tool = await updates(page);
  await expect(tool.locator("[data-official-update-status]")).toHaveText("目前顯示 20 筆官方更新");
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(20);
  await expect(tool.getByText("Coverage仍為partial", {exact: false})).toHaveCount(0);
});

test("Official Updates keyword search finds a real title", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("農業發展基金貸款作業規範");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-official-update-result]:visible").first()).toHaveAttribute("data-official-update-id", "afna-agri-development-fund-rules-20251231");
});

test("Official Updates institutional disaster measure remains a formal record", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("復耕復建");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-official-update-result]:visible").first()).toHaveAttribute("data-official-update-id", "afna-mataian-disaster-loan-relief-20260130");
});

test("Short ordinary numbers do not mass-match official updates", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("2928");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(0);
});

for (const [query, id] of [["農輔字第1150022928C號", "afna-disaster-relief-regulations-20260629"], ["1150022928C", "afna-disaster-relief-regulations-20260629"]]) {
  test(`Official Updates document number query ${query} is exact`, async ({page}) => {
    const tool = await updates(page);
    await tool.locator("input[name=q]").fill(query);
    await tool.locator("button[type=submit]").click();
    await expect(tool.locator("[data-official-update-result]:visible").first()).toHaveAttribute("data-official-update-id", id);
  });
}

async function visibleIds(tool) {
  return tool.locator("[data-official-update-result]:visible").evaluateAll((cards) => cards.map((card) => card.dataset.officialUpdateId));
}

test("Official Updates multi-keyword matching is non-contiguous AND", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("農民 對象");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(2);
  expect(await visibleIds(tool)).toEqual(["afna-farmer-relief-object-announcement-20251219", "afna-farmer-relief-object-letter-20251219"]);
  const targetText = await tool.locator('[data-official-update-result][data-official-update-id="afna-farmer-relief-object-letter-20251219"]').innerText();
  expect(targetText).toContain("農民");
  expect(targetText).toContain("對象");
  expect(targetText).not.toContain("農民對象");
});

test("Official Updates multi-keyword results require every token", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("農民 貸款");
  await tool.locator("button[type=submit]").click();
  const ids = await visibleIds(tool);
  expect(ids).toHaveLength(12);
  const texts = await tool.locator("[data-official-update-result]:visible").allInnerTexts();
  for (const text of texts) {
    expect(text).toContain("農民");
    expect(text).toContain("貸款");
  }
});

test("Official Updates negative multi-keyword query returns zero", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("農民 不存在詞");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(0);
  await expect(tool.locator("[data-official-update-status]")).toHaveText("目前顯示 0 筆官方更新");
});

test("Official Updates whitespace variants preserve multi-keyword results", async ({page}) => {
  const tool = await updates(page);
  const variants = ["農民 貸款", "農民  貸款", "農民　貸款", "農民\t貸款"];
  const results = [];
  for (const query of variants) {
    await tool.locator("input[name=q]").fill(query);
    await tool.locator("button[type=submit]").click();
    results.push(await visibleIds(tool));
  }
  for (const result of results.slice(1)) expect(result).toEqual(results[0]);
});

test("Official Updates multi-keyword query survives reload", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("天然災害 貸款");
  await tool.locator("button[type=submit]").click();
  const before = await visibleIds(tool);
  await page.reload();
  expect(await page.locator("[data-official-updates-lookup] input[name=q]").inputValue()).toBe("天然災害 貸款");
  expect(await visibleIds(page.locator("[data-official-updates-lookup]").first())).toEqual(before);
});

test("Official Updates Back and Forward restore multi-keyword state", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("農民 對象");
  await tool.locator("button[type=submit]").click();
  await tool.locator("input[name=q]").fill("青壯 農民");
  await tool.locator("button[type=submit]").click();
  await page.goBack();
  expect(new URL(page.url()).searchParams.get("q")).toBe("農民 對象");
  expect(await visibleIds(page.locator("[data-official-updates-lookup]").first())).toHaveLength(2);
  await page.goForward();
  expect(new URL(page.url()).searchParams.get("q")).toBe("青壯 農民");
  expect(await visibleIds(page.locator("[data-official-updates-lookup]").first())).toHaveLength(6);
});

test("Official Updates program filter is data-derived", async ({page}) => {
  const tool = await updates(page);
  const select = tool.locator("select[name=program]");
  await expect(select.locator("option")).toHaveCount(21);
  await select.selectOption("farmer-relief-loan");
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(6);
});

test("Official Updates type filter is data-derived", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("select[name=type]").selectOption("faq");
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(3);
});

test("Official Updates year filter uses the event date", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("select[name=year]").selectOption("2025");
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(11);
});

test("Official Updates filter state is reflected in URL parameters", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("select[name=type]").selectOption("faq");
  await expect(page).toHaveURL(/type=faq/);
  await tool.locator("select[name=year]").selectOption("2025");
  await expect(page).toHaveURL(/type=faq&year=2025/);
});

test("Official Updates combined filters keep only the expected record", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("select[name=program]").selectOption("farmer-relief-loan");
  await tool.locator("select[name=type]").selectOption("faq");
  await tool.locator("select[name=year]").selectOption("2025");
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(1);
  await expect(tool.locator("[data-official-update-result]:visible").first()).toHaveAttribute("data-official-update-id", "afna-farmer-relief-faq-20251216");
});

test("Official Updates clear removes all query state", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("農民紓困貸款");
  await tool.locator("button[type=submit]").click();
  await tool.locator("button[type=reset]").click();
  await expect(page).toHaveURL(/\/updates\/$/);
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(20);
});

test("Official Updates URL state survives reload", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("農民紓困貸款");
  await tool.locator("button[type=submit]").click();
  await tool.locator("select[name=program]").selectOption("farmer-relief-loan");
  await page.reload();
  await expect(page.locator("[data-official-updates-lookup] input[name=q]")).toHaveValue("農民紓困貸款");
  await expect(page.locator("[data-official-updates-lookup] select[name=program]")).toHaveValue("farmer-relief-loan");
});

test("Official Updates Back and Forward restore filter state", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("select[name=type]").selectOption("faq");
  await tool.locator("select[name=year]").selectOption("2025");
  await page.goBack();
  await expect(page).toHaveURL(/type=faq/);
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(3);
  await page.goForward();
  await expect(page).toHaveURL(/type=faq&year=2025/);
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(2);
});

test("Official Updates empty result is explicit", async ({page}) => {
  const tool = await updates(page);
  await tool.locator("input[name=q]").fill("不存在的官方文號");
  await tool.locator("button[type=submit]").click();
  await expect(tool.locator("[data-official-update-status]")).toHaveText("目前顯示 0 筆官方更新");
  await expect(tool.locator("[data-official-update-result]:visible")).toHaveCount(0);
});

test("Official Updates cards expose official source and handbook links", async ({page}) => {
  const tool = await updates(page);
  const card = tool.locator("[data-official-update-result]:visible").filter({hasText: "青壯年農民從農貸款"}).first();
  await expect(card.getByRole("link", {name: /查看官方來源/})).toHaveAttribute("rel", "noopener noreferrer");
  await expect(card.getByRole("link", {name: /查看114年手冊原貸款/})).toHaveAttribute("href", /\/loans\/young-farmer-loan\//);
  await expect(card.getByText("官方更新", {exact: true})).toBeVisible();
});

test("Official Updates source links open the formal source in a new tab", async ({page}) => {
  const tool = await updates(page);
  const link = tool.locator("[data-official-update-result]:visible").first().getByRole("link", {name: /查看官方來源/});
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("href", /^https:\/\/(law\.afna\.gov\.tw|www\.afna\.gov\.tw)\//);
});

test("Homepage keeps handbook search separate and exposes the updates entry", async ({page}) => {
  await page.goto("/");
  await expect(page.getByRole("link", {name: "查看手冊出版後官方更新"})).toBeVisible();
  await expect(page.locator("[data-official-updates-lookup]")).toHaveCount(0);
});

test("Disaster route remains an AFNA gateway and has no local records", async ({page}) => {
  await page.goto("/updates/disasters/");
  await expect(page.locator(".disaster-announcement, [data-disaster-filters]")).toHaveCount(0);
  await expect(page.getByRole("link", {name: /前往農業金融署天然災害低利貸款專區/})).toHaveAttribute("href", "https://www.afna.gov.tw/list.php?theme=natural_disaster&subtheme=");
});

test("Official Updates form is keyboard usable and announces count", async ({page}) => {
  const tool = await updates(page);
  const input = tool.locator("input[name=q]");
  await input.focus();
  await page.keyboard.type("復耕復建");
  await page.keyboard.press("Enter");
  await expect(tool.locator("[data-official-update-status]")).toContainText("目前顯示");
  await expect(tool.locator("[data-official-update-status]")).toHaveAttribute("aria-live", "polite");
});

for (const width of [390, 393]) {
  test(`Official Updates has no horizontal overflow at ${width}px`, async ({page}) => {
    await page.setViewportSize({width, height: 844});
    await updates(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
}

for (const width of [375, 430]) {
  test(`Official Updates has no horizontal overflow at ${width}px`, async ({page}) => {
    await page.setViewportSize({width, height: 844});
    await updates(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
}

test("Official Updates remains usable at desktop width", async ({page}) => {
  await page.setViewportSize({width: 1440, height: 1000});
  await updates(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("Official Updates lookup has no runtime errors or unexpected requests", async ({page}) => {
  const runtime = observeRuntime(page);
  await updates(page);
  expect(runtime).toEqual({consoleErrors: [], pageErrors: [], badResponses: [], external: []});
});
