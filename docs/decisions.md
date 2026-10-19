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

## Pending before real-data acquisition/preprocessing

- Choose one therapeutic class and one official FDA quarter; add a second only
  after the first succeeds.
- Record the official source page, archive URL, README, retrieval timestamp and
  SHA-256. No real archive has been downloaded.
- Create and review the real-class ingredient/alias mapping.
- Freeze role definition and reaction floor in the real experiment config.
- Freeze a small support/metric sensitivity grid before examining final rankings.
- Freeze 5–10 externally supported positive benchmark pairs before final mining.
- Add streaming/columnar preprocessing and full case_drugs/case_reactions tables
  before attempting quarterly-scale processing.

## Course items owned by the student

- Confirm Canvas deadlines; PRD planning target for Milestone 2 is October 20,
  2026, with conflicting dates in supplied materials still unresolved.
- Verify permitted AI-assisted code use/disclosure with course guidance.
- Author all submitted literature/progress/final reports, slide prose and narration.

No PRD course-complete or real-data acceptance boxes are checked by this milestone.
