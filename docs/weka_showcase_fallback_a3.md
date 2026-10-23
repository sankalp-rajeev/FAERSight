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
