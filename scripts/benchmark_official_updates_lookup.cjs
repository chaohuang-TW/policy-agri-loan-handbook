#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "site/updates/index.html"), "utf8");
const match = html.match(/<script[^>]*data-official-updates-data[^>]*>([\s\S]*?)<\/script>/);
if (!match) throw new Error("embedded Official Updates lookup data is missing");
const records = JSON.parse(match[1]);
const fixture = JSON.parse(fs.readFileSync(path.join(root, "tests/fixtures/official-updates-lookup.json"), "utf8"));
const queries = fixture.queries.map((item) => item.query);
const context = {window: {}, document: {querySelectorAll: () => []}};
vm.runInNewContext(fs.readFileSync(path.join(root, "assets/js/official-updates-lookup.js"), "utf8"), context);
const sortRecords = context.window.OfficialUpdatesLookup && context.window.OfficialUpdatesLookup.sortRecords;
if (typeof sortRecords !== "function") throw new Error("lookup sort function is not exported");

const samples = 3000;
const timings = [];
for (let index = 0; index < samples; index += 1) {
  const query = queries[index % queries.length];
  const start = process.hrtime.bigint();
  const result = sortRecords(records, query);
  const elapsed = Number(process.hrtime.bigint() - start) / 1e6;
  if (!Array.isArray(result)) throw new Error("lookup result is not an array");
  timings.push(elapsed);
}
timings.sort((a, b) => a - b);
const average = timings.reduce((sum, value) => sum + value, 0) / samples;
const percentile = (p) => timings[Math.min(samples - 1, Math.floor(samples * p))];
const report = {
  samples,
  records: records.length,
  averageMs: Number(average.toFixed(4)),
  p50Ms: Number(percentile(0.5).toFixed(4)),
  p95Ms: Number(percentile(0.95).toFixed(4)),
  maxMs: Number(timings[samples - 1].toFixed(4)),
};
if (report.p95Ms > 50) throw new Error(`Official Updates lookup p95 exceeded 50ms: ${report.p95Ms}`);
console.log(JSON.stringify(report, null, 2));
