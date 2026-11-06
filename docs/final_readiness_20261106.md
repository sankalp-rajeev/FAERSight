# Final validation and project-readiness audit

November 6, 2026. Baseline `f6816ffe877d5f5a51b6a869985ddde7905cf101`.
Repository engineering evidence only; not graded report or presentation prose.

**Overall status: PARTIAL.** Core computations and captured Explorer verification
are complete. Technical evidence is available for student-authored deliverables;
student source/alias/benchmark signoff, final interpretation, final-template/Canvas
confirmation and the actual report/slides/upload receipts are outstanding.
`scientific_findings_validated` remains false.

Status meanings: **COMPLETE** = the stated bounded criterion has concrete evidence;
**PARTIAL** = evidence covers only part of the criterion or a human gate remains;
**MISSING** = the required deliverable or confirmation was not found. These are
audit findings, not edits to historical PRD checkboxes or student reviewer fields.

## Case audit and mapping validation

The [15-case report](case_source_evidence_review_20261106.md) was independently
rerun against the original checksum-pinned ZIP/extracted files, `cases.json`,
the PS mart and the PS+SS mart. All 15 cases agree: **15 DEMO, 679 DRUG and 131
REAC rows**, with source-column, physical-row, mapping, role, reaction, exposure
and basket checks. No discrepancy was found. Checklist fields remain empty and
packet verdicts remain pending; this is not student manual signoff.

Every reviewed case has only one DEMO row in the selected quarter. The selected
numeric maximum agrees within 2025 Q4, but the real sample does not exercise
competing historical versions. Cross-quarter ordering is exercised by synthetic
tests; no original earlier/later-quarter history was acquired. **Unresolved:
global longitudinal latest-version status cannot be asserted.** The existing
one-quarter design is valid within its stated scope; adding history would be a
separate scope/data decision, not a silent fix.

The [independent regulatory review](rosuvastatin_zinc_reference_review_20261106.md)
supports both exact `ROSUVASTATIN ZINC -> rosuvastatin` SS ingredient mappings.
This resolves the earlier lack of external ingredient evidence at the engineering
level. It does not prove brand/strength, causal association, clinical dose
equivalence in these cases, or student approval. Frozen maps/results are unchanged.

## Verification record

- **Local full suite: COMPLETE.** 192 passed, zero failures/errors/skips, WEKA
  enabled; current run 82.95 s. Python 3.14.3, pinned WEKA/JDK; XML retained locally
  at `.tools/readiness-20261106-tests.xml`.
- **Fresh source/Python environment: COMPLETE for the tested scope.** A Git archive
  of `f6816ff` was unpacked into `.tools/readiness-clean-20261106`, with a new
  Python 3.11.14 venv installed from `uv.lock`. Tests ran from that directory:
  **192 passed**, zero failures/errors/skips, 88.43 s. Installed imports resolve
  to that source export. Verified WEKA/Bounce jars, the existing JDK and a pinned
  host plotting environment were reused. No FDA database/results were copied.
  The initial offline dependency install lacked the CPython-3.11 DuckDB wheel;
  the subsequent locked network install succeeded.
- **Clean synthetic reproduction: COMPLETE.** The isolated environment also ran
  `reproduce-fixture` successfully (N=10) and validated the frozen experiment
  configuration. Its `transactions.arff`, `case_index.csv`, `signal_counts.csv`
  and `comparison.csv` match the existing fixture outputs byte for byte. This
  is fixture validation, not another real-data experiment.
- **GitHub Actions: COMPLETE for current baseline CI.** [Run 42262757742](https://github.com/sankalp-rajeev/FAERSight/actions/runs/42262757742)
  succeeded for `f6816ff`. Job logs report **173 passed / 19 skipped** on Ubuntu
  Python 3.11/Java 21 and a successful actual-WEKA synthetic workflow. The skipped
  tests require the historical Windows showcase runtime. Green CI does not mean
  all 192 tests passed on Linux.
- **Lint/format/config: COMPLETE.** Ruff lint and formatting checks pass; frozen
  configuration has no pending scope values. No implementation changes were made.
- **Artifact integrity: COMPLETE within recorded inventories.** Existing auditors
  verify **108 frozen core files**, **393 protected prior files**, **1,096 primary**
  and **1,106 sensitivity generated artifacts**, source/projection provenance,
  metric rankings/charts and unchanged full-data mining invocation inventory.
  The original preparation auditor's GUI-pending fields remain historical.
- **Full current-clone FDA rerun: PARTIAL.** Not repeated because this checkpoint
  forbids additional real-data mining. The historical
  [fresh-clone record](../artifacts/manifests/2025Q4-statins-sensitivity/fresh_clone_reproduction.json)
  reports 10 primary and 17 sensitivity deterministic artifact matches and 1,077
  raw-log matches per experiment. It explicitly used the same host, cached
  archive/jars and a hashed then-uncommitted milestone overlay. Its failed
  attempts/recovery remain disclosed. This supports bounded reproducibility,
  not universal all-artifact/OS equivalence.

## Functional requirements: PRD FR inventory

**26 COMPLETE / 1 PARTIAL / 0 MISSING (27 total).** COMPLETE applies to technical
criteria and frozen scope; student interpretation is counted separately.

- **FR-DATA-01 COMPLETE** - official archive/provenance and SHA-256:
  [data manifest](../artifacts/manifests/2025Q4-statins/data_manifest.json),
  [acquisition implementation](../src/faersight/acquire.py).
- **FR-DATA-02 COMPLETE** - all three source schemas/counts and integration:
  [integration manifest](../artifacts/manifests/2025Q4-statins/integration_manifest.json).
- **FR-DATA-03 COMPLETE** - exactly 2025 Q4:
  [experiment config](../config/experiment.yaml).
- **FR-DATA-04 COMPLETE within frozen scope** - deterministic latest-before-
  eligibility implementation and tests:
  [mart SQL](../src/faersight/sql/analytical_mart.sql),
  [version/quarter tests](../tests/unit/test_preprocessing.py).
  Original cross-quarter history is explicitly unverified above.
- **FR-DATA-05 COMPLETE for ingredient policy** - exact canonical mappings:
  [primary map](../mappings/drug_mapping.csv),
  [SS overlay](../mappings/sensitivity_ss_aliases.csv),
  [regulatory validation](rosuvastatin_zinc_reference_review_20261106.md).
- **FR-DATA-06 COMPLETE** - unmapped names retained/audited without fuzzy guesses:
  [preprocess audit](../artifacts/manifests/2025Q4-statins/preprocess_audit.json),
  [unmapped review summary](../artifacts/manifests/2025Q4-statins/unmapped_review_summary.json).
- **FR-DATA-07 COMPLETE** - frozen PS and isolated PS+SS definitions:
  [primary config](../config/experiment.yaml), [sensitivity config](../config/sensitivity.yaml),
  [role comparison](../artifacts/manifests/2025Q4-statins-sensitivity/role_comparison.json).
- **FR-OLAP-01 COMPLETE** - raw/provenance/case/drug/reaction mart:
  [schema](../src/faersight/sql/analytical_mart.sql),
  [revalidation](../artifacts/manifests/2025Q4-statins/revalidation.json).
- **FR-OLAP-02 COMPLETE** - quarter/drug/role/reaction views and aggregate exports:
  [schema views](../src/faersight/sql/analytical_mart.sql),
  [integration evidence](milestone2.md#executed-integration-evidence).
- **FR-TXN-01 COMPLETE** - all eligible cases, including empty background baskets:
  [ARFF manifest](../artifacts/manifests/2025Q4-statins-mining/arff_manifest.json),
  [export tests](../tests/integration/test_full_mart.py).
- **FR-TXN-02 COMPLETE** - separate DRUG/REAC item namespaces:
  [ARFF exporter](../src/faersight/arff.py), [fixture test](../tests/integration/test_fixture.py).
- **FR-TXN-03 COMPLETE** - native parser and actual Explorer load:
  [preflight](../artifacts/manifests/weka-explorer-demo/preflight/preflight.json),
  [manual GUI record](weka_explorer_demo.md).
- **FR-WEKA-01 COMPLETE** - 1,077 actual WEKA projected searches:
  [WEKA manifest](../artifacts/manifests/2025Q4-statins-mining/weka_manifest.json),
  [raw logs](../artifacts/manifests/2025Q4-statins-mining/weka_raw_logs.zip).
- **FR-WEKA-02 COMPLETE** - presence semantics/absence rejection:
  [WEKA config tests](../tests/unit/test_config_weka.py),
  [actual integration tests](../tests/integration/test_mining.py).
- **FR-WEKA-03 COMPLETE** - version, options, runtime and input hashes:
  [experiment manifest](../artifacts/manifests/2025Q4-statins-mining/experiment_manifest.json).
- **FR-WEKA-04 COMPLETE** - prespecified supports with rule counts 383/61/20:
  [run records](../artifacts/manifests/2025Q4-statins-mining/weka_runs.csv),
  [threshold stability](../artifacts/manifests/2025Q4-statins-mining/support_stability.json).
- **FR-WEKA-05 COMPLETE** - primary scientific exports retain single statin ->
  single reaction, despite four general demo rules:
  [accepted scored rules](../artifacts/manifests/2025Q4-statins-mining/accepted_rules_scored.csv),
  [direction tests](../tests/unit/test_config_weka.py).
- **FR-PV-01 COMPLETE** - all 2,513 candidate pairs preserve integer cells:
  [full candidate counts](../artifacts/manifests/2025Q4-statins-mining/all_candidate_counts.csv).
- **FR-PV-02 COMPLETE** - independent hand-computed PRR fixture:
  [statistics tests](../tests/unit/test_statistics.py).
- **FR-PV-03 COMPLETE** - independent hand-computed ROR and zero-cell policies:
  [statistics implementation](../src/faersight/disproportionality.py),
  [statistics tests](../tests/unit/test_statistics.py).
- **FR-PV-04 COMPLETE** - common N and marginal/coverage checks:
  [quality gates](../artifacts/manifests/2025Q4-statins-mining/quality_gates.json),
  [evaluation tests](../tests/unit/test_evaluation.py).
- **FR-EVAL-01 COMPLETE** - full-pair counts plus matched accepted-rule scores:
  [all candidates](../artifacts/manifests/2025Q4-statins-mining/all_candidate_counts.csv),
  [scored exports](../artifacts/manifests/2025Q4-statins-mining/accepted_rules_scored.csv).
  The PRD's illustrative `comparison.csv` name is not the real-data contract;
  filtered-out pairs remain in the full candidate table.
- **FR-EVAL-02 COMPLETE** - shared finite-pool Spearman/top-K with tie policies:
  [ranking comparison](../artifacts/manifests/2025Q4-statins-mining/ranking_comparison.json).
- **FR-EVAL-03 COMPLETE computationally** - eight preregistered positive pairs,
  including misses/recovery/ranks:
  [benchmark](../benchmarks/known_signals.yaml),
  [recovery](../artifacts/manifests/2025Q4-statins-mining/benchmark_recovery.csv),
  [sensitivity ranks](../artifacts/manifests/2025Q4-statins-sensitivity/benchmark_ranks.csv).
  Student label review remains unsigned.
- **FR-EVAL-04 PARTIAL** - raw cells, thresholds and role-effect diagnostics exist:
  [role pair differences](../artifacts/manifests/2025Q4-statins-sensitivity/role_pair_differences.csv),
  [review rules](../artifacts/manifests/2025Q4-statins-sensitivity/manual_rule_review.csv).
  Student-written explanation/approval of actual agreement and disagreement
  examples is absent; numerical diagnostics alone do not complete interpretation.
- **FR-REP-01 COMPLETE** - code/config/source/runtime/output provenance:
  [primary manifest](../artifacts/manifests/2025Q4-statins-mining/experiment_manifest.json),
  [sensitivity manifest](../artifacts/manifests/2025Q4-statins-sensitivity/sensitivity_manifest.json).
- **FR-REP-02 COMPLETE technically** - programmatic tables and deterministic
  metric-study charts, without spreadsheet edits:
  [metric runner](../showcase_metrics/runner.py),
  [metric validation](../artifacts/manifests/weka-showcase-metrics/run/validation.json).

## Nonfunctional requirements: PRD NFR inventory

**8 COMPLETE / 4 PARTIAL / 0 MISSING (12 total).**

- **NFR-01 PARTIAL** - current isolated environment and synthetic reproduction
  pass; historical full-data key-artifact reproduction is bounded as described
  in the verification record. No current all-core/all-OS reproduction is claimed.
- **NFR-02 COMPLETE** - input/code/config/runtime/score provenance is retained in
  primary/sensitivity manifests and [evidence indexes](../artifacts/manifests/2025Q4-statins-mining/evidence_index.json).
- **NFR-03 COMPLETE** - [determinism tests](../tests/regression/test_determinism.py)
  and historical byte comparisons, with explicitly excluded timing differences.
- **NFR-04 PARTIAL** - automated tests and independent source reconciliation
  pass; student manual source fields remain unsigned in the local review packet.
- **NFR-05 COMPLETE technically** - score definitions in
  [PRD](../PRD.md#signal-statistics), raw cells/flags in scored exports and
  [screening implementation](../src/faersight/screening.py). Student comprehension
  remains a course gate, not an automated assertion.
- **NFR-06 COMPLETE** - one class/quarter in frozen configs; showcase paths remain
  separate from the primary/sensitivity experiments.
- **NFR-07 PARTIAL** - Python 3.11 clean install and Linux core CI work; pinned
  Windows showcase/Explorer runtime paths are host-specific and 19 tests skip on
  Ubuntu. See [runtime documentation](plotting_runtime.md). No universal GUI portability claim.
- **NFR-08 COMPLETE for core** - streaming source staging, DuckDB budgets and
  bounded projected Apriori are evidenced in [Milestone 2](milestone2.md) and
  [Milestone 3](milestone3.md). The full-ARFF Apriori 0.001 timeout remains a
  disclosed separate showcase feasibility failure, not a successful run.
- **NFR-09 PARTIAL** - public-source processing with no identity-enrichment feature
  in the inspected pipeline; this checkpoint does not establish the absolute
  claim that no secret ever existed anywhere in Git history. No comprehensive
  history-wide secret audit was performed. Case report publication was user-authorized.
- **NFR-10 COMPLETE for repository automation** - workflows emit technical
  evidence, not graded artifacts. [Course policy](course_compliance.md) preserves
  the student-only boundary. Authorship/AI-code disclosure still needs student
  attestation before submission.
- **NFR-11 COMPLETE for inspected outputs** - noncausal reporting-association
  boundaries in README/manifests; no validated-clinical-signal flag is enabled.
- **NFR-12 COMPLETE** - exclusions, identities, roles, normalization and source
  counts persist in [preprocessing evidence](../artifacts/manifests/2025Q4-statins/preprocess_audit.json).

## Test-plan acceptance inventory

The PRD lists 25 acceptance scenarios; these are not a claim of 25 distinct test
functions. **21 COMPLETE / 4 PARTIAL / 0 MISSING.**

- **UT-ID-01 COMPLETE** - numeric latest versions: `tests/unit/test_preprocessing.py`.
- **UT-ID-02 COMPLETE** - two-quarter synthetic selection: same file and
  `tests/integration/test_full_mart.py`.
- **UT-NORM-01 COMPLETE** - exact known aliases: `tests/unit/test_preprocessing.py`.
- **UT-NORM-02 COMPLETE** - unknown names preserved: same file.
- **UT-ROLE-01 COMPLETE** - PS/SS/C classifications: same file and
  `tests/integration/test_sensitivity.py`.
- **UT-REAC-01 COMPLETE** - distinct reaction membership: preprocessing tests.
- **UT-TXN-01 COMPLETE** - separate presence items: `tests/integration/test_fixture.py`.
- **UT-TXN-02 COMPLETE** - background/empty baskets: same file and full-mart tests.
- **UT-PV-01 COMPLETE** - hand-calculated cells/scores: `tests/unit/test_statistics.py`.
- **UT-PV-02 COMPLETE** - explicit zero/undefined scores: same file.
- **INT-JOIN-01 COMPLETE** - cross-case join rejection: full-mart integration tests.
- **INT-UNIVERSE-01 COMPLETE** - integer cells/marginals: full-mart/evaluation tests.
- **INT-ARFF-01 COMPLETE** - native parser: fixture/mining integration tests.
- **INT-WEKA-01 COMPLETE** - actual known toy pair: fixture integration tests.
- **INT-WEKA-02 COMPLETE** - no accepted absence rules: config/mining tests.
- **INT-WEKA-03 COMPLETE** - API counts/metrics plus displayed-rounding allowance:
  `tests/integration/test_mining.py` and `test_fixture.py`.
- **INT-COMP-01 COMPLETE** - matched count/identity gates: those files plus
  `tests/unit/test_evaluation.py`.
- **REG-PREP-01 COMPLETE** - stable order-independent hashes:
  `tests/regression/test_determinism.py`.
- **REG-STATS-01 COMPLETE** - golden CSV: same file.
- **REG-WEKA-01 COMPLETE** - known toy rule assertions and pinned actual-runtime
  fixture integration; local and isolated runs enabled WEKA.
- **E2E-SMOKE-01 COMPLETE** - isolated N=10 end-to-end workflow plus fixture tests.
- **E2E-SAMPLE-01 PARTIAL** - full real-data processing and a 15-case source audit
  exist, but no separately preserved *pre-full-run small-real-sample pipeline*
  execution record was located. Real-format synthetic tests are not that evidence.
- **MAN-SOURCE-01 PARTIAL** - automated 15-case report complete; student signoff absent.
- **MAN-RULE-01 PARTIAL** - GUI four-rule agreement and automatic direction checks
  pass; unsigned 17-pair interpretation/review packet remains.
- **MAN-REPRO-01 PARTIAL** - historical automated fresh-clone matches plus current
  isolated verification exist; no student manual reproduction approval recorded.

## Course-compliance rows from PRD

Numbered in the original matrix order: **14 COMPLETE / 7 PARTIAL / 2 MISSING**.
Local PDFs are reference/draft documents, not proof of Canvas submission.

- **C01 Real-world dataset COMPLETE** - FDA source manifest.
- **C02 Mining software COMPLETE** - actual WEKA manifests/logs and screenshots.
- **C03 Application-oriented study COMPLETE** - frozen experiment and working pair analysis.
- **C04 Biomedical relevance COMPLETE** - FAERS source and statin scope.
- **C05 DEMO COMPLETE** - source schemas/audits and retained identities.
- **C06 DRUG COMPLETE** - source roles/mapping records and case audit.
- **C07 REAC COMPLETE** - source/reaction records and case audit.
- **C08 One class COMPLETE** - `config/therapeutic_class.yaml`.
- **C09 One/two quarters COMPLETE** - one quarter in `config/experiment.yaml`.
- **C10 Warehousing/OLAP COMPLETE** - SQL mart/views and integration evidence.
- **C11 Preprocessing COMPLETE** - persisted preprocessing audit and tests.
- **C12 Five mining primitives COMPLETE** - technical evidence: task-relevant data in
  experiment config; association knowledge in `config/mining.yaml`; domain
  background in class/mapping/benchmark files; interestingness in support/lift/
  PRR/ROR exports; presentation in captured Explorer rules and generated charts.
- **C13 Association rules COMPLETE** - real WEKA rules/raw logs.
- **C14 Interestingness COMPLETE** - support/confidence/lift/PRR/ROR count exports.
- **C15 Literature review PARTIAL** - local `Literature_Review_Progress_Report.pdf`
  contains a four-paper draft; prompts/authorship/citation completeness and
  actual submitted version are not approved by this audit.
- **C16 Literature/progress milestone PARTIAL** - local progress document exists;
  no Canvas receipt or deadline-compliance proof.
- **C17 Final presentation/demo PARTIAL** - genuine demo evidence exists; final
  student slide file and required attribution are missing.
- **C18 Presentation date PARTIAL** - rendered guide gives November 17 for the
  in-person session; Session 2-only students do not require in-person attendance.
  Current Canvas instructions are not confirmed.
- **C19 Final report/slides MISSING** - no final five-page report or PowerPoint
  submission artifact inspected; no upload receipts.
- **C20 Final upload date MISSING** - no Canvas submission confirmation. Rendered
  guide says November 19, 2026, 11:59 p.m.; student must confirm Canvas.
- **C21 No GenAI-written graded prose PARTIAL** - repository boundary documented;
  final student authorship and permitted-code/disclosure attestation absent.
- **C22 Results evaluated PARTIAL** - computational evaluation exists; student
  interpretation/approval remains pending.
- **C23 Reproducibility PARTIAL** - current isolated tests/fixture and historical
  same-host full-data matches; limitations in verification record apply.

Course evidence: local `docs/01_Introduction_to_Data_Mining.pdf`, visually
inspected pages 2, 4 and 5, and `docs/Literature_Review_Progress_Report.pdf`.
The rendered guide overrides stale December text underneath November date
overlays. Canvas remains authoritative. Detailed submission checks are in
[reproduction/demo readiness](reproduction_and_demo_readiness.md#students-submission-checks).

## Definition-of-done crosswalk

Each original unchecked statement remains historical. Below, D01-D25 follow
"course done" order; R01-R08 follow "resume ready" order in the PRD.

- **D01-D19 COMPLETE** - class, quarter, three tables, provenance, deterministic
  versions, mappings, role policy, mart/OLAP, case transactions, namespaces,
  ARFF load, semantic smoke, real WEKA, metrics, saved options/logs, PRR/ROR,
  hand-calculated tests, common universe and threshold sensitivity: FR evidence above.
- **D20 PARTIAL** - explain an agreement and disagreement: FR-EVAL-04 pending student judgment.
- **D21 COMPLETE** - explicit reporting-association terminology: NFR-11.
- **D22 COMPLETE** - automated unit/integration/regression checks: verification record.
- **D23 PARTIAL** - clean reproduction: NFR-01 scope/limitations.
- **D24 PARTIAL** - every course row evidenced: missing submissions/receipts above.
- **D25 MISSING** - independent authorship of final graded prose not attested;
  final report/slides not created by this checkpoint.
- **R01 COMPLETE** - dataset scale: 385,288 reports / 7 drugs / 359 reactions,
  ARFF and integration manifests.
- **R02 COMPLETE** - architecture: PRD data model and README implementation diagram.
- **R03 COMPLETE** - test count known with environment/skip distinctions above.
- **R04 COMPLETE** - quantitative lift/PRR/ROR comparison JSON.
- **R05 COMPLETE computationally** - eight-pair frozen benchmark evaluated;
  reference-label signoff remains separate.
- **R06 COMPLETE technically** - README instructions and current bounded reproduction guide.
- **R07 PARTIAL** - artifact sources exist, but no finalized student-approved resume
  claims were audited; do not fill numbers from estimates.
- **R08 COMPLETE technically** - no additional feature needed for the bounded
  engineering result. Resume-ready overall still depends on the unmet course gate.

## Evidence packaging and remaining actions

All required technical artifact categories in PRD section "Required evidence
artifacts" have a concrete counterpart: source/preprocess manifests, primary map,
mart SQL/summary views, toy ARFF, smoke logs, ARFF manifest, Apriori config/raw
logs, full candidate cells/scored exports, benchmark, threshold stability, tests/CI,
experiment/reproduction manifests and deterministic metric-study charts. File
names differ from illustrative `signals.csv`/`comparison.csv`; FR links identify
the actual contracts. This does not imply that all final-report figures or prose
have been selected or authored by the student.

The existing [Explorer checklist](weka_explorer_verification_checklist.md) and
screenshots remain valid; their measurements have not been expanded. Original
scientific evidence and historical validation records remain byte-preserved.
This checkpoint adds/updates Markdown documentation only.

**Student actions required before a submission-ready claim:**

1. Independently complete case, exact-alias, eight-benchmark-label and selected-rule
   reviews; explain the role-sensitive/threshold/sparse-count conclusions in your
   own words. Only the student can supply those reviewer fields and judgment.
2. Confirm the final report template, Canvas deadline and Session 2 file/recording
   requirements; confirm AI-assisted code/disclosure permissions. Supply the final
   template if a later format-only review is wanted.
3. Author and check the five-page inclusive report and PowerPoint independently,
   including slide 1 title/team, slide 2 contribution allocation, correct names,
   citations and actual upload receipts. None were generated here.

**Explicit approval needed for any future scope-changing work:** broader alias
mapping, role/config changes, dataset/history expansion or replacement scientific
results. No such change is necessary or proposed for this checkpoint. Further
mining is outside this authorization. Do not set scientific validation true as a
side effect of the engineering review. This checkpoint stops after documentation
verification, commit and push.
