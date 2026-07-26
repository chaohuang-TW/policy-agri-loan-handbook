(function (global) {
  "use strict";

  const TYPES = ["原文頁面", "貸款索引", "函釋", "常見問答", "書表附件", "附錄附件"];
  const QUERY_LIMITS = {maxLength: 256, maxTokens: 16, maxTokenLength: 128};
  const WEIGHTS = {
    exactNumber: 1200, exactTitle: 1000, phraseTitle: 650, phraseBody: 180,
    title: 180, heading: 320, breadcrumb: 100, body: 45,
    conceptTitle: 110, conceptBody: 25, allTerms: 220, proximity: 120,
    loanTitle: 500, formTitle: 500,
  };

  function graphemes(text) {
    if (typeof Intl !== "undefined" && Intl.Segmenter) {
      return [...new Intl.Segmenter("zh-Hant", {granularity: "grapheme"}).segment(text)]
        .map((item) => ({segment: item.segment, index: item.index}));
    }
    const result = [];
    for (let index = 0; index < text.length;) {
      const code = text.codePointAt(index);
      const segment = text.slice(index, index + (code > 0xffff ? 2 : 1));
      result.push({segment, index});
      index += segment.length;
    }
    return result;
  }

  function normalizeWithMap(original) {
    const text = String(original || "");
    let normalizedText = "";
    const startMap = [];
    const endMap = [];
    let pendingSpace = null;
    for (const item of graphemes(text)) {
      const start = item.index;
      const end = start + item.segment.length;
      if (/^\s+$/u.test(item.segment)) {
        if (pendingSpace === null && normalizedText) pendingSpace = start;
        continue;
      }
      if (pendingSpace !== null) {
        normalizedText += " ";
        startMap.push(pendingSpace);
        endMap.push(start);
        pendingSpace = null;
      }
      const converted = item.segment.normalize("NFKC").toLocaleLowerCase("zh-Hant");
      normalizedText += converted;
      for (let unit = 0; unit < converted.length; unit += 1) {
        startMap.push(start);
        endMap.push(end);
      }
    }
    return {normalizedText, startMap, endMap};
  }

  function normalize(value) {
    return String(value || "").normalize("NFKC").toLocaleLowerCase("zh-Hant").replace(/\s+/gu, " ").trim();
  }

  function canonicalizeDocumentNumber(value) {
    return normalize(value).replace(/\s+/gu, "").toUpperCase();
  }

  function validateQuery(value) {
    const normalized = normalize(value);
    if (!normalized) return {ok: true, empty: true, normalized, terms: []};
    if (normalized.length > QUERY_LIMITS.maxLength) {
      return {ok: false, empty: false, normalized, terms: [], error: "搜尋文字過長，請縮短至256字以內。"};
    }
    const terms = [...new Set(normalized.split(/[\s,，、;；]+/u).filter(Boolean))];
    if (terms.length > QUERY_LIMITS.maxTokens || terms.some((term) => term.length > QUERY_LIMITS.maxTokenLength)) {
      return {ok: false, empty: false, normalized, terms: [], error: "搜尋條件過多或單一詞過長，請縮短後再試。"};
    }
    return {ok: true, empty: false, normalized, terms};
  }

  function tokenizeQuery(value) {
    const query = validateQuery(value);
    return query.ok ? query.terms : [];
  }

  function prepareRecords(records) {
    return records.map((record, index) => {
      if (record._prepared) return record;
      return {
        ...record,
        _prepared: true,
        stableOriginalIndex: index,
        normalizedTitle: normalize(record.title),
        normalizedHeadings: normalize((record.headings || []).join(" ")),
        normalizedBreadcrumb: normalize((record.breadcrumb || []).join(" ")),
        normalizedText: normalize(record.text),
        canonicalDocumentNumber: canonicalizeDocumentNumber(record.documentNumber),
      };
    });
  }

  function prepareConceptData(concepts) {
    return concepts.map((concept) => ({
      ...concept,
      normalizedTerms: [...new Set((concept.terms || []).map(normalize).filter(Boolean))],
      normalizedTriggerTerms: [...new Set(
        (concept.triggerTerms || concept.terms || []).map(normalize).filter(Boolean)
      )],
      normalizedRelatedTerms: [...new Set(
        (concept.relatedTerms || concept.terms || []).map(normalize).filter(Boolean)
      )],
    }));
  }

  function prepareIntentData(intents) {
    return intents.map((intent) => ({
      ...intent,
      normalizedTriggers: [...new Set((intent.triggers || []).map(normalize).filter(Boolean))],
    }));
  }

  function prepareSearchData(records, concepts, intents) {
    return {
      records: prepareRecords(records),
      concepts: prepareConceptData(concepts),
      intents: prepareIntentData(intents),
    };
  }

  function expandedConceptTerms(queryInfo, concepts) {
    const expanded = [];
    for (const concept of concepts) {
      const normalizedTriggers = concept.normalizedTriggerTerms
        || (concept.triggerTerms || concept.terms || []).map(normalize);
      const normalizedRelated = concept.normalizedRelatedTerms
        || (concept.relatedTerms || concept.terms || []).map(normalize);
      if (normalizedTriggers.some((term) =>
        queryInfo.terms.some((token) => term.includes(token) || token.includes(term))
      )) {
        expanded.push(...normalizedRelated);
      }
    }
    return [...new Set(expanded)].filter((term) => !queryInfo.terms.includes(term));
  }

  function prepareConcepts(query, concepts) {
    const info = validateQuery(query);
    return info.ok && !info.empty ? expandedConceptTerms(info, prepareConceptData(concepts)) : [];
  }

  function minimalTermDistance(text, terms) {
    if (terms.length < 2) return null;
    const events = [];
    terms.forEach((term, termIndex) => {
      let at = text.indexOf(term);
      let count = 0;
      while (at >= 0 && count < 8) {
        events.push({at, end: at + term.length, termIndex});
        count += 1;
        at = text.indexOf(term, at + Math.max(1, term.length));
      }
    });
    events.sort((a, b) => a.at - b.at || a.end - b.end);
    const counts = new Map();
    let left = 0;
    let best = Infinity;
    for (let right = 0; right < events.length; right += 1) {
      counts.set(events[right].termIndex, (counts.get(events[right].termIndex) || 0) + 1);
      while (counts.size === terms.length && left <= right) {
        best = Math.min(best, events[right].end - events[left].at);
        const key = events[left].termIndex;
        counts.set(key, counts.get(key) - 1);
        if (!counts.get(key)) counts.delete(key);
        left += 1;
      }
    }
    return Number.isFinite(best) ? best : null;
  }

  function scorePreparedRecord(record, queryInfo, concepts, intents) {
    const originalTerms = queryInfo.terms;
    const relatedTerms = expandedConceptTerms(queryInfo, concepts);
    const fields = {
      title: record.normalizedTitle,
      headings: record.normalizedHeadings,
      breadcrumb: record.normalizedBreadcrumb,
      body: record.normalizedText,
    };
    const matches = {};
    for (const [name, value] of Object.entries(fields)) {
      matches[name] = originalTerms.filter((term) => value.includes(term));
    }
    let score = matches.title.length * WEIGHTS.title
      + matches.headings.length * WEIGHTS.heading
      + matches.breadcrumb.length * WEIGHTS.breadcrumb
      + matches.body.length * WEIGHTS.body;
    score += relatedTerms.filter((term) => fields.title.includes(term)).length * WEIGHTS.conceptTitle;
    score += relatedTerms.filter((term) => fields.body.includes(term)).length * WEIGHTS.conceptBody;
    if (record.normalizedTitle === queryInfo.normalized) score += WEIGHTS.exactTitle;
    else if (queryInfo.normalized.length >= 2 && record.normalizedTitle.includes(queryInfo.normalized)) score += WEIGHTS.phraseTitle;
    if (queryInfo.normalized.length >= 8 && record.normalizedText.includes(queryInfo.normalized)) score += WEIGHTS.phraseBody;
    const canonicalQuery = canonicalizeDocumentNumber(queryInfo.normalized);
    if (canonicalQuery && record.canonicalDocumentNumber && canonicalQuery === record.canonicalDocumentNumber) {
      score += WEIGHTS.exactNumber;
    }
    if (originalTerms.length > 1 && originalTerms.every((term) => fields.body.includes(term))) score += WEIGHTS.allTerms;
    const distance = minimalTermDistance(fields.body, originalTerms);
    if (distance !== null && distance <= 180) score += Math.max(0, WEIGHTS.proximity - Math.floor(distance / 3));
    if (record.type === "貸款索引" && matches.title.length) score += WEIGHTS.loanTitle;
    if (record.type === "書表附件" && matches.title.length) score += WEIGHTS.formTitle;
    for (const intent of intents) {
      const triggers = intent.normalizedTriggers || (intent.triggers || []).map(normalize);
      if (triggers.some((trigger) => queryInfo.normalized.includes(trigger)) && intent.preferredTypes.includes(record.type)) {
        score += intent.boost;
      }
    }
    return {score, terms: originalTerms.concat(relatedTerms), originalTerms, relatedTerms};
  }

  function scoreRecord(record, query, concepts, intents) {
    const info = typeof query === "object" && query.normalized ? query : validateQuery(query);
    if (!info.ok || info.empty) return {score: 0, terms: [], originalTerms: [], relatedTerms: []};
    const prepared = record._prepared ? record : prepareRecords([record])[0];
    return scorePreparedRecord(prepared, info, prepareConceptData(concepts), prepareIntentData(intents));
  }

  function stableCompare(a, b) {
    return b.score - a.score
      || (a.record.pdfPage || 0) - (b.record.pdfPage || 0)
      || a.record.stableOriginalIndex - b.record.stableOriginalIndex;
  }

  function diversifyResults(items) {
    const sorted = items.slice().sort(stableCompare);
    const window = sorted.slice(0, 80);
    const tail = sorted.slice(80);
    const selected = [];
    const scopeCounts = new Map();
    const groupCounts = new Map();
    while (window.length) {
      let bestIndex = 0;
      let bestScore = -Infinity;
      for (let index = 0; index < window.length; index += 1) {
        const item = window[index];
        const scopeCount = scopeCounts.get(item.record.scope) || 0;
        const groupCount = item.record.scopeGroup ? (groupCounts.get(item.record.scopeGroup) || 0) : 0;
        const adjusted = item.score - Math.max(0, scopeCount - 1) * 18 - Math.max(0, groupCount - 2) * 10;
        if (adjusted > bestScore || (adjusted === bestScore && stableCompare(item, window[bestIndex]) < 0)) {
          bestIndex = index;
          bestScore = adjusted;
        }
      }
      const item = window.splice(bestIndex, 1)[0];
      selected.push({...item, adjustedScore: bestScore});
      scopeCounts.set(item.record.scope, (scopeCounts.get(item.record.scope) || 0) + 1);
      if (item.record.scopeGroup) groupCounts.set(item.record.scopeGroup, (groupCounts.get(item.record.scopeGroup) || 0) + 1);
    }
    return selected.concat(tail.map((item) => ({...item, adjustedScore: item.score})));
  }

  function scopeSet(scope) {
    if (scope === "all" || !scope) return null;
    if (Array.isArray(scope)) return new Set(scope);
    return new Set(String(scope).split(",").map((value) => value.trim()).filter(Boolean));
  }

  function searchRecords(records, query, concepts, intents, type = "all", scope = "all") {
    const queryInfo = validateQuery(query);
    const empty = [];
    if (!queryInfo.ok) {
      empty.error = queryInfo.error;
      return empty;
    }
    if (queryInfo.empty) return empty;
    const preparedRecords = records.length && records[0]._prepared ? records : prepareRecords(records);
    const preparedConcepts = concepts.length && concepts[0].normalizedTerms ? concepts : prepareConceptData(concepts);
    const preparedIntents = intents.length && intents[0].normalizedTriggers ? intents : prepareIntentData(intents);
    const allowedScopes = scopeSet(scope);
    const candidates = preparedRecords.filter((record) => {
      const typeMatch = type === "all" || record.type === type;
      const scopeMatch = !allowedScopes || allowedScopes.has(record.scope) || allowedScopes.has(record.scopeGroup);
      return typeMatch && scopeMatch;
    });
    const scored = candidates.map((record) => ({record, ...scorePreparedRecord(record, queryInfo, preparedConcepts, preparedIntents)}))
      .filter((item) => item.score > 0);
    return diversifyResults(scored);
  }

  function originalBoundaries(text) {
    const values = graphemes(text).map((item) => item.index);
    values.push(text.length);
    return [...new Set(values)].sort((a, b) => a - b);
  }

  function floorBoundary(boundaries, value) {
    let result = 0;
    for (const boundary of boundaries) {
      if (boundary > value) break;
      result = boundary;
    }
    return result;
  }

  function ceilBoundary(boundaries, value) {
    return boundaries.find((boundary) => boundary >= value) ?? boundaries[boundaries.length - 1];
  }

  function createSnippetRange(original, originalTerms, relatedTerms = []) {
    const text = String(original || "");
    const map = normalizeWithMap(text);
    const termInfo = [
      ...[...new Set((originalTerms || []).map(normalize).filter(Boolean))].map((term) => ({term, related: false})),
      ...[...new Set((relatedTerms || []).map(normalize).filter(Boolean))].map((term) => ({term, related: true})),
    ];
    const occurrences = [];
    for (const info of termInfo) {
      let at = map.normalizedText.indexOf(info.term);
      let count = 0;
      while (at >= 0 && count < 8) {
        const endAt = at + info.term.length;
        occurrences.push({
          start: map.startMap[at] ?? 0,
          end: map.endMap[endAt - 1] ?? text.length,
          term: info.term,
          related: info.related,
        });
        count += 1;
        at = map.normalizedText.indexOf(info.term, at + Math.max(1, info.term.length));
      }
    }
    const boundaries = originalBoundaries(text);
    if (!occurrences.length) {
      return {start: 0, end: floorBoundary(boundaries, Math.min(text.length, 160)), matches: []};
    }
    const target = 240;
    let best = null;
    for (const occurrence of occurrences) {
      let start = floorBoundary(boundaries, Math.max(0, occurrence.start - 70));
      let end = floorBoundary(boundaries, Math.min(text.length, start + target));
      if (end - start < target && end === text.length) start = ceilBoundary(boundaries, Math.max(0, end - target));
      const inside = occurrences.filter((item) => item.start >= start && item.end <= end);
      const direct = new Set(inside.filter((item) => !item.related).map((item) => item.term)).size;
      const related = new Set(inside.filter((item) => item.related).map((item) => item.term)).size;
      const span = inside.length ? Math.max(...inside.map((item) => item.end)) - Math.min(...inside.map((item) => item.start)) : target;
      const score = direct * 1000 + related * 100 + inside.length * 5 - span / 1000;
      if (!best || score > best.score || (score === best.score && start < best.start)) best = {start, end, score, inside};
    }
    const ranges = best.inside.sort((a, b) => a.start - b.start || a.end - b.end);
    const merged = [];
    for (const range of ranges) {
      const last = merged[merged.length - 1];
      if (last && range.start < last.end) {
        last.end = Math.max(last.end, range.end);
        last.related = last.related && range.related;
      } else {
        merged.push({start: range.start, end: range.end, related: range.related});
      }
    }
    return {
      start: best.start,
      end: best.end,
      matches: merged.map((range) => ({
        start: range.start,
        end: range.end,
        kind: range.related ? "related" : "direct",
      })),
    };
  }

  global.ManualSearchCore = {
    TYPES, QUERY_LIMITS, WEIGHTS, normalize, normalizeWithMap, canonicalizeDocumentNumber,
    validateQuery, tokenizeQuery, prepareRecords, prepareSearchData, prepareConcepts,
    scoreRecord, diversifyResults, searchRecords, createSnippetRange,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = global.ManualSearchCore;
})(typeof globalThis !== "undefined" ? globalThis : this);
