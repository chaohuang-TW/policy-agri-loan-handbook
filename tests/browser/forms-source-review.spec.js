const {test,expect}=require('@playwright/test');
const forms=require('../../data/114/forms.json');
const reviews=require('../../curation/114/forms-source-review.json').records;

test.beforeEach(async({page})=>{await page.goto('/forms/');});
test('forms index retains all 28 stable IDs',async({page})=>{
  await expect(page.locator('[data-form-id]')).toHaveCount(28);
  expect(await page.locator('[data-form-id]').evaluateAll(nodes=>nodes.map(n=>n.dataset.formId))).toEqual(forms.map(f=>f.id));
});
test('every form title and visible subtitle match source-reviewed data',async({page})=>{
  for(const form of forms){const row=page.locator(`#item-${form.id}`);await expect(row.locator('strong')).toHaveText(form.title);if(form.sourceSubtitle)await expect(row).toContainText(form.sourceSubtitle);}
});
test('every Evidence link resolves to its actual source anchor',async({page,request})=>{
  const links=await page.locator('[data-form-evidence]').evaluateAll(nodes=>nodes.map(n=>n.href));
  for(const link of new Set(links)){const url=new URL(link);const response=await request.get(url.pathname);expect(response.status()).toBe(200);expect(await response.text()).toContain(`id="${url.hash.slice(1)}"`);}
});
test('every PDF link points to untouched download and legal starting page',async({page,request})=>{
  const links=await page.locator('[data-form-pdf]').evaluateAll(nodes=>nodes.map(n=>({url:n.href,page:Number(n.dataset.formPdf)})));
  for(let i=0;i<links.length;i++){expect(links[i].page).toBe(forms[i].pdfPageStart);expect(links[i].page).toBeGreaterThanOrEqual(1);expect(links[i].page).toBeLessThanOrEqual(359);expect(new URL(links[i].url).hash).toBe(`#page=${forms[i].pdfPageStart}`);}
  expect((await request.get('/downloads/policy-agri-loan-handbook-114.pdf')).status()).toBe(200);
});
test('all multi-page forms visibly expose first and last Evidence pages',async({page})=>{
  for(const f of forms.filter(f=>f.sourcePages.length>1)){
    const row=page.locator(`#item-${f.id}`);await expect(row).toContainText(`手冊頁 ${f.printedPageStart}–${f.printedPageEnd}｜PDF頁 ${f.pdfPageStart}–${f.pdfPageEnd}`);
    expect(await row.locator('[data-form-evidence]').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.formEvidence)))).toEqual([f.pdfPageStart,f.pdfPageEnd]);
  }
});
test('form-023 presents directly evidenced scope, full title and two-page range',async({page})=>{
  const row=page.locator('#item-form-023');await expect(row).toHaveAttribute('data-form-scope','loan:agri-organization-disaster-recovery-loan');await expect(row).toContainText('申貸「農民組織及農企業天然災害復耕復建貸款」專用');await expect(row).toContainText('PDF頁 251–252');await expect(row).toContainText('來源核對完成');
});
test('form-027 presents source subtitle, evidenced scope and two-page range',async({page})=>{
  const row=page.locator('#item-form-027');await expect(row).toHaveAttribute('data-form-scope','loan:natural-disaster-low-interest-loan');await expect(row).toContainText('(申貸「農業天然災害低利貸款」專用)');await expect(row).toContainText('PDF頁 292–293');
});
test('forms 390px preserves long titles, links and no overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.reload();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  for(const f of forms){const row=page.locator(`#item-${f.id}`);await expect(row.locator('strong')).toHaveText(f.title);expect(await row.evaluate(n=>n.scrollWidth<=n.clientWidth+1)).toBe(true);}
});
test('forms has no console errors during source navigation',async({page})=>{
  const errors=[];page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});await page.reload();await page.locator('#item-form-023 [data-form-evidence]').first().click();await expect(page.locator('#pdf-page-251')).toBeVisible();expect(errors).toEqual([]);
});
test('forms has no pageerror or unhandled rejection',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.addInitScript(()=>{window.__reviewRejections=[];addEventListener('unhandledrejection',e=>window.__reviewRejections.push(String(e.reason)));});await page.reload();expect(errors).toEqual([]);expect(await page.evaluate(()=>window.__reviewRejections)).toEqual([]);
});
test('source evidence link is keyboard operable with visible focus',async({page})=>{
  const link=page.locator('#item-form-028 [data-form-evidence]');await link.focus();await expect(link).toBeFocused();expect(await link.evaluate(n=>getComputedStyle(n).outlineStyle)).not.toBe('none');await page.keyboard.press('Enter');await expect(page).toHaveURL(/page-305\.html#pdf-page-305$/);
});
test('model source review never claims human review',async({page})=>{
  expect(reviews.every(r=>r.humanReviewed===false&&r.reviewedByModel===true)).toBe(true);await expect(page.locator('main')).not.toContainText('人工覆核完成');
});
