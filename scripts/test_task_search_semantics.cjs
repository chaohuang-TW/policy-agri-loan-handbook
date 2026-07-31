"use strict";

const assert = require("assert");
const fs = require("fs");
const core = require("../assets/js/search-core.js");

const read = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const records = read("site/assets/data/search-index.json");
const concepts = read("data/114/search-concepts.json");
const intents = read("data/114/search-intents.json");
const shortcuts = read("data/114/navigation-shortcuts.json");
const pages = read("data/114/pages.json");
const relationships = read("data/114/content-relationships.json");
const prepared = core.prepareSearchData(records, concepts, intents);

const TASKS = [
  {id: "task-eligibility", shortcutId: "task-eligibility", label: "申請資格", query: "申請資格", terms: ["申請資格條件", "申貸資格", "貸款對象", "本貸款之對象", "救助對象"]},
  {id: "task-loan-purpose", shortcutId: "task-purpose", label: "貸款用途", query: "貸款用途", terms: ["貸款用途", "資金用途", "所需資金"]},
  {id: "task-loan-amount", shortcutId: "task-amount", label: "可以貸多少", query: "貸款額度", terms: ["貸款額度", "最高貸款額度", "最高額度"]},
  {id: "task-loan-term", shortcutId: "task-term", label: "期限與寬緩期", query: "貸款期限 寬緩期", terms: ["貸款期限", "還款期限", "寬緩期", "寬限期"]},
  {id: "task-interest", shortcutId: "task-interest", label: "利率", query: "利率 利息差額補貼", terms: ["貸款利率", "利率", "利息差額補貼"]},
  {id: "task-required-documents", shortcutId: "task-documents", label: "應備文件", query: "應備文件 申請書", terms: ["應檢具", "應檢附", "申請書", "證明文件"]},
  {id: "task-post-loan-management", shortcutId: "task-post-loan", label: "貸放後管理", query: "貸放後管理", terms: ["貸放後管理", "貸款用途及經營狀況查驗", "用途查驗", "經營狀況查驗"]},
];

function search(query, scope = "all") {
  return core.searchRecords(prepared.records, query, prepared.concepts, prepared.intents, "all", scope);
}

function matchesTask(record, task) {
  return task.terms.some((term) => record.text.includes(term));
}

function distribution(items, key) {
  return Object.fromEntries([...items.reduce((counts, item) => {
    const value = item.record[key] || "(none)";
    counts.set(value, (counts.get(value) || 0) + 1);
    return counts;
  }, new Map()).entries()].sort());
}

function reportTask(task, scope = "all") {
  const results = search(task.query, scope);
  const top10 = results.slice(0, 10);
  const top5 = results.slice(0, 5);
  const semanticMatches = top10.filter(({record}) => matchesTask(record, task));
  const top5Relevant = top5.filter(({record}) => matchesTask(record, task)).length;
  const top10Relevant = semanticMatches.length;
  const concept = concepts.find((item) => item.id === task.id);
  assert(concept, `missing task concept: ${task.id}`);
  assert((concept.triggerTerms || []).length, `${task.id} has no triggerTerms`);
  assert((concept.relatedTerms || []).length, `${task.id} has no relatedTerms`);
  return {
    id: task.id,
    label: task.label,
    visibleQuery: task.query,
    conceptTerms: {
      triggers: concept.triggerTerms,
      related: concept.relatedTerms,
    },
    totalResults: results.length,
    intentOnlyCount: results.filter((item) => !item.hasRetrievalEvidence).length,
    top1Relevant: Boolean(results[0] && matchesTask(results[0].record, task)),
    top5Relevant,
    top5Precision: top5Relevant / Math.max(1, top5.length),
    top10Relevant,
    top10Precision: top10Relevant / Math.max(1, top10.length),
    directCount: results.filter((item) => item.matchKind === "direct").length,
    relatedCount: results.filter((item) => item.matchKind === "related").length,
    exactDocumentCount: results.filter((item) => item.matchKind === "exact-document").length,
    top10Types: distribution(top10, "type"),
    top10Ids: top10.map(({record}) => record.id),
    top10Titles: top10.map(({record}) => record.title),
    directSourcePhraseMatchCount: results.filter(({record}) => matchesTask(record, task)).length,
    top10SemanticMatchCount: semanticMatches.length,
    contextTitleDistribution: distribution(top10, "contextTitle"),
    firstResult: top10[0] ? {
      id: top10[0].record.id,
      title: top10[0].record.title,
      printedPage: top10[0].record.printedPage,
      contextTitle: top10[0].record.contextTitle,
    } : null,
    pass: results.length > 0
      && results.every((item) => item.hasRetrievalEvidence)
      && results[0] && matchesTask(results[0].record, task)
      && top5Relevant / Math.max(1, top5.length) >= .60
      && top10Relevant / Math.max(1, top10.length) >= .50,
  };
}

const globalReports = TASKS.map((task) => reportTask(task));
globalReports.forEach((report) => assert(report.pass, `${report.label} failed global semantic quality`));

const sampleLoans = ["young-farmer-loan", "farm-machinery-loan", "natural-disaster-low-interest-loan"];
const loanTaskIds = new Set(
  shortcuts.filter((item) => item.kind.split(":")[1]?.split(",").includes("loan")).map((item) => item.id)
);
const loanReports = [];
for (const loanId of sampleLoans) {
  for (const task of TASKS.filter((item) => loanTaskIds.has(item.shortcutId))) {
    const scope = `loan:${loanId}`;
    const results = search(task.query, scope);
    const leakedScopeCount = results.filter(({record}) => record.scopeGroup !== scope).length;
    const semanticEvidence = results.slice(0, 10).filter(({record}) => matchesTask(record, task)).length;
    const report = {
      loanId,
      task: task.label,
      resultCount: results.length,
      leakedScopeCount,
      topResult: results[0]?.record.title || null,
      semanticEvidence,
      pass: results.length > 0 && leakedScopeCount === 0 && semanticEvidence > 0,
    };
    assert(report.pass, `${loanId} ${task.label} failed scoped semantics`);
    loanReports.push(report);
  }
}

const sectionIds = ["agricultural-development-fund-rules", "natural-disaster-rules"];
const sectionContext = {
  "agricultural-development-fund-rules": "common",
  "natural-disaster-rules": "disaster",
};
const sectionReports = [];
for (const sectionId of sectionIds) {
  const section = relationships.sections.find((item) => item.id === sectionId);
  const scopes = [...new Set(pages.filter((page) =>
    page.printedPage !== null
    && page.printedPage >= section.printedPageStart
    && page.printedPage <= section.printedPageEnd
  ).map((page) => `section:${page.chapterId}`))];
  const visibleIds = new Set(shortcuts.filter((item) =>
    item.kind.split(":")[1]?.split(",").includes(sectionContext[sectionId])
  ).map((item) => item.id));
  for (const task of TASKS.filter((item) => visibleIds.has(item.shortcutId))) {
    const results = search(task.query, scopes);
    const leakedScopeCount = results.filter(({record}) =>
      record.type === "原文頁面" && !scopes.includes(record.scope)
    ).length;
    const semanticEvidence = results.slice(0, 10).filter(({record}) => matchesTask(record, task)).length;
    const report = {
      sectionId,
      task: task.label,
      resultCount: results.length,
      leakedScopeCount,
      topResult: results[0]?.record.title || null,
      semanticEvidence,
      pass: results.length > 0 && leakedScopeCount === 0 && semanticEvidence > 0,
    };
    assert(report.pass, `${sectionId} ${task.label} failed scoped semantics`);
    sectionReports.push(report);
  }
}

console.log(JSON.stringify({
  status: "TASK SEARCH SEMANTICS PASSED",
  tasks: globalReports,
  sampleLoans: loanReports,
  sampleSections: sectionReports,
}, null, 2));
