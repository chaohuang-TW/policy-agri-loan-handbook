"use strict";

const assert = require("assert");
const fs = require("fs");
const core = require("../assets/js/search-core.js");

const read = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const records = read("site/assets/data/search-index.json");
const concepts = read("data/114/search-concepts.json");
const intents = read("data/114/search-intents.json");
const loans = read("data/114/loan-programs.json");
const interpretations = read("data/114/interpretations.json");
const forms = read("data/114/forms.json");
const faqs = read("data/114/faq.json");
const appendices = read("data/114/appendices.json");
const relationships = read("data/114/content-relationships.json");
const pages = read("data/114/pages.json");
const prepared = core.prepareSearchData(records, concepts, intents);

function search(query, type = "all", scope = "all") {
  return core.searchRecords(prepared.records, query, prepared.concepts, prepared.intents, type, scope);
}

function topContains(query, predicate, limit, type = "all", scope = "all") {
  const found = search(query, type, scope).slice(0, limit).some(({record}) => predicate(record));
  assert(found, `top ${limit} missing expected result for: ${query}`);
}

const fixed = [
  ["青農", (record) => /青壯年農民/.test(record.text)],
  ["買農地", (record) => /購買耕地/.test(record.text)],
  ["寬限期", (record) => /寬緩期/.test(record.text)],
  ["農機申請書", (record) => /農機/.test(record.text)],
  ["農授金字第0955080181號", (record) => record.documentNumber === "農授金字第0955080181號"],
  ["天災", (record) => /天然災害/.test(record.text)],
  ["農企業", (record) => /農企業/.test(record.text)],
  ["電商", (record) => /電子商務/.test(record.text)],
  ["復耕", (record) => /復耕復建/.test(record.text)],
  ["週轉金", (record) => /週轉金/.test(record.text)],
  ["常見問題", (record) => record.type === "常見問答"],
  ["申請書", (record) => record.type === "書表附件"],
];
fixed.forEach(([query, predicate]) => topContains(query, predicate, 20));

for (const loan of loans) {
  topContains(
    loan.title,
    (record) => record.id === `loan-${loan.id}`,
    5
  );
  const group = `loan:${loan.id}`;
  const members = records.filter((record) => record.scopeGroup === group);
  assert(members.some((record) => record.type === "貸款索引"), `${group} missing loan index`);
  assert(members.some((record) => record.type === "原文頁面"), `${group} missing source page`);
  if (loan.hasInterpretations) {
    assert(members.some((record) => record.type === "函釋"), `${group} missing interpretation`);
  }
  const scoped = search(loan.title, "all", group);
  assert(scoped.length, `${group} query returned no results`);
  assert(scoped.every(({record}) => record.scopeGroup === group), `${group} leaked another group`);
}

function fullWidthVariant(value) {
  const spaced = value.replace(/第/u, "第 ").replace(/號/u, " 號");
  return [...spaced].map((character) => {
    const code = character.codePointAt(0);
    if (code >= 0x21 && code <= 0x7e) return String.fromCodePoint(code + 0xfee0);
    return character;
  }).join("");
}

for (const item of interpretations) {
  const expected = `interpretations-${item.id}`;
  for (const query of [item.documentNumber, fullWidthVariant(item.documentNumber)]) {
    topContains(query, (record) => record.id === expected, 3);
  }
  assert.strictEqual(
    core.canonicalizeDocumentNumber(item.documentNumber),
    core.canonicalizeDocumentNumber(fullWidthVariant(item.documentNumber))
  );
}

for (const item of forms) {
  topContains(item.title, (record) => record.id === `forms-${item.id}`, 5);
}
for (const item of faqs) {
  topContains(item.title, (record) => record.id === `faq-${item.id}`, 5);
  const record = records.find((candidate) => candidate.id === `faq-${item.id}`);
  assert(record && !record.scope.startsWith("form:"), `${item.id} has form scope`);
}
for (const item of appendices) {
  topContains(item.title, (record) => record.id === `forms-${item.id}`, 5);
}

for (const section of relationships.sections) {
  const sectionPages = pages.filter((page) =>
    page.printedPage !== null
    && page.printedPage >= section.printedPageStart
    && page.printedPage <= section.printedPageEnd
  );
  const scopes = [...new Set(sectionPages.map((page) => `section:${page.chapterId}`))];
  assert(scopes.length, `${section.id} has no scopes`);
  const sectionRecords = records.filter((record) =>
    record.type === "原文頁面" && scopes.includes(record.scope)
  );
  assert(sectionRecords.length, `${section.id} has no source records`);
  const broad = search("貸款", "原文頁面", scopes);
  assert(broad.every(({record}) => scopes.includes(record.scope)), `${section.id} leaked source pages`);
}

const unicodeCases = [
  ["一般中文農機", "農", "農"],
  ["ABCdef", "D", "d"],
  ["ＡＢＣ", "b", "Ｂ"],
  ["１２３", "2", "２"],
  ["a   b", "b", "b"],
  ["a\tb", "b", "b"],
  ["a\nb", "b", "b"],
  ["a\r\nb", "b", "b"],
  ["農🚜機申請書", "機", "機"],
  ["農機🚜", "機", "機"],
  ["農🚜機", "🚜", "🚜"],
  ["😀abc", "a", "a"],
  ["😀😀abc", "b", "b"],
  ["e\u0301cole", "é", "e\u0301"],
  ["①項", "1", "①"],
  ["㍿會社", "株式会社", "㍿"],
  ["農，機", "，", "，"],
  ["農（機）", "(", "（"],
  ["機機機", "機", "機"],
  ["ababa", "aba", "aba"],
];
for (const [text, query, expected] of unicodeCases) {
  const mapped = core.normalizeWithMap(text);
  assert.strictEqual(mapped.normalizedText.length, mapped.startMap.length);
  assert.strictEqual(mapped.normalizedText.length, mapped.endMap.length);
  const snippet = core.createSnippetRange(text, [query]);
  assert(snippet.matches.length, `no Unicode match for ${JSON.stringify([text, query])}`);
  const match = snippet.matches[0];
  assert.strictEqual(text.slice(match.start, match.end), expected);
}

const longCases = [
  ["甲" + "中".repeat(1000) + "乙", ["甲", "乙"]],
  ["甲" + "中".repeat(1500) + "乙" + "尾".repeat(1500) + "丙", ["甲", "乙", "丙"]],
  ["農機".repeat(100), ["農機"]],
  ["青壯年農民".repeat(100), ["青農"], ["青壯年農民"]],
  ["甲".repeat(5000), ["甲"]],
  [records.reduce((a, b) => a.text.length > b.text.length ? a : b).text, ["貸款"]],
];
let longestSnippet = 0;
for (const [text, direct, related = []] of longCases) {
  const snippet = core.createSnippetRange(text, direct, related);
  longestSnippet = Math.max(longestSnippet, snippet.end - snippet.start);
  assert(snippet.end - snippet.start <= 320, "snippet exceeded 320 UTF-16 units");
  assert(snippet.start >= 0 && snippet.end <= text.length);
  for (let index = 1; index < snippet.matches.length; index += 1) {
    assert(snippet.matches[index - 1].end <= snippet.matches[index].start, "overlapping marks");
  }
}

assert.deepStrictEqual(search("", "all"), []);
assert.deepStrictEqual(search("   ", "all"), []);
assert.doesNotThrow(() => core.validateQuery("字".repeat(256)));
assert.strictEqual(core.validateQuery("字".repeat(257)).ok, false);
assert.strictEqual(core.validateQuery("字".repeat(5000)).ok, false);
assert.strictEqual(core.validateQuery(("農機 ").repeat(5000)).ok, false);
assert.doesNotThrow(() => search("<img src=x onerror=alert(1)>"));
assert.deepStrictEqual(core.tokenizeQuery("農機 農機 農機"), ["農機"]);
const first = search("青農").map(({record}) => record.id);
assert.deepStrictEqual(first, search("青農").map(({record}) => record.id));

// Evidence is a retrieval gate, never an inference from a positive score.
const syntheticConcepts = [{id: "task-eligibility", triggerTerms: ["申請資格"], relatedTerms: ["貸款對象", "完全未出現"]}, {id: "legacy", terms: ["青農", "青壯年農民"]}];
const syntheticIntents = [{triggers: ["申請資格"], preferredTypes: ["原文頁面"], boost: 999}];
const synthetic = core.prepareSearchData([
  {id: "direct", type: "原文頁面", title: "規定", text: "申請資格應符合規定。", scope: "all"},
  {id: "related", type: "原文頁面", title: "規定", text: "貸款對象為農民。", scope: "all"},
  {id: "intent-only", type: "原文頁面", title: "規定", text: "完全無關文字。", scope: "all"},
  {id: "document", type: "函釋", title: "函釋", text: "正文無文號。", documentNumber: "農授金字第1147467200A號", scope: "all"},
  {id: "title-only", type: "原文頁面", title: "申請資格", text: "正文沒有對應詞。", scope: "all"},
], syntheticConcepts, syntheticIntents);
const syntheticResults = core.searchRecords(synthetic.records, "申請資格", synthetic.concepts, synthetic.intents);
assert(!syntheticResults.some((item) => item.record.id === "intent-only"), "intent-only record entered results");
assert(syntheticResults.every((item) => item.hasRetrievalEvidence), "formal result lacks retrieval evidence");
const directFixture = syntheticResults.find((item) => item.record.id === "direct");
assert(directFixture.hasDirectEvidence && directFixture.matchedOriginalTerms.includes("申請資格"));
const relatedFixture = syntheticResults.find((item) => item.record.id === "related");
assert(relatedFixture.hasRelatedEvidence && relatedFixture.matchedRelatedTerms.includes("貸款對象"));
const titleFixture = syntheticResults.find((item) => item.record.id === "title-only");
assert(titleFixture.matchedTitleTerms.includes("申請資格") && !titleFixture.matchedBodyTerms.includes("申請資格"));
const documentFixture = core.searchRecords(synthetic.records, "1147467200A", synthetic.concepts, synthetic.intents)[0];
assert(documentFixture.record.id === "document" && documentFixture.exactDocumentNumberMatch && documentFixture.matchKind === "exact-document");
assert.deepStrictEqual(relatedFixture.matchedOriginalTerms, []);
assert.deepStrictEqual(relatedFixture.matchedRelatedTerms, ["貸款對象"]);
assert(!core.prepareConcepts("資格", syntheticConcepts).includes("貸款對象"), "short task token triggered concept");
assert(core.prepareConcepts("青農", syntheticConcepts).includes("青壯年農民"), "legacy concept compatibility failed");

const indexedDocument = "農授金字第0955080181號";
const indexedDocumentId = "interpretations-interpretation-001";
for (const query of [indexedDocument, "0955080181"]) {
  const results = search(query);
  assert.strictEqual(results[0]?.record.id, indexedDocumentId, `${query} did not rank indexed document first`);
  assert(results[0].exactDocumentNumberMatch && results[0].matchKind === "exact-document");
}
assert.strictEqual(search("農授金字第1147467200A號").length, 0);
assert.strictEqual(search("1147467200A").length, 0);
assert.deepStrictEqual(first, search("青農").map(({record}) => record.id));

assert(!records.some((record) => /手冊頁 None|undefined|\[object Object\]|\bnan\b/i.test(record.text)));
assert(!records.some((record) => String(record.documentNumber || "").includes("日農授金字第")));
assert.strictEqual(records.filter((record) => record.type === "原文頁面" && record.scopeGroup).length, 215);
assert.strictEqual(records.filter((record) => record.type === "函釋" && record.scopeGroup).length, 56);
assert.strictEqual(records.filter((record) => record.type === "書表附件" && record.scopeGroup).length, 21);

console.log(JSON.stringify({
  status: "SEARCH CORE TEST PASSED",
  fixedQueries: `${fixed.length}/${fixed.length}`,
  loanTitles: `${loans.length}/${loans.length}`,
  documentNumbers: `${interpretations.length}/${interpretations.length}`,
  formTitles: `${forms.length}/${forms.length}`,
  faqTitles: `${faqs.length}/${faqs.length}`,
  appendixTitles: `${appendices.length}/${appendices.length}`,
  sections: `${relationships.sections.length}/${relationships.sections.length}`,
  unicode: `${unicodeCases.length}/${unicodeCases.length}`,
  longestSnippet
}, null, 2));
