#!/usr/bin/env python3
"""Hard-gate semantic precision, short-trigger, and document-number search audit."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROGRAM = r'''
const fs=require("fs"), core=require("./assets/js/search-core.js");
const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const prepared=core.prepareSearchData(read("site/assets/data/search-index.json"),read("data/114/search-concepts.json"),read("data/114/search-intents.json"));
const tasks=[
  {query:"申請資格",terms:["申請資格","申請資格條件","申貸資格","貸款對象","本貸款之對象","救助對象","借款人","申請人","資格條件"]},
  {query:"貸款用途",terms:["貸款用途","資金用途","所需資金"]},
  {query:"貸款額度",terms:["貸款額度","最高貸款額度","最高額度"]},
  {query:"貸款期限 寬緩期",terms:["貸款期限","還款期限","寬緩期","寬限期"]},
  {query:"應備文件",terms:["應備文件","應檢具","應檢附","申請書","證明文件"]},
  {query:"貸放後管理",terms:["貸放後管理","貸款用途及經營狀況查驗","用途查驗","經營狀況查驗"]}
];
const searchable=r=>[r.normalizedTitle,r.normalizedHeadings,r.normalizedBreadcrumb,r.normalizedText,r.canonicalDocumentNumber,r.normalizedKeywords,r.normalizedAliases,r.normalizedSourceTitle].join(" ");
const relevant=(item,task)=>task.terms.some(term=>searchable(item.record).includes(core.normalize(term)));
const taskReports=tasks.map(task=>{const results=core.searchRecords(prepared.records,task.query,prepared.concepts,prepared.intents), top5=results.slice(0,5), top10=results.slice(0,10), top5Relevant=top5.filter(x=>relevant(x,task)).length, top10Relevant=top10.filter(x=>relevant(x,task)).length; return {query:task.query,totalResults:results.length,intentOnlyCount:results.filter(x=>!x.hasRetrievalEvidence).length,top1Relevant:Boolean(results[0]&&relevant(results[0],task)),top5Relevant,top5Precision:top5.length?top5Relevant/top5.length:0,top10Relevant,top10Precision:top10.length?top10Relevant/top10.length:0,directCount:results.filter(x=>x.matchKind==="direct").length,relatedCount:results.filter(x=>x.matchKind==="related").length,exactDocumentCount:results.filter(x=>x.matchKind==="exact-document").length,top10AllHaveRetrievalEvidence:top10.every(x=>x.hasRetrievalEvidence),top10Ids:top10.map(x=>x.record.id),top10MatchReasons:top10.map(x=>({id:x.record.id,matchKind:x.matchKind,matchedOriginalTerms:x.matchedOriginalTerms,matchedRelatedTerms:x.matchedRelatedTerms}))};});
const shortReports=["資格","文件","期限","管理","申請","對象"].map(query=>{const related=core.prepareConcepts(query,prepared.concepts), results=core.searchRecords(prepared.records,query,prepared.concepts,prepared.intents); return {query,taskConceptTriggered:related.some(term=>["貸款對象","應檢具","還款期限","用途查驗"].includes(term)),totalResults:results.length,intentOnlyCount:results.filter(x=>!x.hasRetrievalEvidence).length,directCount:results.filter(x=>x.matchKind==="direct").length,relatedCount:results.filter(x=>x.matchKind==="related").length};});
const documentCases=["農授金字第0955080181號","0955080181","農授金字第1147467200A號","1147467200A"].map(query=>{const results=core.searchRecords(prepared.records,query,prepared.concepts,prepared.intents);return {query,totalResults:results.length,topId:results[0]?.record.id||null,topMatchKind:results[0]?.matchKind||null,topExactDocumentNumberMatch:results[0]?.exactDocumentNumberMatch||false};});
console.log(JSON.stringify({taskReports,shortReports,documentCases}));
'''

def main() -> int:
    node = shutil.which("node")
    if not node:
        print("SEARCH PRECISION AUDIT FAILED: Node.js is required")
        return 1
    result = subprocess.run([node, "-e", PROGRAM], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        return result.returncode
    report = json.loads(result.stdout)
    errors: list[str] = []
    for row in report["taskReports"]:
        if row["intentOnlyCount"] or not row["top1Relevant"] or row["top5Precision"] < .60 or row["top10Precision"] < .50 or not row["top10AllHaveRetrievalEvidence"]:
            errors.append(row["query"])
    for row in report["shortReports"]:
        if row["taskConceptTriggered"] or row["intentOnlyCount"]:
            errors.append(row["query"])
    inside_full, inside_core, outside_full, outside_core = report["documentCases"]
    for row in (inside_full, inside_core):
        if row["topId"] != "interpretations-interpretation-001" or row["topMatchKind"] != "exact-document":
            errors.append(row["query"])
    for row in (outside_full, outside_core):
        if row["totalResults"] != 0:
            errors.append(row["query"])
    output = {"status": "SEARCH PRECISION AUDIT PASSED" if not errors else "SEARCH PRECISION AUDIT FAILED", **report, "errors": errors}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
