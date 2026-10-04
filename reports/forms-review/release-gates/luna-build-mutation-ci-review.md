# beta.3.3 build / mutation / CI Luna readonly review

Reviewer: actual gpt-6-luna subagent in this conversation. This is model review,
not human confirmation. `humanReviewed` remains false. The earlier forms-source
review does not cover these new programs.

## Review history

1. FAIL: dict diagnostic formatting masked the original Node assertion; case 54
   reached the earlier intent-only evidence assertion, not the narrower later
   assertion initially expected.
2. FAIL: raw diagnostics inside the fixture would contaminate the UX validator;
   shallow CI checkout did not ensure the fixed source-review Git baseline.
3. PASS: both issues corrected with user approval. Raw diagnostics are retained
   outside each fixture; checkout uses `fetch-depth: 0`. Causal assertions remain
   exact and source-bound; arbitrary nonzero exits or runtime errors do not count.

## Reviewed unique files

- scripts/build_all.py
- scripts/test_build_reproducibility.py
- scripts/test_validator_mutations.py
- scripts/test_reference_lookup_mutations.py
- scripts/test_official_updates_lookup_mutations.py
- scripts/audit_forms_regression.py
- scripts/audit_forms_source.py
- .github/workflows/pages.yml
- README.md
- CHANGELOG.md

Latest approved input checksums:

- scripts/audit_forms_regression.py: `689f239611a02c0294dd8686850624cdf1f9a5bbf7e71f8095e0568a8e53a276`
- .github/workflows/pages.yml: `949efe2e78cbb76f98a6f7e0916db419e418a0d669f9f1f32f94bb27193590b2`

The reviewer performed readonly code inspection, no test execution, build, file
changes, commit, push or deployment. At review completion the 70/12/16 execution
gates remained pending; this PASS is not their runtime result.

All fixtures are independent byte copies retained outside the Pages artifact.
Existing permissions are unchanged; deployment remains main-only. No deletion
or business-content changes were found in the reviewed new release programs.
The 12/16 summaries do not carry a per-row raw-log field; their retained run path
and case number locate the corresponding sibling `validator-logs/case-NN` JSON.
