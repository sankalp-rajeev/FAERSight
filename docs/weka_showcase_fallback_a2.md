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


## Completed authorized A2 attempt

Implementation/preregistration `4741fbc`; execution lock `a41bb28`. The committed manifest and SHA-256 sidecar preceded either full invocation; manifest SHA-256 `752db0a8fa8197a7b764b4c4843ed320af9b013ed655298d804cce2162f38fd3`. No run setting, resource bound or earlier evidence was changed.

### Raw execution times and completion

- **apriori: passed**, JVM exit 0; total driver wall 361.626217 s; JVM wall 360.891450 s. Association-build 360.503531 s; 241 frequent itemsets; 194 complete rules. Existing cap/completeness gates passed.
- **fpgrowth: passed**, JVM exit 0; total driver wall 1.416367 s; JVM wall 0.750769 s. Association-build 0.339151 s; 241 frequent itemsets; 194 complete rules. Existing cap/completeness gates passed.

JVM wall includes launch/load/validation/build/export; build brackets `buildAssociations`; total driver also includes compilation and post-return validation, as in A1. Raw times are preserved without extrapolation or speed ratio. Peak-memory behavior was not measured comparably.

### Verified singleton eligibility

- **apriori, cutoff 1,156**: atorvastatin 1,157 (eligible); fluvastatin 6 (ineligible); lovastatin 0 (ineligible); pitavastatin 16 (ineligible); pravastatin 67 (ineligible); rosuvastatin 864 (ineligible); simvastatin 188 (ineligible).
- **fpgrowth, cutoff 1,156**: atorvastatin 1,157 (eligible); fluvastatin 6 (ineligible); lovastatin 0 (ineligible); pitavastatin 16 (ineligible); pravastatin 67 (ineligible); rosuvastatin 864 (ineligible); simvastatin 188 (ineligible).

### Direct comparable-rule analysis

Native cutoffs both equal 1,156. Apriori 194; FPGrowth 194; intersection **194**; Apriori-only **0**; FPGrowth-only **0**; Jaccard **1.0**. No common-count restriction is required; the redundant 1,156 audit uses the same pool.

Shared metrics reconcile at absolute/relative 1e-12: **True**. Maximum absolute differences: `{"confidence": 0.0, "conviction": 0.0, "leverage": 0.0, "lift": 0.0, "support": 0.0}`. Every exported count and all finite metrics were independently reconciled against the frozen ARFF. Direction, presence, lift floor and unrestricted itemset family were preserved. No metric ranking was performed.

### Statin-containing rules and complexity

- **apriori**: statin-containing **0**; reaction-only **194**. Maximum antecedent/consequent/total rule sizes **2/2/3**; maximum frequent-itemset size 3. Antecedent-size counts `{"1": 185, "2": 9}`; consequent-size counts `{"1": 185, "2": 9}`; multi-item antecedents 9; multi-item consequents 9.
  Statin breakdown: `{"other_statin_containing": 0, "reaction_only": 194, "single_reaction_to_single_statin": 0, "single_statin_to_multi_reaction_consequent": 0, "single_statin_to_single_reaction": 0, "statin_plus_one_reaction_to_single_reaction": 0, "two_reactions_to_single_statin": 0, "two_statins_to_single_reaction": 0}`.
  Reaction-only progression: 1->1 176; multi->1 9; 1->multi 9; total size >=4 0.
  Complete canonical exports: `statin_rules_apriori.csv` and `statin_rules_apriori.json`, preserving algorithm source and all native itemsets/counts/metrics. No statin representatives exist; empty exports are explicit, with no fabricated examples.
- **fpgrowth**: statin-containing **0**; reaction-only **194**. Maximum antecedent/consequent/total rule sizes **2/2/3**; maximum frequent-itemset size 3. Antecedent-size counts `{"1": 185, "2": 9}`; consequent-size counts `{"1": 185, "2": 9}`; multi-item antecedents 9; multi-item consequents 9.
  Statin breakdown: `{"other_statin_containing": 0, "reaction_only": 194, "single_reaction_to_single_statin": 0, "single_statin_to_multi_reaction_consequent": 0, "single_statin_to_single_reaction": 0, "statin_plus_one_reaction_to_single_reaction": 0, "two_reactions_to_single_statin": 0, "two_statins_to_single_reaction": 0}`.
  Reaction-only progression: 1->1 176; multi->1 9; 1->multi 9; total size >=4 0.
  Complete canonical exports: `statin_rules_fpgrowth.csv` and `statin_rules_fpgrowth.json`, preserving algorithm source and all native itemsets/counts/metrics. No statin representatives exist; empty exports are explicit, with no fabricated examples.

These are observed A2 counts. Atorvastatin singleton eligibility does not override monotonic rule support or imply a statin co-occurrence rule. No clinical/causal interpretation or validated safety claim is made.

## Validation and stop gate

**145 tests passed**, zero failures/errors/skips; 8 new A2 tests and all 137 pre-existing tests retained, actual WEKA enabled. Deterministic CSV/JSON exports and sample order were checked independently of dictionary order. Ruff lint/format pass (59 source files). All 270 protected earlier files match `b5daa01`; all 108 frozen scientific-core files match `69d27d7`; all 1,096 primary and 1,106 sensitivity generated artifacts retain their registered hashes. Earlier 0.001/A1 evidence, code/configuration, manifests and scientific validation flags are unchanged; scientific validation remains false.

Preregistered 0.002 eligible: **True**, pending new explicit authorization. No 0.002, metric-ranking, Explorer, scaling or new algorithm ran. Stop after commit/push.

Tracked evidence: `artifacts/manifests/weka-showcase-fallback-a2-0.003/run/`. The [outcome](../artifacts/manifests/weka-showcase-fallback-a2-0.003/run/outcome.json) retains commands/times/native metadata/comparison/counts/statin export provenance. The [evidence index](../artifacts/manifests/weka-showcase-fallback-a2-0.003/run/evidence_index.json) hashes every snapshot and every raw emitted file; the ZIP preserves full native logs, rules, resolved options, partial outputs if any and compiled classes.

- Raw archive SHA-256: `6347461eacea75b112bbd9e24c097d5542f72b891f1d9ad8a03860e3f12814bf`.
- Evidence index SHA-256: `eae861c335cf46bf1e0427c67e08acd045b5954a5f58aa177e5629d475c70acc`.
