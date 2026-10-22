# Post-timeout FPGrowth checkpoint

## Pre-run lock

Apriori's 0.001 timeout evidence is preserved at `6afd22d`. Pre-result amendment
`23a3a34` authorizes one FPGrowth 0.001 attempt. Corrected Fallback A ladder
0.004 -> 0.003 -> 0.002 becomes eligible after either outcome, with separate
authorization. Fallback B remains conditional on both original algorithms
failing and requires separate authorization. Neither fallback runs here.

Implementation commit `d425714` verifies the pinned jar/runtime on the 20-row
fixture. All 127 tests pass with actual WEKA (14 new, all 113 existing retained).
The [semantic record](../showcase_fpgrowth/SEMANTICS.md) documents exact options
and defaults. The separate
[execution manifest](../artifacts/manifests/weka-showcase-fpgrowth/locked/execution_manifest.json)
contains source/runtime/input hashes, raw fixture archive, count mismatch,
schema, completeness/policy gate, resource limits and test evidence. Its assertion
that full-data FPGrowth has not begun records the historical pre-run boundary.

Select **-S fixed-support all-rules mode**. N=100000 is ignored by WEKA for
generation/export. Require normal build return, complete export and internal/API
count equality; stop at internal count >=100000. Effective resource bounds:
4 GiB, 1,800 seconds, one JVM and ActiveProcessorCount=2 (JVM hint, no associator
parallelism). No result-dependent configuration tuning is permitted.

FPGrowth resolves **386** reports at 0.001, versus Apriori's **385**. This is a
pre-run comparability limitation; neither support is adjusted. The primary PS
ARFF remains 385,288 reports, 366 attributes, SHA-256
`de0f94f545ebae18033195524984fc842d3359154b864cb52bef2372a877dcf1`.

Locked CLI (exactly one invocation under the user's current authorization):

```powershell
.venv/Scripts/python -m showcase_fpgrowth.runner run --execution-manifest artifacts/manifests/weka-showcase-fpgrowth/locked/execution_manifest.json --authorize-full-data
```

Resolved associator options:

```text
-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.001 -D 1.0 -S
```

No direction filter or maximum itemset size. Sparse P=2 preserves correct =1
labels. Fixture: 50 exhaustive qualifying rules, 22 multi-item consequents, eight
empty baskets, five required forms, counts/four metrics within 1e-12 and repeated
byte-identical exports. U1/D1 without S takes two passes and clips the returned
API list at N; that mode was rejected before results.

If output is complete and below the policy limit, choose the first eight
multi-item rules by increasing total item count, then canonical antecedent and
consequent strings. Verify representative counts independently against the
unchanged primary mart. No score-based or attractiveness-based selection.
No clinical interpretation, rule overlap against Apriori or completed-runtime
ratio follows from Apriori's unfinished model. A timeout does not identify its
precise internal cause; later authorized diagnostics describe scaling only.
