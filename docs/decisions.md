# Engineering decisions and pending experiment choices

Private technical notes; not course-submission prose. Baseline: October 18, 2026.

## Implemented for the synthetic milestone

- Python package and CLI; uv dependency lock; DuckDB presence-item mart.
- WEKA 3.8.6, lift ranking (`-T 1`), `{0,1}` nominal order and `-Z`.
- Synthetic primary role policy: PS; PS+SS available in transaction-building tests.
- Latest case selection: numeric maximum caseversion, then numeric primaryid,
  then quarter, with conflicting same-report case/version metadata rejected.
- Apply latest-version selection before eligibility. Require at least one DRUG
  and one REAC record on the latest report; do not fall back to an older version.
- Preserve all eligible background cases, even when no target drug or candidate
  reaction survives. Deduplicate normalized drugs and reactions per case.
- Candidate reaction floor counts distinct target-exposed cases. Synthetic floor
  is 2; real-data floor remains pending.
- Only reviewed exact aliases map drugs. Audit all unknown eligible-role names;
  these include background products and are not automatically target-class gaps.
- No continuity correction: retain original counts, emit `nan`/`inf` in CSV and
  explicit score flags. JSON manifests contain no non-finite statistics.
- The initial parser fails on malformed rows instead of silently dropping them;
  real-quarter source README must establish the actual encoding and schema.

## Frozen real-data integration

Statins and 2025 Q4 are verified and frozen in `config/experiment.yaml` and
`config/therapeutic_class.yaml`. The official source has been downloaded,
checksum-pinned and integrated into the full DuckDB mart with its complete
eligible report population. Source documentation and the FDA deleted-case list
are retained. Real-data role policy, reaction floor and later mining grid are
frozen. See [the Milestone 2 decision and evidence](milestone2.md) for exact
policies, counts, hashes, reproduction and outstanding quality gates.

## Pending before real-data mining and interpretation

- Student manually audits the retained source sample; automated independent
  membership checks are complete.
- Review unmapped target-like C/SS names before a role sensitivity experiment.
  Unknown spellings remain unmapped; the frozen alias map is not changed silently.
- Freeze 5–10 externally supported positive benchmark pairs before final mining.
- Export and validate the real sparse ARFF over the same full case universe.
- Run actual WEKA Apriori with the prespecified grid and record any resource-driven
  change as a new decision before interpreting results.
- Complete benchmark recovery, ranking agreement, role/threshold sensitivity and
  student interpretation before treating reporting signals as validated findings.

## Course items owned by the student

- Confirm Canvas deadlines; PRD planning target for Milestone 2 is October 20,
  2026, with conflicting dates in supplied materials still unresolved.
- Verify permitted AI-assisted code use/disclosure with course guidance.
- Author all submitted literature/progress/final reports, slide prose and narration.

No PRD course-complete or real-data acceptance boxes are checked by this milestone.

## October 22 role-sensitivity decision

The historical pending items above are superseded by Milestone 3 mining evidence
and the separate [Milestone 4 record](milestone4.md). The new run stays within
2025 Q4 and preserves the frozen primary population, vocabulary, support grid,
lift floor, alias map and benchmark. One independently supported exact SS
ingredient-token overlay resolves both rosuvastatin-zinc candidate rows, without
changing PS or C mappings. The broader SS reaction vocabulary is listed but not
searched. Benchmark ranks use declared finite pools and average ties. Screening
uses uncorrected raw cells for log-Wald ROR intervals and an explicitly
Yates-corrected PRR convention; none constitutes clinical validation.

Student source/alias/label review and interpretation remain pending in the
unsigned packet. Stop before the optional WEKA showcase extension; no new
quarter, discovery vocabulary, reference pairs or ranking thresholds are added.
