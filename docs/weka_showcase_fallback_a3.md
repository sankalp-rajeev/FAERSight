# Final Fallback A checkpoint: A3 at 0.002

Separate preregistration after frozen A2 `a1113d0`. Preserve all earlier primary,
sensitivity, Apriori/FPGrowth 0.001, A1 and A2 source/configuration/evidence.
No additional support level is part of Fallback A after this checkpoint.

## Pre-run lock

Use the unchanged primary PS sparse ARFF: **385,288 reports, 366 attributes**,
117,325 empty baskets; SHA-256
`de0f94f545ebae18033195524984fc842d3359154b864cb52bef2372a877dcf1`.
Keep lift >=1.2, presence-only unrestricted rules, the verified WEKA 3.8.6
fixed-support semantics, 4 GiB heap, 1,800-second JVM wall timeout per invocation,
one shared JVM lock and ActiveProcessorCount=2 (JVM hint, not parallel mining
or CPU quota). No result-driven tuning, classifier, features or FDA quarter.

Independently resolved integer thresholds before execution:

- Apriori `int(max(.002,1/N)*N+.5)` = **771**.
- FPGrowth `ceil(.002*N)` = **771**.

Both native thresholds match. Compare complete directional itemsets directly;
retain the same common-count audit at 771 without another mining run. Require
finite support/confidence/lift/leverage/WEKA-conviction and counts reconciled
independently against the frozen ARFF. Shared metrics use absolute/relative
1e-12 tolerance. Retain complete native outputs and all available metrics/ranks;
do not rank metrics or call threshold differences algorithmic disagreement.

Recompute all seven singleton counts before locking. Under each 771 cutoff:
atorvastatin 1,157 and rosuvastatin 864 are eligible; simvastatin 188,
pravastatin 67, pitavastatin 16, fluvastatin 6 and lovastatin 0 are ineligible.
Singleton eligibility does not imply any qualifying statin rule. The earlier
complete 0.001 FPGrowth pool contained none; higher support with other definitions
fixed cannot introduce such rules. Still inspect the actual A3 results mechanically.

Commit/hash a separate A3 execution manifest before either full-data invocation.
Run **Apriori first**. Timeout, OOM, process/semantic error, unresolved top-N
ambiguity, incomplete output or >=31 Apriori itemset caveat stops A3 before
FPGrowth. Preserve every partial artifact and terminate Fallback A at that first
failed A3 algorithm. No retry, tuned configuration or replacement level follows.
If Apriori completes, execute FPGrowth once with its preregistered settings.

Native cap/completeness policies are unchanged: Apriori clips top-N after
generation and equality at N=100000 is ambiguous; FPGrowth -S ignores N for
generation/export, so require internal/API count equality and stop at internal
count >=100000. Neither N bounds candidate generation or memory. No user
itemset-length/direction limit; stop for Apriori's implementation caveat rather
than silently restricting the pool. Reuse the unchanged native Java bridges.

```text
.venv/Scripts/python -m showcase_fallback_a3.runner run --authorize-full-data
```

Apriori options:

```text
-N 100000 -T 1 -C 1.2 -D 1.0 -U 1.0 -M 0.002 -S -1.0 -Z -c -1
```

FPGrowth options, only after complete Apriori success:

```text
-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.002 -D 1.0 -S
```

## Registered analysis and terminal gate

Export every statin-containing rule, with algorithm, full antecedent/consequent,
joint/side counts, support, confidence, lift, leverage, conviction and retained
native schema/provenance. CSV/JSON exports are canonical; empty output remains
explicit. Classify single statin->reaction, statin->multiple reactions,
statin+reaction->reaction, reaction->statin, multiple reactions->statin (two or
more), two statins->reaction, other statin-containing structures and reaction-
only rules. Retain complexity histograms/maxima and the A1/A2 reaction categories.
The optional first-eight canonical statin sample stays metric-independent;
the complete set is always exported. No clinical/causal interpretation.

Produce a mechanical **CSV and JSON progression** for registered supports
0.004, 0.003, 0.002, with one row per completed algorithm/level: exact integer
cutoff, frequent-itemset/rule counts, build/JVM wall seconds, maximum total rule
size, all seven singleton eligibilities, statin-containing/reaction-only counts,
and native/common-count Jaccard. Hash/reference frozen source outcome and lock
files. Keep failed/unattempted statuses separate; do not substitute zero results.
Capture A3's pre-progression outcome separately to avoid circular provenance hashes.

Preserve A1/A2 timing boundaries: build brackets `buildAssociations`; JVM wall
includes launch/load/validation/build/export; total driver additionally includes
compilation and post-return validation. Report raw measured times without speed
ratio or extrapolation. Progression records observed sequences and whether
they are nondecreasing, without assuming runtime monotonicity. In particular,
Apriori's measured A2 build time was below A1's; support alone does not establish
a monotonic runtime pattern from these single observations.

If supported by completed comparisons, final conclusions may describe equivalent
rule outputs at these measured supports (A1's 1,541/1,542 native mismatch and
1,542 common-count audit remain disclosed), different measured computational
costs under this fixed dataset/version/configuration/envelope, and Apriori's
original 0.001 timeout versus FPGrowth completion. Do not claim equivalence for
an unfinished model, a precise internal timeout cause, or universal performance.

Validate all tests, fixture/count/comparison/deterministic exports, lint/format
and protected-file/generated-core hashes. Commit/push and stop. Whether A3
completes or fails, **no further support levels** may be added. Metric-ranking,
Explorer, scaling diagnostics and additional algorithms need new authorization.


## Completed authorized A3 attempt

Implementation/preregistration `602c1ab`; execution lock `adb5f35`. The committed manifest and SHA-256 sidecar preceded either full invocation; manifest SHA-256 `589c32b4aaa0299ac24fe1a1ebae727f87ff2a81f4804d5b7b9377895f035132`. No run setting, resource bound or earlier evidence was changed.

### Raw execution times and completion

- **apriori: passed**, JVM exit 0; total driver wall 829.371142 s; JVM wall 828.657024 s. Association-build 828.229460 s; 447 frequent itemsets; 586 complete rules. Existing cap/completeness gates passed.
- **fpgrowth: passed**, JVM exit 0; total driver wall 1.494203 s; JVM wall 0.831523 s. Association-build 0.395028 s; 447 frequent itemsets; 586 complete rules. Existing cap/completeness gates passed.

JVM wall includes launch/load/validation/build/export; build brackets `buildAssociations`; total driver also includes compilation and post-return validation, as in A1. Raw times are preserved without extrapolation or speed ratio. Peak-memory behavior was not measured comparably.

### Verified singleton eligibility

- **apriori, cutoff 771**: atorvastatin 1,157 (eligible); fluvastatin 6 (ineligible); lovastatin 0 (ineligible); pitavastatin 16 (ineligible); pravastatin 67 (ineligible); rosuvastatin 864 (eligible); simvastatin 188 (ineligible).
- **fpgrowth, cutoff 771**: atorvastatin 1,157 (eligible); fluvastatin 6 (ineligible); lovastatin 0 (ineligible); pitavastatin 16 (ineligible); pravastatin 67 (ineligible); rosuvastatin 864 (eligible); simvastatin 188 (ineligible).

### Direct comparable-rule analysis

Native cutoffs both equal 771. Apriori 586; FPGrowth 586; intersection **586**; Apriori-only **0**; FPGrowth-only **0**; Jaccard **1.0**. No common-count restriction is required; the redundant 771 audit uses the same pool.

Shared metrics reconcile at absolute/relative 1e-12: **True**. Maximum absolute differences: `{"confidence": 0.0, "conviction": 0.0, "leverage": 0.0, "lift": 0.0, "support": 0.0}`. Every exported count and all finite metrics were independently reconciled against the frozen ARFF. Direction, presence, lift floor and unrestricted itemset family were preserved. No metric ranking was performed.

### Statin-containing rules and complexity

- **apriori**: statin-containing **0**; reaction-only **586**. Maximum antecedent/consequent/total rule sizes **2/2/3**; maximum frequent-itemset size 3. Antecedent-size counts `{"1": 529, "2": 57}`; consequent-size counts `{"1": 529, "2": 57}`; multi-item antecedents 57; multi-item consequents 57.
  Statin breakdown: `{"multiple_reactions_to_single_statin": 0, "other_statin_containing": 0, "reaction_only": 586, "single_reaction_to_single_statin": 0, "single_statin_to_multi_reaction_consequent": 0, "single_statin_to_single_reaction": 0, "statin_plus_one_reaction_to_single_reaction": 0, "two_statins_to_single_reaction": 0}`.
  Reaction-only progression: 1->1 472; multi->1 57; 1->multi 57; total size >=4 0.
  Complete canonical exports: `statin_rules_apriori.csv` and `statin_rules_apriori.json`, preserving algorithm source and all native itemsets/counts/metrics. No statin representatives exist; empty exports are explicit, with no fabricated examples.
- **fpgrowth**: statin-containing **0**; reaction-only **586**. Maximum antecedent/consequent/total rule sizes **2/2/3**; maximum frequent-itemset size 3. Antecedent-size counts `{"1": 529, "2": 57}`; consequent-size counts `{"1": 529, "2": 57}`; multi-item antecedents 57; multi-item consequents 57.
  Statin breakdown: `{"multiple_reactions_to_single_statin": 0, "other_statin_containing": 0, "reaction_only": 586, "single_reaction_to_single_statin": 0, "single_statin_to_multi_reaction_consequent": 0, "single_statin_to_single_reaction": 0, "statin_plus_one_reaction_to_single_reaction": 0, "two_statins_to_single_reaction": 0}`.
  Reaction-only progression: 1->1 472; multi->1 57; 1->multi 57; total size >=4 0.
  Complete canonical exports: `statin_rules_fpgrowth.csv` and `statin_rules_fpgrowth.json`, preserving algorithm source and all native itemsets/counts/metrics. No statin representatives exist; empty exports are explicit, with no fabricated examples.

These are observed A3 counts. Atorvastatin/rosuvastatin singleton eligibility does not override monotonic rule support or imply a statin co-occurrence rule. No clinical/causal interpretation or validated safety claim is made.

## Validation and stop gate

**153 tests passed**, zero failures/errors/skips; 8 new A3 tests and all 145 pre-existing tests retained, actual WEKA enabled. Deterministic CSV/JSON exports and sample order were checked independently of dictionary order. Ruff lint/format pass (64 source files). All 292 protected earlier files match `a1113d0`; all 108 frozen scientific-core files match `69d27d7`; all 1,096 primary and 1,106 sensitivity generated artifacts retain their registered hashes. Earlier 0.001/A1/A2 evidence, code/configuration, manifests and scientific validation flags are unchanged; scientific validation remains false.

Fallback A terminates here. No further support levels, metric-ranking, Explorer, scaling diagnostics or additional algorithms are authorized or were executed. Stop after commit/push.

Tracked evidence: `artifacts/manifests/weka-showcase-fallback-a3-0.002/run/`. The [outcome](../artifacts/manifests/weka-showcase-fallback-a3-0.002/run/outcome.json) retains commands/times/native metadata/comparison/counts/statin export provenance. The [evidence index](../artifacts/manifests/weka-showcase-fallback-a3-0.002/run/evidence_index.json) hashes every snapshot and every raw emitted file; the ZIP preserves full native logs, rules, resolved options, partial outputs if any and compiled classes.

- Raw archive SHA-256: `98dae74683399ead3207b5457418f9936e5fa4c54ebc4fca56d1289df5ee22f7`.
- Evidence index SHA-256: `dd274100a74011200688191491005c49e968c50d591dd2909eb0bf85268f63bc`.

## Measured Fallback A progression

All values below are single observed invocations. Build/JVM wall times are separate timing boundaries; missing outputs remain unavailable. Full seven-statin eligibility and source hashes are in support_progression.csv/json.

- 0.004 apriori: minimum 1541; 154 frequent itemsets; 70 rules; build/JVM 393.965737/394.350229 s; max total size 3; eligible none; statin/reaction-only 0/70; native/common Jaccard 1.0/1.0.
- 0.004 fpgrowth: minimum 1542; 154 frequent itemsets; 70 rules; build/JVM 0.325450/0.735651 s; max total size 3; eligible none; statin/reaction-only 0/70; native/common Jaccard 1.0/1.0.
- 0.003 apriori: minimum 1156; 241 frequent itemsets; 194 rules; build/JVM 360.503531/360.891450 s; max total size 3; eligible atorvastatin; statin/reaction-only 0/194; native/common Jaccard 1.0/1.0.
- 0.003 fpgrowth: minimum 1156; 241 frequent itemsets; 194 rules; build/JVM 0.339151/0.750769 s; max total size 3; eligible atorvastatin; statin/reaction-only 0/194; native/common Jaccard 1.0/1.0.
- 0.002 apriori: minimum 771; 447 frequent itemsets; 586 rules; build/JVM 828.229460/828.657024 s; max total size 3; eligible atorvastatin, rosuvastatin; statin/reaction-only 0/586; native/common Jaccard 1.0/1.0.
- 0.002 fpgrowth: minimum 771; 447 frequent itemsets; 586 rules; build/JVM 0.395028/0.831523 s; max total size 3; eligible atorvastatin, rosuvastatin; statin/reaction-only 0/586; native/common Jaccard 1.0/1.0.

A1 native cutoffs differ (Apriori 1541, FPGrowth 1542); its retained common-count audit at 1542 also agrees completely. A2 and A3 native cutoffs match. Apriori A2 build time is below A1: these measurements do not establish monotonic runtime as support decreases. No runtime ratio, extrapolation or peak-memory comparison is reported.

Under this frozen PS input, WEKA 3.8.6, registered options and 4 GiB/1800 s envelope, both algorithms completed all three higher-support comparisons with identical observed directional rule sets and reconciled metrics. Their measured computational costs differed substantially. The original unrestricted Apriori 0.001 task exceeded the 30-minute budget while FPGrowth completed; no Apriori 0.001 completed rule set exists for equivalence comparison. These matched runs provide bounded tool-study evidence, not a universal algorithm performance claim or diagnosis of the internal timeout cause.

Manual student judgment remains necessary for presentation selection and factual, non-causal interpretation. The frozen primary/sensitivity experiments and their scientific_findings_validated=false boundaries remain unchanged.
