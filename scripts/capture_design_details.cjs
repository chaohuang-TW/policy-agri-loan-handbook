// Focused source/answer comparison, real journey, and print QA; no site writes.
const {chromium}=require('@playwright/test');
const fs=require('fs');const path=require('path');
const out='tmp/design-audit/details';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch();
 async function completeElement(page,element,file,width){
  const height=await element.evaluate(e=>Math.ceil(e.getBoundingClientRect().height));
  // A complete component capture must render its lower composited controls too.
  // The main audit still uses the fixed 390x844/1440x1000 first-screen viewports.
  await page.setViewportSize({width,height:height+200});
  // Fixed camera clearance is QA-only, including the unchanged baseline whose
  // sticky header was taller than its old fragment margin.
  await element.evaluate(e=>window.scrollTo({top:Math.max(0,scrollY+e.getBoundingClientRect().top-document.querySelector('.site-header').getBoundingClientRect().height-24),behavior:'instant'}));
  await element.screenshot({path:file});
 }
 for(const width of [390,1440]){
  const page=await browser.newPage({viewport:{width,height:width===390?844:1000},reducedMotion:'reduce'});
  for(const [name,base] of [['before','http://127.0.0.1:8768'],['after','http://127.0.0.1:8766']]){
   await page.goto(base+'/faq/?q=屠宰場登記證書');const card=page.locator('[data-lookup-result]:visible').first();await card.locator('summary').click();
   await completeElement(page,card,path.join(out,`${name}-faq-answer-${width}.png`),width);
   await page.setViewportSize({width,height:width===390?844:1000});
   await page.goto(base+'/loans/young-farmer-loan/');await completeElement(page,page.locator('.loan-source-page').first(),path.join(out,`${name}-loan-source-${width}.png`),width);
   await page.setViewportSize({width,height:width===390?844:1000});
  }
  await page.goto('http://127.0.0.1:8766/');await page.locator('.popular button',{hasText:'農機'}).click();
  await page.locator('.hero .search-result a',{hasText:'查看貸款'}).first().waitFor({state:'visible'});
  await page.screenshot({path:path.join(out,`journey-query-${width}.png`)});
  await page.locator('.hero .search-result a',{hasText:'查看貸款'}).first().click();await page.screenshot({path:path.join(out,`journey-loan-${width}.png`)});
  await page.locator('#loan-task-navigation a').first().click();await page.screenshot({path:path.join(out,`journey-anchor-${width}.png`)});
  await page.locator('.loan-source-page a',{hasText:'查看原始頁面'}).first().click();await page.screenshot({path:path.join(out,`journey-evidence-${width}.png`)});
  await page.close();
 }
 const page=await browser.newPage();
 for(const [name,route] of [['loan','loans/young-farmer-loan/'],['faq','faq/?q=屠宰場登記證書'],['evidence','versions/114/pages/page-315.html']]){
  await page.goto('http://127.0.0.1:8766/'+route);await page.emulateMedia({media:'print'});await page.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));
  await page.evaluate(()=>Promise.all([...document.images].map(image=>image.complete?Promise.resolve():new Promise((resolve,reject)=>{image.addEventListener('load',resolve,{once:true});image.addEventListener('error',reject,{once:true});}))));
  await page.pdf({path:path.join(out,`print-${name}.pdf`),format:'A4',printBackground:true,margin:{top:'15mm',bottom:'15mm',left:'15mm',right:'15mm'}});
 }
 await browser.close();console.log('Focused before/after, journey, and 3 print PDFs captured.');
})().catch(e=>{console.error(e);process.exitCode=1;});
