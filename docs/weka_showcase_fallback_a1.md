# Fallback A1: preregistered full-data comparison at 0.004

Purpose: find a higher support where both unrestricted WEKA associators complete
on the same frozen primary PS input, permitting a direct output comparison.
This is a tool feasibility/comparison checkpoint; no clinical interpretation.
Apriori's 0.001 timeout and FPGrowth's 0.001 success remain immutable history.

## Pre-run registration

Only 0.004 is authorized. Run Apriori first; any timeout, resource/process error,
cap ambiguity, incomplete export or long-itemset caveat stops A1 **before**
FPGrowth. If Apriori passes, run FPGrowth once. No retry, descent, metric-ranking
experiment, Explorer or scaling diagnostics. A successful A1 only makes 0.003
eligible for a later explicit authorization; it does not execute that level.

The same 385,288-report / 366-attribute primary PS ARFF is required, SHA-256
`de0f94f545ebae18033195524984fc842d3359154b864cb52bef2372a877dcf1`.
Keep all 117,325 empty baskets, lift >=1.2, general presence rules, 4 GiB heap,
1,800-second JVM timeout per algorithm and one shared JVM lock. JVM active
processors=2 is a hint, not parallel associator search or a CPU quota.

Exact verified integer counts **before either run**:

- Apriori: `int(max(.004,1/N)*N+.5)` = **1,541**.
- FPGrowth: `ceil(.004*N)` = **1,542**.

This one-report difference prevents treating raw native output sets as identical
support tasks. Preserve and report both raw sets. Additionally preregister a
comparison of both complete native exports filtered to joint count **>=1,542**,
the larger native cutoff. This is mechanical restriction of existing complete
outputs, not support adjustment or another mining run. Report any excluded
1,541-count rules explicitly. Canonical rule identity includes both complete
directional itemsets, not only the union. Require finite support/confidence/lift/
leverage/conviction and raw-count consistency. Compare all shared metrics at
relative and absolute tolerance 1e-12. No metric ranking is performed.

Both bridges emit all nonempty proper partitions without a user length limit.
Apriori's >=31 frequent-itemset integer-partition caveat stops completion rather
than silently restricting the pool; FPGrowth uses boolean-array enumeration.
Native cap policies remain unchanged: Apriori top-N clipping, equality with
100,000 ambiguous; FPGrowth -S ignores N, requires internal/API count equality
and stops at internal count >=100,000. Neither N bounds generation memory/work.
The CSV `rule_cap` field records requested N, not an enforced FPGrowth cap.

Commands/options are locked in the separate execution manifest before either
full-data invocation. The new driver compiles the **unchanged existing** Java
showcase bridges; it does not alter either prior runner/config or primary bridge.
Both timing boundaries record JVM launch through load/validation/build/export;
build is the native `buildAssociations` call. Record compile+process time
separately. No speed ratio is registered because native support workloads differ;
absolute times suffice. No peak-memory comparison is claimed without measurement.

## Statin absence is expected, not a discovery

With other settings fixed, increasing support cannot create a qualifying
statin-containing rule absent from the completed unrestricted FPGrowth 0.001
pool. This fallback is not an attempt to recover such rules. Independently, at
0.004 the maximum statin singleton count, atorvastatin **1,157**, is below both
1,541 and 1,542. Other primary counts: rosuvastatin 864, simvastatin 188,
pravastatin 67, pitavastatin 16, fluvastatin 6, lovastatin 0. Recheck these from
the frozen ARFF before locking. No statin singleton can survive either cutoff.

If both complete, mechanically summarize reaction->reaction, multi-reaction
antecedents->reaction, reaction->multi-reaction consequents, larger reaction-only
rules, side-size maxima, frequent-itemset counts and raw/common-support overlap.
Independently reconcile every exported rule's counts against the frozen ARFF.
Do not label differences algorithmic disagreement until definitions match.
No inference about the internal cause of Apriori's 0.001 timeout is authorized.

Registered A1 CLI (Apriori-first gate controls both invocations):

```text
.venv/Scripts/python -m showcase_fallback_a1.runner run --authorize-full-data
```

Apriori options:

```text
-N 100000 -T 1 -C 1.2 -D 1.0 -U 1.0 -M 0.004 -S -1.0 -Z -c -1
```

FPGrowth options, executed only after complete Apriori success:

```text
-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.004 -D 1.0 -S
```
