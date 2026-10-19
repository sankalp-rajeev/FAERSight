# Milestone 3: real WEKA experiment execution contract

Engineering record frozen October 19, 2026. Not course-submission prose or
validated drug-safety interpretation.

## Pre-experiment decisions

The Milestone 2 source, mappings, PS role definition, reaction floor and support
grid remain frozen. `benchmarks/known_signals.yaml` selects eight positive pairs
from four pre-2025 FDA labels, before any real mining/ranking run. These sources
are referenced for known reported associations, not for present-day clinical advice.
Exact uppercase terms are used; absent or filtered terms are reported rather than
renamed after the results. A positive-only benchmark cannot measure specificity.

The analytical mart has 385,288 eligible cases, seven candidate drugs and 359
candidate reactions. The exporter will write a complete sparse nominal `{0,1}`
ARFF and a case index, retaining empty and non-exposed cases. The source database
and all input/config/benchmark hashes are pinned in the experiment manifest.

## Bounded WEKA search, without changing pair statistics

Use actual `weka.associations.Apriori` through its public Java API. For each
reaction, project the full ARFF onto all seven drug attributes plus that one
reaction. Every projection retains every report, including empty baskets.
Only rules with exactly one present drug antecedent and one present reaction
consequent enter the accepted rule table. Python only verifies counts/statistics
and compares rankings; it does not implement association-rule search.

For a fixed drug/reaction pair, projection changes neither its joint count,
marginals nor N, hence support, confidence and lift remain identical. Every
desired one-to-one rule above the same support/lift thresholds remains available
to WEKA. Reaction-to-reaction and larger-consequent rules are outside the frozen
question. A synthetic test must compare projected results with a full-attribute
WEKA Apriori run, including co-exposures and empty background cases.

The 10,000-rule cap exceeds the maximum number of possible presence-only rules
on eight items: `3^8 - 2*2^8 + 1 = 6050`. Actual output caps are still checked.
This avoids silently losing drug rules behind a global reaction-rule output cap.

For each prespecified support value (`0.00001`, `0.00005`, `0.0001`), set WEKA
lower support to that value, upper support to 1, and delta to 1. This forces one
cycle at the lower bound without pruning high-support rules. Retain its
reported integer support count rather than assume a rounding convention.
Lift threshold remains 1.2. Raw per-projection output, exact options, full API
metrics and version/resource logs are retained. Reuse the existing Java 21 JDK
and WEKA 3.8.6 jars with a 4 GB heap and a 30-minute run timeout.

## Quality gates and interpretation boundary

- Validate source mart hash, full case count and binary attribute semantics.
- Prove projected/full WEKA equivalence on a scientific fixture.
- Check all raw mined items for presence value 1 and validate rule direction.
- Verify WEKA N and integer joint/drug/reaction counts against the mart.
- Independently check support, confidence and lift at full floating precision.
- Detect missing eligible pairs, duplicates and output-cap truncation.
- Retain `a,b,c,d,N` for PRR/ROR and explicitly flag undefined/infinite scores.
- Compute rank correlation with ties and top-K overlap on explicitly shared pair
  sets. Separate pair eligibility and benchmark recovery from top-K appearance.
- Preserve failures and partial logs; never label a timed-out run complete.

Student manual source review, benchmark review, role sensitivity and final
scientific interpretation remain pending. Unmapped C/SS spellings remain unchanged.
All primary experiment outputs must retain `scientific_findings_validated: false`.

## Pre-run correction from the mandatory toy gate

The initial execution contract incorrectly set upper support equal to lower
support. The actual WEKA toy run returned zero rules despite a known qualifying
pair. Inspection of the pinned 3.8.6 bytecode and the
[upstream implementation](https://github.com/Waikato/weka-3.8/blob/master/weka/src/main/java/weka/associations/Apriori.java)
showed that the upper bound also prunes rules whose joint count exceeds it.
The corrected `-U 1 -M <grid value> -D 1` starts at the lower bound and performs
one cycle. Tests require exact toy metrics and projected/full search agreement.
This correction precedes the real experiment; the support grid, lift threshold,
benchmark and population are unchanged. Failed toy logs remain local test evidence.

WEKA 3.8.6 rounds the integer minimum as `int(max(support, 1/N)*N + 0.5)`.
The runner verifies this against raw WEKA output and records the count source.
If no large pair itemsets exist, WEKA omits the support line; the runner records
the pinned rounding rule with that explicit absence flag. Every search must
report exactly one cycle, including searches with zero accepted rules.

## Execution evidence: October 19, 2026

Implementation commit `818a6d88d8ef78f728d10c0af58b586ff10a9f8d` passed all
87 local tests with actual WEKA enabled and
[GitHub CI](https://github.com/sankalp-rajeev/FAERSight/actions/runs/39200542596).
The positive benchmark was committed earlier at `1256b62`, before real mining.
Both complete experiment invocations started from a clean worktree at the same
implementation commit, using the existing Android Studio Java/Javac 21.0.10,
WEKA 3.8.6 and Bounce 0.18. No additional JDK was installed.

The complete ARFF contains 385,288 reports and 366 attributes, including 117,325
empty transactions. Each run completed 359 reactions times three support values
(1,077 actual WEKA searches) with one cycle per search. The first JVM run took
about 73 seconds. Integer minimum counts were 4, 19 and 39; corresponding accepted
drug-to-reaction pair counts were 383, 61 and 20. These are computational output
counts, not validated safety findings. The accepted sets are nested as support
increases. All 2,513 candidate count rows remain available, including pairs that
WEKA does not emit. Full-population PRR/ROR denominators remain unchanged.

Every emitted rule's integer joint, drug and reaction counts and N match the
mart. Exact API confidence and lift match independent calculations within
`1e-12`; displayed rounded scores are not used for this check. Eligible pair
coverage, direction, presence values and rule caps all pass. PRR/ROR retain
undefined/infinite flags. Correlation and top-K comparisons use the same finite
pair set for both methods, with average rank ties and recorded boundary ties.
Reference recovery includes all eight frozen positives at every threshold;
missing/filtered references are retained with explicit reasons.

An independent second Java invocation reproduced eleven key artifacts and all
1,077 raw logs byte for byte. All 1,077 projection records also match after
excluding elapsed seconds. This is a same-environment rerun; a fresh-clone
reproduction is still pending. The second manifest and comparison hashes are
included in the evidence snapshot.

Tracked evidence is in
[`artifacts/manifests/2025Q4-statins-mining/`](../artifacts/manifests/2025Q4-statins-mining/).
`evidence_index.json` hashes the aggregate counts, scored accepted rules,
positive-reference recovery, ranking comparisons, support stability, QA records,
runtime/version logs, both experiment manifests and a ZIP containing all original
raw WEKA logs. ARFF rows, case indexes, source records and the mart stay local.
The aggregate evidence can be exported reproducibly after a successful run:

```powershell
.venv/Scripts/python scripts/export_mining_evidence.py artifacts/generated/2025Q4-statins-mining artifacts/manifests/new-mining-snapshot
```

No environment or data-access blocker remains. Outstanding scientific work is
student manual review of source samples and benchmark choices, reviewed treatment
of the unresolved C/SS aliases before PS+SS sensitivity, and student-authored
interpretation. All delivered manifests retain `scientific_findings_validated: false`.
