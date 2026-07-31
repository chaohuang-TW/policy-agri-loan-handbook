"use strict";

const crypto = require("crypto");
const fs = require("fs");
const vm = require("vm");
const {execFileSync} = require("child_process");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const BASE = "b8e7a177f631e19c35121a40ce6aa0cc5c87aed2";
const GENERATED_AT = new Date().toISOString();
const QUERIES = [
  "申請資格", "資格", "貸款用途", "用途", "貸款額度", "額度", "貸款期限", "期限",
  "寬緩期", "應備文件", "文件", "貸放後管理", "管理", "農授金字第0955080181號",
  "0955080181", "農授金字第1147467200A號", "1147467200A", "青壯年農民", "農機",
  "天然災害", "利率", "申請書"
];
const read = (name) => JSON.parse(fs.readFileSync(path.join(ROOT, name), "utf8"));
const records = read("site/assets/data/search-index.json");
const concepts = read("data/114/search-concepts.json");
const intents = read("data/114/search-intents.json");

function loadCore(source, filename) {
  const sandbox = {module: {exports: {}}, exports: {}, globalThis: {}};
  vm.runInNewContext(source, sandbox, {filename});
  return sandbox.module.exports;
}

function sha256(source) {
  return crypto.createHash("sha256").update(source).digest("hex");
}

function evidence(core, item, query, relatedTerms) {
  if (typeof item.hasRetrievalEvidence === "boolean") return item;
  const terms = core.tokenizeQuery(query);
  const record = item.record;
  const fields = [
    record.normalizedTitle, record.normalizedHeadings, record.normalizedBreadcrumb,
    record.normalizedText, record.canonicalDocumentNumber
  ].filter(Boolean);
  const matchedOriginalTerms = terms.filter((term) => fields.some((field) => field.includes(term)));
  const matchedRelatedTerms = relatedTerms.filter((term) => fields.some((field) => field.includes(term)));
  const canonical = core.canonicalizeDocumentNumber(query);
  const exactDocumentNumberMatch = Boolean(canonical && record.canonicalDocumentNumber &&
    (record.canonicalDocumentNumber === canonical || record.canonicalDocumentNumber.includes(canonical)));
  return {
    ...item, matchedOriginalTerms, matchedRelatedTerms, exactDocumentNumberMatch,
    hasDirectEvidence: matchedOriginalTerms.length > 0,
    hasRelatedEvidence: matchedRelatedTerms.length > 0,
    hasStructuredEvidence: exactDocumentNumberMatch,
    hasRetrievalEvidence: matchedOriginalTerms.length > 0 || matchedRelatedTerms.length > 0 || exactDocumentNumberMatch,
    matchKind: exactDocumentNumberMatch ? "exact-document" : matchedOriginalTerms.length ? "direct" :
      matchedRelatedTerms.length ? "related" : "intent-only"
  };
}

function run(core) {
  const prepared = core.prepareSearchData(records, concepts, intents);
  return QUERIES.map((query) => {
    const relatedTerms = core.prepareConcepts(query, prepared.concepts);
    const results = core.searchRecords(prepared.records, query, prepared.concepts, prepared.intents)
      .map((item) => evidence(core, item, query, relatedTerms));
    return {
      query,
      totalResults: results.length,
      intentOnlyCount: results.filter((item) => !item.hasRetrievalEvidence).length,
      directMatchCount: results.filter((item) => item.hasDirectEvidence).length,
      relatedMatchCount: results.filter((item) => item.hasRelatedEvidence && !item.hasDirectEvidence).length,
      exactDocumentNumberCount: results.filter((item) => item.exactDocumentNumberMatch).length,
      top10ResultIds: results.slice(0, 10).map((item) => item.record.id),
      top10MatchReasons: results.slice(0, 10).map((item) => ({
        id: item.record.id,
        matchKind: item.matchKind,
        matchedOriginalTerms: item.matchedOriginalTerms || [],
        matchedRelatedTerms: item.matchedRelatedTerms || []
      }))
    };
  });
}

const oldSource = execFileSync("git", ["show", `${BASE}:assets/js/search-core.js`], {cwd: ROOT, encoding: "utf8"});
const newSource = fs.readFileSync(path.join(ROOT, "assets/js/search-core.js"), "utf8");
const before = {
  baselineCommit: BASE,
  source: "pre-change search core",
  searchCoreSha256: sha256(oldSource),
  generatedAt: GENERATED_AT,
  queries: run(loadCore(oldSource, "search-core-before.js"))
};
const after = {
  workingTreeBaseCommit: BASE,
  source: "beta.2.8 working-tree search core",
  searchCoreSha256: sha256(newSource),
  generatedAt: GENERATED_AT,
  queries: run(loadCore(newSource, "search-core-after.js"))
};
fs.mkdirSync(path.join(ROOT, "reports"), {recursive: true});
fs.writeFileSync(path.join(ROOT, "reports/search-precision-before.json"), JSON.stringify(before, null, 2) + "\n");
fs.writeFileSync(path.join(ROOT, "reports/search-precision-after.json"), JSON.stringify(after, null, 2) + "\n");
console.log(JSON.stringify({before: before.searchCoreSha256, after: after.searchCoreSha256, queries: QUERIES.length}, null, 2));
