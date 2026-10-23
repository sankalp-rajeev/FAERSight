# Fallback A2: preregistered full-data comparison at 0.003

Separate checkpoint after A1, frozen at `b5daa01`. Earlier Apriori 0.001,
FPGrowth 0.001 and A1 source/configuration/evidence remain unchanged. Use the
same full primary PS ARFF: 385,288 reports, 366 attributes, including 117,325
empty baskets; SHA-256
`de0f94f545ebae18033195524984fc842d3359154b864cb52bef2372a877dcf1`.

## Pre-execution registration

Authorize **0.003 only**. Execute Apriori first, then FPGrowth only after complete
below-cap, finite-metric, canonical Apriori output passes its existing gates.
Any timeout/OOM/error/incomplete output/cap ambiguity or >=31-itemset caveat
stops before FPGrowth; preserve every partial artifact. Do not retry, change
settings, descend to 0.002, rank metrics, run Explorer/scaling or add algorithms.

Resolve counts independently from the pinned WEKA 3.8.6 semantics:

- Apriori: `int(max(.003,1/N)*N+.5)` = **1,156**.
- FPGrowth: `ceil(.003*N)` = **1,156**.

Native integer thresholds are identical here; direct canonical comparison at
1,156 requires no additional filter. Retain a redundant common-count audit at
1,156 to keep the A1 comparison machinery consistent. Preserve whole directional
itemsets, every unrestricted presence rule, and finite support/confidence/lift/
leverage/WEKA-conviction. Reconcile shared counts/metrics with relative and
absolute tolerance 1e-12; independently check every exported count against the
frozen ARFF. No algorithmic-disagreement claim precedes definition checks.

Retain lift >=1.2, 4 GiB heap, 1,800-second timeout per JVM, one shared JVM lock,
ActiveProcessorCount=2 (JVM hint, not associator parallelism or CPU quota), and
unchanged algorithm-specific fixed-support/cap semantics. Apriori top-N clips
after generation; N=100000 equality is ambiguous. FPGrowth -S ignores N and
returns all internal rules; require internal/API equality and stop at internal
count >=100000. No user itemset-size or direction filter. Apriori's >=31 caveat
stops rather than silently limiting the comparison. Both native sources remain
the previously committed Java bridges; no core or earlier runner is edited.

The A2 driver preserves A1's exact time boundaries: JVM wall includes launch,
load/validation/build/export; build brackets `buildAssociations`; total driver
also includes compilation and post-return validation. Record raw times first,
without extrapolation or a speed ratio in this checkpoint, so support-level
timing can be studied later under explicit authorization.

Registered CLI (separate committed A2 execution manifest required first):

```text
.venv/Scripts/python -m showcase_fallback_a2.runner run --authorize-full-data
```

Apriori options:

```text
-N 100000 -T 1 -C 1.2 -D 1.0 -U 1.0 -M 0.003 -S -1.0 -Z -c -1
```

FPGrowth options, only after Apriori completes:

```text
-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.003 -D 1.0 -S
```

## Singleton eligibility and statin-rule question

Recompute all seven singleton counts from the frozen input before locking.
Under **each** algorithm's 1,156 cutoff, expected eligibility is:

- Atorvastatin 1,157: eligible.
- Rosuvastatin 864: ineligible.
- Simvastatin 188: ineligible.
- Pravastatin 67: ineligible.
- Pitavastatin 16: ineligible.
- Fluvastatin 6: ineligible.
- Lovastatin 0: ineligible.

A2 is the first fallback level admitting a statin **singleton**. This does not
establish new statin-rule eligibility: with the population, vocabulary, metric
floor and rule family fixed, increasing support cannot introduce statin rules
absent from the completed unrestricted FPGrowth 0.001 pool. Preserve this
monotonic-support distinction rather than reinterpret the earlier result.
Nevertheless, count the actual A2 outputs mechanically and report presence or
absence; never insert predicted rules or suppress unexpected observed rules.

Use a disjoint statin-rule classification: single statin -> single reaction;
single statin -> multi-reaction consequent; statin + one reaction -> reaction;
two statins -> reaction; single reaction -> statin; two reactions -> statin;
other statin-containing rules; reaction-only. Retain all statin-containing
rules, including unlisted structures, in algorithm-specific canonical CSV and
JSON exports, each with algorithm source and the complete native schema/counts/
metrics. Emit explicit empty files/header-only CSV if none. No attr expansion.

Always export the entire machine-readable statin set. A deterministic sample
uses the first **eight** by increasing total item count, then canonical lhs/rhs,
independent of metrics or clinical attractiveness. No examples are borrowed
from the fixture. Preserve reaction-only A1 categories and add antecedent/
consequent-size histograms, multi-item side counts and maximum side/total sizes.
All interpretation stays factual and non-causal: no interactions, causal
effects, clinical risks or validated safety claims.

Stop after validation and commit/push. A successful, reconciled A2 can make
0.002 eligible for separate explicit authorization; no later execution follows.
