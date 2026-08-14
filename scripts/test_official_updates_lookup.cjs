#!/usr/bin/env node
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("assets/js/official-updates-lookup.js", "utf8");
const context = {window: {}, document: {querySelectorAll: () => []}};
vm.runInNewContext(source, context, {filename: "official-updates-lookup.js"});
const lookup = context.window.OfficialUpdatesLookup;
assert.ok(lookup, "lookup exports are available");

const record = {
  id: "synthetic-farmer-relief",
  officialTitle: "115年農民紓困貸款之貸款對象",
  documentNumber: "農授金字第1147467500B號",
  officialAgency: "農業部",
  sourceTypeLabel: "函示",
  relationEvidence: "政策性貸款",
  relatedLoanTitles: ["農民紓困貸款"],
  relatedSectionTitles: ["各項貸款規定"],
  publishedDate: "2025-12-19",
};

assert.deepEqual(Array.from(lookup.tokenizeQuery("農民 貸款")), ["農民", "貸款"]);
assert.deepEqual(Array.from(lookup.tokenizeQuery("農民　貸款")), ["農民", "貸款"]);
assert.deepEqual(Array.from(lookup.tokenizeQuery("農民\t貸款")), ["農民", "貸款"]);
assert.ok(lookup.score(record, "農民 對象") > 0, "non-contiguous AND query matches");
assert.equal(lookup.score(record, "農民對象"), 0, "concatenated phrase is not present");
assert.equal(lookup.score(record, "農民 不存在"), 0, "AND query rejects missing token");
assert.ok(lookup.score(record, "農民  對象") > 0, "double-space query matches");
assert.ok(lookup.score(record, "農民\t對象") > 0, "tab query matches");

const exact = { ...record, id: "exact-title", officialTitle: "農民紓困貸款" };
const broader = { ...record, id: "broader-title", officialTitle: "115年農民紓困貸款之貸款對象" };
assert.equal(lookup.sortRecords([broader, exact], "農民紓困貸款")[0].id, "exact-title", "full phrase ranking is preserved");

console.log(JSON.stringify({status: "OFFICIAL UPDATES LOOKUP JS TEST PASSED", checks: 9}, null, 2));
