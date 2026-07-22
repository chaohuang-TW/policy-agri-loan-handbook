(function (global) {
  "use strict";
  const TYPES = ["原文頁面", "貸款索引", "函釋", "常見問答", "書表附件", "附錄附件"];
  const WEIGHTS = {exactNumber:1200, exactTitle:1000, phraseTitle:650, title:180, heading:320, breadcrumb:100, body:45, conceptTitle:110, conceptBody:25, allTerms:220, proximity:120, loanTitle:500, formTitle:500};
  function normalizeWithMap(original) {
    const text = String(original || ""); let normalizedText = ""; const startMap = []; const endMap = [];
    let pendingSpace = null;
    for (let index = 0; index < text.length;) {
      const code = text.codePointAt(index); const raw = text.slice(index, index + (code > 0xffff ? 2 : 1)); const next = index + raw.length;
      if (/\s/.test(raw)) { if (pendingSpace === null && normalizedText) pendingSpace = index; index = next; continue; }
      const converted = raw.normalize("NFKC").toLocaleLowerCase("zh-Hant");
      if (pendingSpace !== null) { normalizedText += " "; startMap.push(pendingSpace); endMap.push(index); pendingSpace = null; }
      for (const unit of converted) { normalizedText += unit; startMap.push(index); endMap.push(next); }
      index = next;
    }
    return {normalizedText, startMap, endMap};
  }
  function normalize(value) { return normalizeWithMap(value).normalizedText.trim(); }
  function tokenizeQuery(value) { return [...new Set(normalize(value).split(/[\s,，、;；]+/).filter(Boolean))]; }
  function prepareConcepts(query, concepts) { const tokens = tokenizeQuery(query); return concepts.filter((c) => c.terms.some((term) => tokens.some((token) => normalize(term).includes(token) || token.includes(normalize(term))))).flatMap((c) => c.terms.map(normalize)); }
  function fieldMatches(record, terms) { const fields = {title:normalize(record.title), headings:normalize((record.headings || []).join(" ")), breadcrumb:normalize((record.breadcrumb || []).join(" ")), body:normalize(record.text)}; return {fields, title:terms.filter((t) => fields.title.includes(t)), headings:terms.filter((t) => fields.headings.includes(t)), breadcrumb:terms.filter((t) => fields.breadcrumb.includes(t)), body:terms.filter((t) => fields.body.includes(t))}; }
  function proximityScore(text, terms) { const source = normalize(text); const positions = terms.map((t) => source.indexOf(t)).filter((n) => n >= 0); if (positions.length < 2) return 0; const distance = Math.max(...positions) - Math.min(...positions); return distance <= 180 ? Math.max(0, WEIGHTS.proximity - Math.floor(distance / 3)) : 0; }
  function scoreRecord(record, query, concepts, intents) {
    const terms = tokenizeQuery(query); const matches = fieldMatches(record, terms); const q = normalize(query); let score = matches.title.length*WEIGHTS.title + matches.headings.length*WEIGHTS.heading + matches.breadcrumb.length*WEIGHTS.breadcrumb + matches.body.length*WEIGHTS.body;
    const conceptTerms = prepareConcepts(query, concepts).filter((term) => !terms.includes(term));
    score += conceptTerms.filter((t) => normalize(record.title).includes(t)).length*WEIGHTS.conceptTitle + conceptTerms.filter((t) => normalize(record.text).includes(t)).length*WEIGHTS.conceptBody;
    if (matches.title.length === terms.length && terms.length) score += WEIGHTS.exactTitle;
    if (q.length >= 8 && normalize(record.text).includes(q)) score += WEIGHTS.phraseTitle;
    if (/農授金字第\d+號|農金字第\d+號|農金三字第\d+號/.test(q) && normalize(record.text).includes(q)) score += WEIGHTS.exactNumber;
    if (terms.length > 1 && matches.body.length === terms.length) score += WEIGHTS.allTerms;
    score += proximityScore(record.text, terms);
    if (record.type === "貸款索引" && matches.title.length) score += WEIGHTS.loanTitle;
    if (record.type === "書表附件" && matches.title.length) score += WEIGHTS.formTitle;
    const active = intents.filter((intent) => intent.triggers.some((term) => q.includes(normalize(term))));
    for (const intent of active) if (intent.preferredTypes.includes(record.type)) score += intent.boost;
    return {score, terms:terms.concat(conceptTerms)};
  }
  function diversifyResults(items) {
    const remaining = items.slice(); const selected = []; const scopeCounts = new Map(); const groupCounts = new Map();
    while (remaining.length) {
      let best = 0; let bestScore = -Infinity;
      remaining.forEach((item, index) => { const s = scopeCounts.get(item.record.scope)||0; const g = item.record.scopeGroup ? (groupCounts.get(item.record.scopeGroup)||0) : 0; const score = item.score - Math.max(0, s-1)*18 - Math.max(0, g-2)*10; if (score > bestScore || (score === bestScore && (item.record.pdfPage||0) < (remaining[best].record.pdfPage||0))) { best=index; bestScore=score; } });
      const item = remaining.splice(best, 1)[0]; selected.push({...item, adjustedScore:bestScore}); scopeCounts.set(item.record.scope,(scopeCounts.get(item.record.scope)||0)+1); if(item.record.scopeGroup) groupCounts.set(item.record.scopeGroup,(groupCounts.get(item.record.scopeGroup)||0)+1);
    }
    return selected;
  }
  function searchRecords(records, query, concepts, intents, type="all", scope="all") { const q=normalize(query); if(!q) return []; const ranked=diversifyResults(records.map((record,index)=>({record,index,...scoreRecord(record,q,concepts,intents)})).filter((x)=>x.score>0)); return ranked.filter((x)=> (type === "all" || x.record.type === type) && (scope === "all" || x.record.scope === scope || x.record.scopeGroup === scope)); }
  function createSnippetRange(original, terms) { const map=normalizeWithMap(original); const positions=[]; for(const term of terms){let at=map.normalizedText.indexOf(normalize(term)); let count=0; while(at>=0 && count++<8){positions.push([at,at+normalize(term).length]); at=map.normalizedText.indexOf(normalize(term),at+normalize(term).length);}} if(!positions.length) return {start:0,end:Math.min(String(original||"").length,160),matches:[]}; const begin=Math.max(0,Math.min(...positions.map((p)=>p[0]))-65); const finish=Math.min(map.normalizedText.length,Math.max(...positions.map((p)=>p[1]))+105); const ranges=positions.map(([s,e])=>[Math.max(begin,s),Math.min(finish,e)]).filter(([s,e])=>e>s).sort((a,b)=>a[0]-b[0]); const merged=[]; for(const range of ranges){const last=merged[merged.length-1]; if(last&&range[0]<=last[1]) last[1]=Math.max(last[1],range[1]); else merged.push(range);} return {start:map.startMap[begin] ?? 0,end:map.endMap[finish-1] ?? String(original||"").length,matches:merged.map(([s,e])=>({start:map.startMap[s] ?? 0,end:map.endMap[e-1] ?? String(original||"").length}))}; }
  global.ManualSearchCore={TYPES,WEIGHTS,normalize,normalizeWithMap,tokenizeQuery,prepareConcepts,scoreRecord,diversifyResults,searchRecords,createSnippetRange};
  if (typeof module !== "undefined" && module.exports) module.exports=global.ManualSearchCore;
})(typeof globalThis !== "undefined" ? globalThis : this);
