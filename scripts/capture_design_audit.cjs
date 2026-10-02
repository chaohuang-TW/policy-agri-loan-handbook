"use strict";
// Fixed Chromium environment. Output stays outside the deployable site.
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const {chromium} = require('@playwright/test');
const core = require('../assets/js/search-core.js');
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const mode = process.argv[2] || 'before';
const output = process.env.DESIGN_AUDIT_DIR || 'tmp/design-audit';
const baseURL = process.env.DESIGN_BASE_URL || 'http://127.0.0.1:8766/';
const target = path.join(output, mode);
fs.mkdirSync(target, {recursive:true});
const routes = [
  ['home', ''], ['loans', 'loans/'], ['long-loan', 'loans/young-farmer-loan/'],
  ['section', 'versions/114/sections/policy-loan-regulations/'], ['faq', 'faq/'],
  ['faq-open', 'faq/', 'answer'], ['interpretations', 'interpretations/?q=0955080181'],
  ['updates', 'updates/'], ['updates-filter', 'updates/?q=農民%20對象'],
  ['dialog', '', 'dialog'], ['toc', 'versions/114/'],
  ['text-evidence', 'versions/114/pages/page-003.html'],
  ['hybrid-evidence', 'versions/114/pages/page-315.html'], ['gateway', 'updates/disasters/']
];
async function main(){
  const browser = await chromium.launch();
  const measurements = [];
  for(const width of [390,1440]){
    const page = await browser.newPage({viewport:{width,height:width===390?844:1000},locale:'zh-TW',deviceScaleFactor:1,reducedMotion:'reduce'});
    for(const [name,route,state] of routes){
      const requests=[];
      const onRequest=request=>requests.push(request.url());
      page.on('request',onRequest);
      await page.goto(new URL(route,baseURL).href,{waitUntil:'networkidle'});
      if(state==='answer'){
        const answer=page.locator('.faq-lookup-result details').first();
        await answer.evaluate(e=>e.open=true);
        await answer.locator('summary').scrollIntoViewIfNeeded();
      }
      if(state==='dialog'){
        await page.locator('[data-open-search]:visible').first().click();
        await page.locator('#dialog-site-search').fill('申請資格');
        await page.locator('#manual-search-dialog button[type=submit]').click();
        await page.locator('#manual-search-dialog .search-result').first().waitFor();
      }
      await page.screenshot({path:path.join(target,`${name}-${width}.png`),fullPage:name==='home'});
      if(name==='home')await page.screenshot({path:path.join(target,`home-first-screen-${width}.png`)});
      const metrics=await page.evaluate(()=>({
        width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
        h1:getComputedStyle(document.querySelector('h1')).fontSize,
        body:getComputedStyle(document.body).fontSize,
        header:document.querySelector('.site-header').getBoundingClientRect().height,
        search:document.querySelector('input[type=search]')?.getBoundingClientRect().toJSON(),
        paint:performance.getEntriesByType('paint').map(e=>({name:e.name,time:e.startTime})),
        navigation:performance.getEntriesByType('navigation')[0]?.toJSON()
      }));
      measurements.push({name,width,metrics,requests:requests.length});
      page.off('request',onRequest);
    }
    await page.close();
  }
  const prepared=core.prepareSearchData(read('site/assets/data/search-index.json'),read('data/114/search-concepts.json'),read('data/114/search-intents.json'));
  const queries=['申請資格','農機','寬緩期','農授金字第0955080181號','0955080181','1147467200A'];
  const semantics={handbook:{},lookup:{}};
  for(const query of queries) semantics.handbook[query]=core.searchRecords(prepared.records,query,prepared.concepts,prepared.intents,'all','all');
  const page=await browser.newPage();
  const ref=read('tests/fixtures/reference-lookup.json');
  const official=read('tests/fixtures/official-updates-lookup.json');
  const cases=[...ref.faq.map(f=>['faq',f.query]),...ref.interpretations.map(f=>['interpretations',f.query]),...official.queries.map(f=>['updates',f.query]),...official.whitespaceVariants.map(q=>['updates',q])];
  for(const [kind,q] of cases){
    await page.goto(new URL(`${kind}/?q=${encodeURIComponent(q)}`,baseURL).href);
    semantics.lookup[kind+':'+q]=await page.locator(kind==='updates'?'[data-official-update-result]:visible':'[data-lookup-result]:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.officialUpdateId||n.dataset.lookupKey||n.dataset.lookupId));
    if(kind==='updates')semantics.lookup[kind+':'+q+':scores']=await page.evaluate(q=>JSON.parse(document.querySelector('[data-official-updates-data]').textContent).map(r=>[r.id,window.OfficialUpdatesLookup.score(r,q)]),q);
  }
  for(const filter of official.filters){
    const params=new URLSearchParams(Object.entries(filter).filter(([k])=>['program','type','year'].includes(k)));
    await page.goto(new URL('updates/?'+params,baseURL).href);
    semantics.lookup['filter:'+filter.name]=await page.locator('[data-official-update-result]:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.officialUpdateId));
  }
  const sizes={};
  for(const name of ['assets/css/site.css','assets/js/search.js','assets/js/site-tools.js','assets/js/search-core.js','assets/js/reference-lookup.js','assets/js/official-updates-lookup.js']){
    const raw=fs.readFileSync(name); sizes[name]={bytes:raw.length,gzip:zlib.gzipSync(raw).length};
  }
  fs.writeFileSync(path.join(target,'measurements.json'),JSON.stringify({measurements,sizes},null,2));
  fs.writeFileSync(path.join(target,'queries.json'),JSON.stringify(semantics,null,2));
  if(mode!=='before'){
    const before=read(path.join(output,'before/queries.json'));
    require('assert').deepStrictEqual(semantics,before,'Query results, scores and matched evidence must be identical');
  }
  await browser.close();
  console.log(`Design capture ${mode}: ${measurements.length} states, query equality ${mode==='before'?'baseline recorded':'PASS'}; ${target}`);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
