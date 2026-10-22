# Milestone 4: 2025 Q4 scientific checks

Engineering evidence and student inspection aid, October 22, 2026. This file is
not a course submission or a clinical interpretation. The primary experiment,
its eight reference pairs, and all original evidence remain frozen.

## Comparison contract

The primary is statins / 2025 Q4 / PS. The separate sensitivity adds SS while
retaining the same 385,288 eligible reports, seven drugs, 359 primary reactions,
2,513 pair grid, support values 0.00001 / 0.00005 / 0.0001 and lift floor 1.2.
An immutable primary database is copied into a new derived mart. Full raw tables,
retained reports and reaction memberships are checked for equality; drug presence
remains distinct per case and contains every primary exposure. Actual WEKA
Apriori executes all 1,077 projections again, with full background/empty reports.

Adding SS makes 404 additional reaction terms meet the exposure floor. They are
listed in `deferred_reactions.csv` but are not searched. Thus this is a matched
role comparison conditional on the primary reaction vocabulary, not a complete
PS+SS discovery experiment. No other quarter is acquired or analyzed.

## SS mapping review

The relevant audit has one unmapped SS product name on two retained source rows:
`EZETIMIBE\ROSUVASTATIN ZINC`, with the same active-ingredient field. The
[HPRA product record](https://www.hpra.ie/find-a-medicine/for-human-use/authorised-medicines/details/28356)
identifies the ezetimibe/rosuvastatin zinc product, and the
[MHRA assessment](https://mhraproducts4853.blob.core.windows.net/docs/704ac196122f3954aaf0295a67fdd22f011126d4)
identifies rosuvastatin zinc as its statin ingredient.

`mappings/sensitivity_ss_review.yaml` records the evidence decision and pending
student signoff. `mappings/sensitivity_ss_aliases.csv` is a separate exact-token
overlay, applied only to those SS rows. The complete combination product remains
in the source record. The primary map and primary PS exposures are unchanged.
The runner fails on any additional unreviewed PS/SS target-like candidate or
unexpected candidate count. All 272 unmapped C rows remain excluded from exposure.

Without the overlay, PS+SS exposes 3,702 reports; after it, 3,703. Both source
rows are resolved, with one additional distinct exposed report. Pre-overlay
PS+SS counts and a separate mapping-effect export isolate this contribution.

## Screening conventions

`screening.py` augments new milestone exports without altering primary metrics:

- ROR 95% log-Wald interval: `exp(log(ROR) +/- 1.96*sqrt(1/a+1/b+1/c+1/d))`.
  All cells must be positive. Zero-cell intervals are unavailable, with an
  explicit status; no 0.5 correction or other pseudocount is applied.
- PRR screening convention: `a >= 3`, `PRR >= 2`, and Yates-corrected chi-square
  `>= 4`, all together. Pearson chi-square is also exported. Undefined PRR or a
  degenerate margin cannot pass. An explicitly infinite PRR can pass the other
  requirements; its original zero cells and flags remain visible.
- With `N=a+b+c+d`, Pearson is `N*(ad-bc)^2/((a+b)(c+d)(a+c)(b+d))`;
  Yates substitutes `max(0,abs(ad-bc)-N/2)^2` in the numerator.

The report-count/PRR/chi-square thresholds come from
[Evans, Waller and Davis (2001)](https://onlinelibrary.wiley.com/doi/abs/10.1002/pds.677).
The correction choice is explicitly Yates in this milestone. The reciprocal-cell
log-ROR variance is documented in
[Oracle's ROR computation reference](https://docs.oracle.com/health-sciences/empirica-signal-811/ESIUG/ROR_Computations.htm);
this implementation uses 1.96 for 95% intervals, rather than that reference's
90% interval, and preserves the project's no-pseudocount policy.

These are unadjusted descriptive screening conventions. They do not establish
causality, clinical incidence, treatment risk, or a validated clinical signal.
They do not correct for multiple comparisons, confounding, co-reporting,
underreporting or case selection. Sparse intervals require particular caution.

## Executed role differences

All integration/role/marginal/source invariants and exact WEKA count/metric/
exhaustive pair-coverage checks passed. PS-exposed reports increase from 2,298
to 3,703 (+1,405; approximately 61.1%). Drug-presence counts are not summed to
count people: a case may contain several statins.

- Atorvastatin: 1,157 to 1,755 exposures.
- Rosuvastatin: 864 to 1,508.
- Simvastatin: 188 to 464.
- Pravastatin: 67 to 135.
- Pitavastatin: 16 to 42; fluvastatin: 6 to 40; lovastatin: 0 to 9.

At support 0.00001, accepted WEKA pairs change from 383 to 763: 371 shared,
392 gained and 12 lost (Jaccard 0.4787). At 0.00005, 61 become 301: 60 shared,
241 gained and one lost. At 0.0001, 20 become 112: all 20 shared, 92 gained.
Adding exposure can dilute drug-conditional reaction frequency, so not every
primary rule survives even though joint counts cannot decrease.

Across the matched finite pair sets, PS-versus-PS+SS Spearman correlations are
0.7931 for lift, 0.7937 for PRR and 0.7926 for ROR. The respective top-10
overlaps are 4, 6 and 5. These role comparisons use the same pairs on both sides
for each score (2,154 for lift; 2,153 for PRR/ROR), with average-rank ties and a
lexical tie break for the fixed-size top-K. Full records are in
`role_comparison.json`; within-role lift-versus-PRR/ROR comparisons are separate.

The PRR convention flags 320 primary pairs and 665 PS+SS pairs: 367 gained,
22 lost. ROR intervals are unavailable for 1,547 / 1,299 pairs respectively,
owing to zero cells. Counts and statuses remain available for every pair.

## Benchmark rank reporting

All eight frozen positives appear in every role/threshold report. Recovery is
unchanged at 5/8, 4/8 and 2/8 across increasing support. There are no dropped
misses and no retrospective synonym expansion.

`benchmark_ranks.csv` contains lift, PRR and ROR scores, descending average rank,
percentile, pool size, excluded nonfinite count and an explicit status. It has
both an all-candidate pool and a WEKA-accepted pool at each support. Missing
accepted pairs receive no invented accepted-set rank. All three metrics use
the same finite-score intersection within each role/pool. The all-candidate
intersection is 2,153 for PS and 2,512 for PS+SS; these denominators differ
because lovastatin has no PS exposure and another pair has nonfinite ratios.
Do not interpret raw ranks as if these two pool sizes were identical.

Percentile is `100*(pool_size-rank)/(pool_size-1)` (singleton: 100), with higher
values better. Tied zero scores receive their average rank and consequently a
nonzero percentile; this does not imply observed drug/reaction co-occurrence.

All-candidate lift ranks (PS to PS+SS), in the denominators above:

- Atorvastatin: myopathy 59 to 96; rhabdomyolysis 52 to 88.
- Rosuvastatin: myopathy 76 to 128; rhabdomyolysis 30 to 71.
- Simvastatin: myopathy 102 to 222; rhabdomyolysis 49 to 106.
- Pravastatin: myopathy 1,560 to 100; rhabdomyolysis 153 to 315.

Seven primary positives are at approximately the 92.7th percentile or higher
across all three metrics; pravastatin/myopathy is at the 27.6th tied percentile
with no primary co-occurrence. Under PS+SS all eight are at the 86.9th percentile
or higher across metrics. Pravastatin/myopathy rises to the 95.4th--96.1st
percentiles but still misses the lowest WEKA support count. A high rank and
reference recovery are distinct measurements. This positive-only set cannot
estimate specificity or establish comparative clinical drug safety.

## Manual review package

The local packet is `artifacts/generated/2025Q4-statins-sensitivity/manual_review/`:

- `cases.json` and `case_checklist.csv`: 15 deterministic cases, covering both
  corrected SS products, PS cases, newly exposed SS cases, co-suspected statins,
  empty mining baskets and C-only background reports. Original DEMO/DRUG/REAC
  text is independently rescanned for latest identity, complete drug rows and
  reaction memberships. All automated checks pass.
- `rules.csv`: 17 distinct pairs with both role definitions, all eight positives,
  shared high-lift examples, sparse extremes, lost/gained rules and screening
  flips. Complete raw counts, intervals and flags accompany scores.
- `benchmark_checklist.csv`: all eight positive pairs with their frozen FDA
  label links; verification fields remain blank.
- `README.md`: inspection sequence and explicit pending student verdicts.

This is a selected explanatory sample, not a random representativeness claim.
Detailed report records and case identifiers remain local and ignored by Git.
Only aggregate rules, review instructions, unsigned benchmark checklist and
package hashes enter tracked evidence. Student review must verify role/mapping
decisions, label terminology, sparse extremes, dilution, co-reporting and the
student's interpretation; no automated step signs off that judgment.

## Reproduction and freeze status

The reproduction harness is `scripts/reproduce_milestone4.py`. It creates a
Git bundle and a separate clone, installs the locked dependencies in a new
environment, verifies and extracts the cached pinned FDA ZIP, rebuilds the
mart, and reruns actual WEKA. It compares deterministic artifacts and every
raw projection log. Cached jars, source ZIP and dependency cache are explicitly
reused; processed tables, ARFF, results and environments are not copied.

The committed primary base is `262dfc0`. The new milestone is transferred to
that clone as a separately hashed, explicitly uncommitted source overlay.
This distinction is retained in the reproduction record. This is a same-host
reproduction using the existing Java runtime, not an independent-platform test.

Execution and final freeze disposition are recorded in the completion addendum
below and in `artifacts/manifests/2025Q4-statins-sensitivity/`. Keep the optional
WEKA showcase extension on hold until the student inspection and final freeze
decision. All manifests continue to say `scientific_findings_validated: false`.

## Completion addendum

The local suite passed all 100 tests with actual WEKA enabled, zero skipped,
zero failures and zero errors. Ruff lint and format checks passed. The separate
fresh environment first passed the 87-test committed primary suite, then all
100 tests after applying the hashed milestone source overlay.

Fresh-clone reproduction passed both experiments. For the primary, ten
deterministic artifacts and all 1,077 raw logs are byte-identical to the frozen
reference. For PS+SS, seventeen deterministic artifacts, including the source
inspection packet, and all 1,077 raw logs are byte-identical to the first new
run. All projection metadata match after excluding the `seconds` field. Physical
DuckDB bytes and path/timing-dependent manifests are not claimed byte-identical;
the independently rebuilt report population and deterministic mining inputs/
counts/rules establish logical agreement.

Initial failures are retained rather than relabeled as successful runs. The
first setup attempt lacked pytest's `.tools` parent; the harness now creates it.
An initial nested ingestion returned exit zero without producing its final
manifest/database. A direct invocation of the clean clone's Python rebuilt
the entire quarter in a new output directory and passed all integration gates;
the successful reproduction explicitly records this recovery and its manifest
hash. The harness now requires completion artifacts as well as a zero exit code.
The cause of that premature initial exit has not been established. The original
partial database is retained, and no partial run is treated as complete.

Aggregate evidence is exported under
`artifacts/manifests/2025Q4-statins-sensitivity/`, with a hash index, exact raw-log
ZIP, new metrics/ranks, paired role differences, isolated mapping effects, test
summary, unsigned review aids and the reproduction record/logs. The local
report-level packet remains under `artifacts/generated/` and is excluded from Git.

The technical core is ready to freeze at 2025 Q4. Final scientific/course
signoff remains conditional on the student's source-case inspection, exact-alias
and benchmark-label approval, interpretation of sparse/co-reported associations,
and student-authored submission. No new quarter or optional showcase was added.

To reproduce in another unused local clone directory from the committed primary
base plus the explicitly hashed milestone overlay:

```powershell
.venv/Scripts/python scripts/reproduce_milestone4.py --clone .tools/new-reproduction-clone --records artifacts/generated/new-reproduction-record --jar .tools/weka/weka-stable-3.8.6.jar
```

Use a new record/output directory for independent reruns. `--resume` is only for
a recorded failed harness attempt, retaining its failure history; a validated
clean-clone ingestion recovery can be supplied through `--integrated-mart`.
