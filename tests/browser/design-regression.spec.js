const {test, expect} = require('@playwright/test');
const routes = ['/', '/loans/', '/loans/young-farmer-loan/', '/versions/114/sections/policy-loan-regulations/', '/faq/', '/interpretations/?q=0955080181', '/updates/?q=農民%20對象', '/forms/', '/versions/114/', '/versions/114/pages/page-003.html', '/versions/114/pages/page-315.html', '/updates/disasters/'];

for (const width of [320,375,390,393,430,768,1024,1280,1440,1920]) {
  test(`editorial reflow and complete content at ${width}px`, async ({page}) => {
    await page.setViewportSize({width, height: 1000});
    for (const route of routes) {
      await page.goto(route);
      const failures = await page.evaluate(() => {
        const visible = e => e.getClientRects().length > 0;
        const failures = [];
        if(document.documentElement.scrollWidth > innerWidth + 1) failures.push('page overflow');
        for(const node of document.querySelectorAll('h1,h2,h3,input,select,.lookup-meta,.lookup-doc-number,.source-meta')){
          if(!visible(node)) continue;
          const r=node.getBoundingClientRect();
          if(r.left < -1 || r.right > innerWidth+1) failures.push(node.tagName+' outside viewport');
          if(['H1','H2','H3'].includes(node.tagName) && (node.scrollHeight > node.clientHeight + 1 || getComputedStyle(node).textOverflow==='ellipsis')) failures.push('heading clipped');
        }
        return failures;
      });
      expect(failures, `${route} at ${width}`).toEqual([]);
      await expect(page.locator('h1')).toHaveCount(1);
    }
  });
}

for(const [width,height] of [[375,667],[390,844]]){
  test(`home query immediately operable in ${width}x${height} first screen`,async({page})=>{
    await page.setViewportSize({width,height}); await page.goto('/');
    const panel=page.locator('#home-search').locator('xpath=ancestor::*[@data-search]');
    for(const locator of [page.locator('#home-search'),panel.locator('button[type=submit]')]){
      const box=await locator.boundingBox(); expect(box.y+box.height).toBeLessThanOrEqual(height); expect(box.height).toBeGreaterThanOrEqual(44);
    }
    await page.locator('.popular button',{hasText:'農機'}).click();
    await expect(page.locator('#home-search')).toHaveValue('農機');
    await expect(panel.locator('.search-result').first()).toBeVisible();
  });
}

test('four primary entries have nonoverlapping native link targets',async({page})=>{
  await page.goto('/');
  const entries=page.locator('.entry-main'); await expect(entries).toHaveCount(4);
  const expected=['loans','interpretations','forms','versions/114'];
  for(let i=0;i<4;i++){
    expect(await entries.nth(i).getAttribute('href')).toContain(expected[i]);
    expect(await entries.nth(i).locator('a,button').count()).toBe(0);
    await expect(entries.nth(i)).toContainText('前往查閱');
  }
});

test('actual text, hover, selected, input and focus contrast',async({page})=>{
  for(const route of ['/', '/faq/', '/faq/?q=不存在查閱詞', '/interpretations/?q=0955080181','/updates/','/updates/disasters/']){
    await page.goto(route);
    const contrast=async()=>page.evaluate(()=>{
      const rgb=s=>{const m=s.match(/[\d.]+/g); return m?m.map(Number):[255,255,255,1];};
      const lum=c=>c.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);
      const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
      const bg=node=>{const c=rgb(getComputedStyle(node).backgroundColor); if((c[3]??1)===1)return c; return node.parentElement?bg(node.parentElement):[255,255,255,1];};
      return [...document.querySelectorAll('a,button,input,select,label,summary,.source-meta,.lookup-meta,.lookup-doc-number,.layout-note,.search-scope-note,.official-update-badge,.search-status,.lookup-status,.official-update-status')]
        .filter(n=>n.getClientRects().length && n.textContent.trim() || n.getClientRects().length && n.matches('input,select'))
        .map(n=>{const s=getComputedStyle(n); const min=parseFloat(s.fontSize)>=24 || parseFloat(s.fontSize)>=18.66&&parseInt(s.fontWeight)>=700?3:4.5; return {tag:n.tagName,text:n.textContent.trim().slice(0,30),ratio:ratio(rgb(s.color),bg(n)),min};}).filter(r=>r.ratio+0.01<r.min);
    });
    expect(await contrast(),route).toEqual([]);
    const main=page.locator('button[type=submit]:visible').first();
    if(await main.count()) {await main.hover(); expect(await contrast(),route+' hover').toEqual([]); await main.focus(); expect(await main.evaluate(e=>getComputedStyle(e).outlineStyle)).toBe('solid');}
    const input=page.locator('input[type=search]:visible').first();
    if(await input.count()) expect(await input.evaluate(e=>parseFloat(getComputedStyle(e).fontSize))).toBeGreaterThanOrEqual(16);
  }
});

test('dialog one scroll surface, Escape and keyboard focus restoration',async({page})=>{
  await page.setViewportSize({width:390,height:844}); await page.goto('/');
  const trigger=page.locator('[data-open-search]:visible').first(); await trigger.focus(); await page.keyboard.press('Enter');
  await expect(page.locator('#dialog-site-search')).toBeFocused();
  const nested=await page.locator('#manual-search-dialog').evaluate(e=>[...e.querySelectorAll('*')].filter(n=>getComputedStyle(n).overflowY==='auto'&&n.scrollHeight>n.clientHeight).length);
  expect(nested).toBe(0);
  await page.keyboard.press('Escape'); await expect(trigger).toBeFocused();
});

test('focused controls and active state have real nontext contrast',async({page})=>{
  for(const route of ['/','/faq/','/updates/']){
    await page.goto(route);
    for(const selector of ['input[type=search]:visible','button[type=submit]:visible']){
      const control=page.locator(selector).first(); await control.focus();
      const values=await control.evaluate(e=>{
        const rgb=s=>s.match(/[\d.]+/g).map(Number);
        const lum=c=>c.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);
        const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
        const bg=n=>{const c=rgb(getComputedStyle(n).backgroundColor);return(c[3]??1)===1?c:n.parentElement?bg(n.parentElement):[255,255,255,1];};
        const s=getComputedStyle(e), r=e.getBoundingClientRect();
        return {focus:ratio(rgb(s.outlineColor),bg(e.parentElement)),border:e.matches('input')?ratio(rgb(s.borderTopColor),bg(e)):null,visible:r.left>=0&&r.right<=innerWidth&&r.top>=document.querySelector('.site-header').getBoundingClientRect().bottom};
      });
      expect(values.focus).toBeGreaterThanOrEqual(3); if(values.border!==null)expect(values.border).toBeGreaterThanOrEqual(3);expect(values.visible).toBe(true);
    }
    const button=page.locator('button[type=submit]:visible').first(); await button.hover();await page.mouse.down();
    expect(await button.evaluate(e=>{
      const lum=s=>s.match(/[\d.]+/g).slice(0,3).map(Number).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);
      const s=getComputedStyle(e),x=lum(s.color),y=lum(s.backgroundColor);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05);
    })).toBeGreaterThanOrEqual(4.5);
    await page.mouse.up();
  }
});

test('dialog submission exposes first result title and evidence context',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');
  await page.locator('[data-open-search]:visible').first().click();await page.locator('#dialog-site-search').fill('申請資格');
  await page.locator('#dialog-site-search').press('Enter');
  const result=page.locator('#manual-search-dialog .search-result').first();
  await expect(result.locator('h3 a')).toBeFocused();
  expect(await result.locator('h3 a').evaluate(e=>getComputedStyle(e).outlineStyle)).toBe('solid');
  const header=await page.locator('.search-dialog-header').boundingBox();
  for(const selector of ['.result-context','h3','.result-match-meta']){
    const box=await result.locator(selector).boundingBox();expect(box.y).toBeGreaterThanOrEqual(header.y+header.height);expect(box.y+box.height).toBeLessThan(844);
  }
  const focusBox=await result.locator('h3 a').boundingBox();expect(focusBox.y).toBeGreaterThanOrEqual(header.y+header.height);expect(focusBox.y+focusBox.height).toBeLessThan(844);
  await expect(result.locator('h3 a')).toHaveAttribute('href',await result.locator('.result-actions a').first().getAttribute('href'));
});

test('mobile native chapter disclosure and anchor clearance',async({page})=>{
  await page.setViewportSize({width:390,height:844}); await page.goto('/versions/114/sections/policy-loan-regulations/');
  const summary=page.locator('.page-toc > summary'); await summary.focus(); await page.keyboard.press('Enter');
  await expect(page.locator('.page-toc')).toHaveJSProperty('open',true);
  const link=page.locator('.page-toc a').nth(2); const href=await link.getAttribute('href'); await link.click();
  await expect.poll(()=>page.evaluate(h=>document.querySelector(h).getBoundingClientRect().top>=document.querySelector('.site-header').getBoundingClientRect().bottom-1,href)).toBe(true);
  await page.reload(); await expect(page.locator(href)).toBeVisible();
});

test('FAQ native answer Enter key and source evidence survive layout',async({page})=>{
  await page.goto('/faq/?q=屠宰場登記證書'); const card=page.locator('[data-lookup-result]:visible').first();
  await card.locator('summary').focus(); await page.keyboard.press('Enter');
  await expect(card.locator('details')).toHaveJSProperty('open',true);
  await expect(card.locator('.lookup-source-text')).toBeVisible();
  await expect(card.locator('a[href*="page-"]')).toHaveCount(1);
  await expect(card.locator('a[href*=".pdf#page="]')).toHaveCount(1);
});

test('official AND query, compatible combined filters and history remain exact',async({page})=>{
  await page.goto('/updates/?q=農民%20對象');
  expect(await page.locator('[data-official-update-result]:visible').count()).toBe(2);
  await page.locator('#official-updates-q').fill('農民 不存在詞'); await page.locator('.update-filters button[type=submit]').click();
  await expect(page.locator('[data-official-update-result]:visible')).toHaveCount(0);
  await page.goBack(); await expect(page.locator('[data-official-update-result]:visible')).toHaveCount(2);
  await page.goto('/updates/?program=farmer-relief-loan&type=faq&year=2025&relation=farmer-relief-loan');
  await expect(page.locator('[data-official-update-result]:visible')).toHaveCount(1);
  await page.reload(); await expect(page.locator('[data-official-update-result]:visible')).toHaveCount(1);
});

test('reduced motion keeps all content immediately readable and queries functional',async({page})=>{
  await page.emulateMedia({reducedMotion:'reduce'}); await page.goto('/');
  expect(await page.locator('html').evaluate(e=>getComputedStyle(e).scrollBehavior)).toBe('auto');
  await expect(page.locator('h1')).toBeVisible();
  expect(await page.locator('h1').evaluate(e=>getComputedStyle(e).opacity)).toBe('1');
  await page.locator('.popular button',{hasText:'農機'}).click();
  await expect(page.locator('.hero .search-result').first()).toBeVisible();
});

test('without JS native sources, answers and footer navigation stay available',async({browser,baseURL})=>{
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}}); const page=await context.newPage();
  for(const route of ['/faq/','/loans/young-farmer-loan/','/versions/114/pages/page-315.html']){
    await page.goto(baseURL+route); await expect(page.locator('h1')).toBeVisible();
    // Playwright deliberately excludes NOSCRIPT from its aggregate text matcher;
    // the browser-parsed paragraph proves the real no-JS fallback is visible.
    await expect(page.locator('noscript p')).toBeVisible();
    await expect(page.locator('noscript p')).toContainText('目錄');
    await expect(page.locator('.site-footer a').first()).toBeVisible();
    if(route==='/faq/') {await page.locator('.faq-lookup-result summary').first().click(); await expect(page.locator('.lookup-source-text').first()).toBeVisible();}
  }
  await context.close();
});

test('200 percent text-size enlargement reflows controls and long headings',async({page})=>{
  await page.setViewportSize({width:1280,height:1000});
  for(const route of ['/','/faq/','/updates/','/loans/young-farmer-loan/']){
    await page.goto(route);
    await page.evaluate(()=>{
      const nodes=[...document.querySelectorAll('*')].map(n=>[n,parseFloat(getComputedStyle(n).fontSize)]);
      nodes.forEach(([n,size])=>n.style.fontSize=size*2+'px');
    });
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),route).toBe(true);
    await expect(page.locator('h1')).toBeVisible();
    const input=page.locator('input:visible').first(); if(await input.count()) {await input.fill('農機'); await expect(input).toHaveValue('農機');}
  }
});

test('source image keeps intrinsic ratio without cropping',async({page})=>{
  await page.goto('/versions/114/pages/page-315.html');
  const image=page.locator('.source-preview-image'); await image.scrollIntoViewIfNeeded();
  await expect.poll(()=>image.evaluate(e=>e.complete&&e.naturalWidth>0)).toBe(true);
  const ratio=await image.evaluate(e=>{const r=e.getBoundingClientRect();return {actual:r.width/r.height,source:e.naturalWidth/e.naturalHeight,fit:getComputedStyle(e).objectFit};});
  expect(ratio.actual).toBeCloseTo(ratio.source,2); expect(ratio.fit).toBe('contain');
});

test('print exposes original answers and source layers without clipping',async({page})=>{
  for(const route of ['/loans/young-farmer-loan/','/faq/?q=屠宰場登記證書','/versions/114/pages/page-315.html']){
    await page.goto(route); await page.emulateMedia({media:'print'});
    await page.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));
    await expect(page.locator('h1')).toBeVisible(); await expect(page.locator('.site-header')).toBeHidden();
    if(route.startsWith('/faq')) await expect(page.locator('[data-lookup-result]:visible .lookup-source-text').first()).toBeVisible();
    if(route.includes('page-315')) {
      await expect(page.locator('.source-text')).toBeVisible();
      const image=page.locator('.source-preview-image');
      await expect(image).toHaveAttribute('loading','eager');
      await expect.poll(()=>image.evaluate(e=>e.complete&&e.naturalWidth>0)).toBe(true);
    }
    expect(await page.locator('.manual-content,.lookup-source-text').first().evaluate(e=>getComputedStyle(e).overflowY)).not.toBe('hidden');
    await page.evaluate(()=>window.dispatchEvent(new Event('afterprint'))); await page.emulateMedia({media:'screen'});
  }
});

test('presentation has no console/page/unhandled/external/404 failures',async({page})=>{
  const errors=[];
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(!['127.0.0.1','localhost'].includes(new URL(r.url()).hostname))errors.push(r.url());});
  page.on('response',r=>{if(r.status()>=400)errors.push(String(r.status())+' '+r.url());});
  await page.addInitScript(()=>window.addEventListener('unhandledrejection',e=>console.error('Unhandled: '+e.reason)));
  for(const route of routes)await page.goto(route,{waitUntil:'networkidle'});
  expect(errors).toEqual([]);
});
