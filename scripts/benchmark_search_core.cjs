"use strict";

const {performance} = require("perf_hooks");
const fs = require("fs");
const core = require("../assets/js/search-core.js");
const read = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const records = read("site/assets/data/search-index.json");
const concepts = read("data/114/search-concepts.json");
const intents = read("data/114/search-intents.json");
const loans = read("data/114/loan-programs.json");
const forms = read("data/114/forms.json");
const interpretations = read("data/114/interpretations.json");

function timed(fn, repeats = 20) {
  for (let index = 0; index < 3; index += 1) fn();
  const values = [];
  for (let index = 0; index < repeats; index += 1) {
    const start = performance.now();
    fn();
    values.push(performance.now() - start);
  }
  return values;
}
function percentile(values, fraction) {
  const sorted = values.slice().sort((a, b) => a - b);
  return sorted[Math.min(sorted.length - 1, Math.ceil(sorted.length * fraction) - 1)];
}
function summarize(values) {
  return {
    average: values.reduce((sum, value) => sum + value, 0) / values.length,
    p50: percentile(values, .5),
    p95: percentile(values, .95),
    max: Math.max(...values)
  };
}

const prepareStart = performance.now();
const prepared = core.prepareSearchData(records, concepts, intents);
const prepareMs = performance.now() - prepareStart;
const fixedQueries = [
  "青農", "買農地", "寬限期", "農機申請書", "農授金字第0955080181號", "天災",
  "農企業", "電商", "復耕", "週轉金", "常見問題", "申請書"
];
const coverageQueries = [
  ...fixedQueries, ...loans.map((item) => item.title), ...forms.map((item) => item.title),
  ...interpretations.map((item) => item.documentNumber),
  "農", "農業天然災害低利貸款規定", "農".repeat(100), "農".repeat(256)
];
const queryTimes = [];
for (const query of coverageQueries) {
  queryTimes.push(...timed(() =>
    core.searchRecords(prepared.records, query, prepared.concepts, prepared.intents)
  ));
}
const scopeTimes = timed(() =>
  core.searchRecords(prepared.records, "貸款", prepared.concepts, prepared.intents, "all", "loan:young-farmer-loan")
, 100);
const typeTimes = timed(() =>
  core.searchRecords(prepared.records, "申請書", prepared.concepts, prepared.intents, "書表附件")
, 100);
const oversized = ["字".repeat(5000), ("農機 ").repeat(5000)];
const oversizedTimes = timed(() => oversized.forEach((query) =>
  core.searchRecords(prepared.records, query, prepared.concepts, prepared.intents)
), 100);
const emptyTimes = timed(() => {
  core.searchRecords(prepared.records, "", prepared.concepts, prepared.intents);
  core.searchRecords(prepared.records, "   ", prepared.concepts, prepared.intents);
}, 100);

const general = summarize(queryTimes);
const scope = summarize(scopeTimes);
const type = summarize(typeTimes);
const defensive = summarize(oversizedTimes);
const empty = summarize(emptyTimes);
const report = {prepareMs, general, scope, type, defensive, empty, samples: queryTimes.length};
console.log(JSON.stringify(report, null, 2));

const failures = [];
if (prepareMs > 1000) failures.push(`prepareRecords ${prepareMs.toFixed(2)}ms > 1000ms`);
if (general.average > 100) failures.push(`general average ${general.average.toFixed(2)}ms > 100ms`);
if (general.p95 > 250) failures.push(`general p95 ${general.p95.toFixed(2)}ms > 250ms`);
if (general.max > 500) failures.push(`general max ${general.max.toFixed(2)}ms > 500ms`);
if (scope.p95 > 200) failures.push(`scope p95 ${scope.p95.toFixed(2)}ms > 200ms`);
if (type.p95 > 200) failures.push(`type p95 ${type.p95.toFixed(2)}ms > 200ms`);
if (defensive.max > 50) failures.push(`oversized defense ${defensive.max.toFixed(2)}ms > 50ms`);
if (empty.max > 10) failures.push(`empty query ${empty.max.toFixed(2)}ms > 10ms`);
if (Math.max(general.max, scope.max, type.max, defensive.max, empty.max) > 1000) {
  failures.push("a search exceeded 1 second");
}
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
