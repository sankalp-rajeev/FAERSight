# WEKA metric-ranking checkpoint preregistration

The unrestricted WEKA showcase is an algorithm and metric study on reaction co-reporting. The projected experiment is the FAERSight drug-safety analysis.

## Frozen analysis population and precision

Use exactly the 586 canonical A3 rules at support 0.002 (771 reports), originally qualified by lift >=1.2. Read the hashed tracked A3 raw archive and verify both miners' complete pools, counts and API metrics. Retain one canonical copy with provenance to both miners. No rule removal/addition, new threshold search, support level, associator or statin-recovery mining is authorized.

Rankings use full-precision values exported directly from WEKA's metric API (`getNamedMetricValue`, Java double round-trip serialization). Rounded WEKA printed model text can never enter the ranking. Independently reconcile counts and all five values at absolute/relative tolerance 1e-12; stop on discrepancy. Exact parsed double equality defines ties; tolerance is for reconciliation only, never tie rounding.

## Registered calculations

Rank confidence, lift, leverage and conviction descending. Statistical ranks use average ranks for ties. Deterministic exports and Top-K use canonical lexical antecedent/consequent tuples only after equal metric values. Export both rank types.

Compare all six metric pairs at K=10,25,50: intersection, union, Jaccard, intersection/K; four-way intersections; boundary value and total/inside/outside boundary ties for every metric/K. Compute Spearman as Pearson correlation of average ranks over all 586 rules and separately over the 472 single-reaction->single-reaction rules, re-ranking within that subset.

The 586 association rules are not independent observations. Reciprocal rules and rules derived from overlapping itemsets share counts and structure, so the rank correlations describe this rule pool rather than an independent statistical sample. The single-to-single analysis is a descriptive robustness check, not an inferential independence correction.

The pool already requires lift >=1.2: lift is truncated at the bottom. Any Spearman involving lift describes this narrower band; this range restriction can compress lift-based agreement. The six correlations cannot establish general metric behavior or what each metric would independently discover.

Rank-gap examples use average ranks, gap >=100, at most three per category, descending positive gap then canonical lexical key: lift_rank-confidence_rank; leverage_rank-lift_rank; lift_rank-leverage_rank; confidence_rank-conviction_rank. Preserve empty/short categories without changing thresholds. Export complete itemsets, joint/side counts, support, all four metrics and all four average ranks.

Distributions: minimum, median, mean when finite, maximum, empirical inverse-CDF percentiles 5/25/50/75/95, distinct values, tied-rule count/fraction and largest tie group. Positive-infinite conviction remains positive infinity (JSON string `Infinity`), above finite values with average tied ranks. No capping/dropping/zero substitution; conventional finite mean is unavailable if infinite. Verify WEKA's confidence=1 convention directly using existing pinned bytecode and a count-only API probe; no association mining is needed.

## Complete statin-itemset support bound

Using the unchanged primary PS ARFF, count all 7x359 statin-reaction pairs and all 21 distinct statin-statin pairs, including zero counts. Every statin-containing itemset of size >=2 contains one of these pairs, so its support cannot exceed that pair's support. Since pairs themselves belong to the family, the largest pair count equals the largest joint count over **all statin-containing itemsets of size 2 or more**, including multi-statin and mixed itemsets. Report both pair-family maxima and all lexical maximum witnesses, plus the exact all-family maximum.

Compare against Apriori 385 / FPGrowth 386 at 0.001; both 771 at 0.002; both 1156 at 0.003; Apriori 1541 / FPGrowth 1542 at 0.004. If confirmed, state: "No statin-containing itemset of size 2 or more reaches the minimum." Singleton eligibility does not establish joint support. This is not evidence of no adverse-event associations. The projected one-reaction-at-a-time design permits the intended statin->reaction comparisons at lower support while preserving the full denominator. Removing unrelated attributes at fixed criteria cannot change a given rule's counts/metrics; do not schedule another statin-recovery experiment.

## Bounded charts, validation and stop

Generate exactly three charts: one full-pool Spearman matrix and two average-rank scatterplots for the highest/lowest full-pool correlations, with canonical metric-name pair tie breaks. Use deterministic Matplotlib SVG/PNG exports, fixed layout/fonts/metadata; no decorative plots. Existing local plotting runtime is pinned separately from the primary Python environment; do not change frozen dependencies.

Test metric/count reconciliation, confidence=1 conviction, positive-infinity parsing/ranking, average ties, Top-K/boundaries, rank-gap selectors, Spearman, subset membership/re-ranking and deterministic chart/data bytes. Run the complete existing suite with actual WEKA fixtures enabled, lint/format, frozen-core and all prior-file hashes. Commit and push analysis code/settings and a hashed lock before full-pool calculations; commit/push results, evidence, charts and documentation afterward.

After completion: unrestricted Apriori study, Apriori/FPGrowth comparison, Fallback A and metric-ranking comparison complete. WEKA Explorer is next, pending explicit authorization; final showcase summary/demo packaging follows Explorer. Do not run Explorer, final packaging or further mining in this checkpoint. Scientific validation boundaries remain false.


## Completed offline checkpoint

Preregistration `b8e676d`; implementation `5b34861`; lock `2b5af74`.
Manifest SHA-256 `35ed664d003881c10d69ee0967cdd97f186380d36d309ec1dcc58a000b0a0494`.
The analysis used exactly 586 frozen A3 rules. Both miner API exports retain identical canonical itemsets, counts and full-precision metrics. Independent ARFF reconciliation verified 586 rules and 314 distinct itemset counts; the maximum difference in support or any of the four metrics is exactly zero. No new association search or support level ran.

### Metric definitions and conviction evidence

For population N, joint count J, antecedent count A and consequent count B:
confidence=J/A; lift=(J/A)/(B/N); leverage=J/N-(A/N)(B/N);
WEKA conviction=(A*(N-B)/N)/(A-J+1). The `+1` correction is part of pinned WEKA 3.8.6, not unsmoothed textbook conviction. Existing pinned bytecode and a count-only probe independently verify both the general-rule and Apriori APIs without running an associator.

The common pool has **zero confidence=1 rules, zero infinite conviction values and zero capped/sentinel values**. Synthetic count-only confidence=1 probes retain raw and parsed API values and independent recomputations: (N,A,B,J)=(20,5,7,5) gives conviction 3.25; (20,1,1,1) gives 0.95; (20,20,20,20) gives 0.0. These are finite formula outputs, not sentinel replacements, mined rules or clinical examples. Ranking retains their original finite value. Defensive tests preserve positive infinity above finite values with average ranks for ties; JSON uses the explicit string `Infinity`, without silent capping/dropping. No such infinity occurs in this pool.

### Pairwise Spearman correlations

Full-pool / separately re-ranked 472 single-to-single values:

- confidence vs conviction: **0.964812376415 / 0.961549347815**.
- confidence vs leverage: **0.472671695768 / 0.556607208758**.
- confidence vs lift: **0.463691698982 / 0.551234411994**.
- conviction vs leverage: **0.568621861498 / 0.655791528212**.
- conviction vs lift: **0.627255054327 / 0.716657062589**.
- leverage vs lift: **0.512411967620 / 0.616915262780**.

Both populations retain the same ordering of the six pairwise correlations. Confidence/conviction remains highest; confidence/lift remains lowest. This describes robustness after removing multi-item rules, not an inferential independence correction. Reciprocal/overlapping rules remain dependent. Lift is truncated by the original >=1.2 pool restriction; lift-based agreement can be compressed by that restricted range. These values are not general metric behavior or an exhaustive comparison of independently discovered pools. No p-values or independence claims are made.

### Top-K overlap and boundary ties

Pairwise records below give intersection/union, Jaccard and intersection/K. Both metric rankings use the same 586 rules; boundary ties are not broken for statistical ranks.

- K=10, confidence/conviction: 10/10; Jaccard 1; overlap/K 1.
- K=10, confidence/leverage: 0/20; Jaccard 0; overlap/K 0.
- K=10, confidence/lift: 4/16; Jaccard 0.25; overlap/K 0.4.
- K=10, conviction/leverage: 0/20; Jaccard 0; overlap/K 0.
- K=10, conviction/lift: 4/16; Jaccard 0.25; overlap/K 0.4.
- K=10, leverage/lift: 0/20; Jaccard 0; overlap/K 0.
- K=25, confidence/conviction: 25/25; Jaccard 1; overlap/K 1.
- K=25, confidence/leverage: 1/49; Jaccard 0.0204081632653; overlap/K 0.04.
- K=25, confidence/lift: 10/40; Jaccard 0.25; overlap/K 0.4.
- K=25, conviction/leverage: 1/49; Jaccard 0.0204081632653; overlap/K 0.04.
- K=25, conviction/lift: 10/40; Jaccard 0.25; overlap/K 0.4.
- K=25, leverage/lift: 0/50; Jaccard 0; overlap/K 0.
- K=50, confidence/conviction: 48/52; Jaccard 0.923076923077; overlap/K 0.96.
- K=50, confidence/leverage: 5/95; Jaccard 0.0526315789474; overlap/K 0.1.
- K=50, confidence/lift: 17/83; Jaccard 0.204819277108; overlap/K 0.34.
- K=50, conviction/leverage: 6/94; Jaccard 0.063829787234; overlap/K 0.12.
- K=50, conviction/lift: 17/83; Jaccard 0.204819277108; overlap/K 0.34.
- K=50, leverage/lift: 4/96; Jaccard 0.0416666666667; overlap/K 0.08.

Four-way intersections: K=10: 0, K=25: 0, K=50: 2.

- confidence, K=10: full-precision boundary 0.5719887955182072; tied group 1; inside 1, outside 0.
- lift, K=10: full-precision boundary 21.982700791993565; tied group 1; inside 1, outside 0.
- leverage, K=10: full-precision boundary 0.006729725187735146; tied group 2; inside 2, outside 0.
- conviction, K=10: full-precision boundary 2.2738990054193224; tied group 1; inside 1, outside 0.
- confidence, K=25: full-precision boundary 0.4331813398807436; tied group 1; inside 1, outside 0.
- lift, K=25: full-precision boundary 17.636989749123728; tied group 2; inside 1, outside 1.
- leverage, K=25: full-precision boundary 0.004951444769204562; tied group 2; inside 1, outside 1.
- conviction, K=25: full-precision boundary 1.6912134522968125; tied group 1; inside 1, outside 0.
- confidence, K=50: full-precision boundary 0.34303753069098564; tied group 1; inside 1, outside 0.
- lift, K=50: full-precision boundary 13.651560783757928; tied group 2; inside 2, outside 0.
- leverage, K=50: full-precision boundary 0.0039112497543584; tied group 2; inside 2, outside 0.
- conviction, K=50: full-precision boundary 1.473221437540442; tied group 1; inside 1, outside 0.

Only K=25 lift/leverage boundaries split tied groups, each 1 inside/1 outside. Their lexical membership must not be interpreted as substantive rank separation. Full-precision reciprocal lift values may also differ at the last binary digits; exact API equality, not rounding or tolerance bucketing, determines statistical ties.

### Registered rank-gap examples

All examples below are selected by fixed average-rank gaps, gap >=100, at most three per category and canonical lexical tie breaks. Itemset names identify co-reporting patterns only; no clinical interpretation is attached. Ranks shown are average descending ranks. All counts/metrics are available at full precision in the machine-readable example export.

**high_confidence_relative_to_lift**: 187 eligible; 3 exported.

- `["REAC_CONDITION AGGRAVATED=1"]` -> `["REAC_OFF LABEL USE=1"]`; joint/A/B 1966/9979/26853; support 0.005102676439442702; confidence 0.19701372883054413; lift 2.8267614625428323; leverage 0.0032975448402406404; conviction 1.1584108380841822; ranks `{"confidence": 150.0, "conviction": 201.0, "leverage": 67.5, "lift": 489.5}`; gap 339.5.
- `["REAC_HYPERTENSION=1"]` -> `["REAC_OFF LABEL USE=1"]`; joint/A/B 895/4436/26853; support 0.0023229376466435496; confidence 0.20175834084761046; lift 2.8948373600154222; leverage 0.0015204961420779272; conviction 1.165112624954523; ranks `{"confidence": 147.0, "conviction": 193.0, "leverage": 511.5, "lift": 486.0}`; gap 339.0.
- `["REAC_PRODUCT USE ISSUE=1"]` -> `["REAC_OFF LABEL USE=1"]`; joint/A/B 871/4691/26853; support 0.0022606465812586947; confidence 0.18567469622681732; lift 2.6640685346083486; leverage 0.0014120773526930196; conviction 1.142124171437945; ranks `{"confidence": 164.0, "conviction": 226.0, "leverage": 521.5, "lift": 495.5}`; gap 331.5.

**high_conviction_relative_to_confidence**: 0 eligible; 0 exported.

Empty category; the threshold remains 100.


**high_leverage_relative_to_lift**: 165 eligible; 3 exported.

- `["REAC_CONDITION AGGRAVATED=1"]` -> `["REAC_OFF LABEL USE=1"]`; joint/A/B 1966/9979/26853; support 0.005102676439442702; confidence 0.19701372883054413; lift 2.8267614625428323; leverage 0.0032975448402406404; conviction 1.1584108380841822; ranks `{"confidence": 150.0, "conviction": 201.0, "leverage": 67.5, "lift": 489.5}`; gap 422.0.
- `["REAC_OFF LABEL USE=1"]` -> `["REAC_CONDITION AGGRAVATED=1"]`; joint/A/B 1966/26853/9979; support 0.005102676439442702; confidence 0.07321342121923062; lift 2.8267614625428323; leverage 0.0032975448402406404; conviction 1.0510086972198103; ranks `{"confidence": 477.0, "conviction": 500.0, "leverage": 67.5, "lift": 489.5}`; gap 422.0.
- `["REAC_DIARRHOEA=1"]` -> `["REAC_FATIGUE=1"]`; joint/A/B 2825/14774/15718; support 0.00733217748800897; confidence 0.19121429538378232; lift 4.687146802381138; leverage 0.0057678617545473855; conviction 1.1858818342833517; ranks `{"confidence": 159.0, "conviction": 171.0, "leverage": 13.5, "lift": 397.5}`; gap 384.0.

**high_lift_relative_to_leverage**: 170 eligible; 3 exported.

- `["REAC_PRURITUS=1"]` -> `["REAC_SKIN BURNING SENSATION=1"]`; joint/A/B 786/11461/1202; support 0.002040032391354; confidence 0.0685804031061862; lift 21.98270079199357; leverage 0.0019472306737371636; conviction 1.0701802746181008; ranks `{"confidence": 491.5, "conviction": 420.0, "leverage": 373.5, "lift": 9.0}`; gap 364.5.
- `["REAC_SKIN BURNING SENSATION=1"]` -> `["REAC_PRURITUS=1"]`; joint/A/B 786/1202/11461; support 0.002040032391354; confidence 0.653910149750416; lift 21.982700791993565; leverage 0.0019472306737371636; conviction 2.7967496686399143; ranks `{"confidence": 7.0, "conviction": 7.0, "leverage": 373.5, "lift": 10.0}`; gap 363.5.
- `["REAC_ABDOMINAL PAIN=1"]` -> `["REAC_DIARRHOEA=1", "REAC_VOMITING=1"]`; joint/A/B 799/5616/3075; support 0.0020737733851041297; confidence 0.14227207977207978; lift 17.82625205568295; leverage 0.0019574408336162233; conviction 1.156325957638507; ranks `{"confidence": 240.5, "conviction": 204.0, "leverage": 365.5, "lift": 21.5}`; gap 344.0.

### Complete statin-containing itemset support explanation

All **2,513 statin-reaction pairs and 21 distinct statin-statin pairs** were counted directly in the hashed frozen primary PS ARFF. The largest statin-reaction joint count is **141**, for `{rosuvastatin, MYALGIA}`. Every statin-statin pair has joint count **0**, including `{atorvastatin, rosuvastatin}`. The full pair table retains every zero.

Every statin-containing itemset of size >=2 includes a statin-reaction pair or a statin-statin pair. Its support cannot exceed that pair's support. Since pairs themselves are members of the family, the maximum over **all statin-containing itemsets of size >=2 is exactly 141**, not merely an upper bound on drug-reaction pairs.

Compare 141 with Apriori/FPGrowth cutoffs: 0.001 **385/386**; 0.002 **771/771**; 0.003 **1156/1156**; 0.004 **1541/1542**. Therefore: **No statin-containing itemset of size 2 or more reaches the minimum.** Any nonempty disjoint rule containing a statin has such a joint itemset, including two-statin antecedents and mixed multi-item rules.

Atorvastatin (1157) and rosuvastatin (864) qualify as singletons at 771; those marginals cannot overcome the joint-count constraint. This explains the unrestricted absence by support eligibility, rather than clinical properties. It is not evidence that statins have no adverse-event associations. Removing unrelated attributes at fixed criteria cannot change a given rule's counts/metrics; no further statin-recovery mining is scheduled.

The unrestricted WEKA showcase is an algorithm and metric study on reaction co-reporting. The projected experiment is the FAERSight drug-safety analysis.

The frozen primary one-reaction-at-a-time design uses the registered much lower support grid and the same full report denominator to permit its intended statin->reaction comparisons. That experiment is unchanged.

### Distributions, tables and three charts

The machine-readable distribution export contains minimum/median/finite mean/maximum, empirical inverse-CDF percentiles 5/25/50/75/95, distinct values, tied-rule counts/fractions and largest tie group. Exact API ties are retained; no rounded console values are used. Infinity handling is explicit even though none occurs here.

- confidence: min/median/mean/max 0.028935314490001116/0.11971011521395974/0.1610856257948585/0.8181818181818182; 578 distinct; 16/586 tied (2.730375%); largest group 2.
- lift: min/median/mean/max 1.2659952860953259/6.067263237208913/8.039308885250417/277.00846780635885; 418 distinct; 336/586 tied (57.337884%); largest group 2.
- leverage: min/median/mean/max 0.0004839970360777817/0.002124015908637039/0.002366621480441641/0.011993783597483793; 293 distinct; 586/586 tied (100.000000%); largest group 2.
- conviction: min/median/mean/max 1.0096511229199383/1.1065785498099667/1.2019871973460534/5.453789134872411; 586 distinct; 0/586 tied (0.000000%); largest group 1.

Tracked output directory: `artifacts/manifests/weka-showcase-metrics/run/`.

- [Canonical pool](../artifacts/manifests/weka-showcase-metrics/run/canonical_pool.json), four `ranking_<metric>.csv/.json` files, raw API strings and both-miner provenance.
- [Spearman CSV](../artifacts/manifests/weka-showcase-metrics/run/spearman.csv), separate full/subset JSONs, Top-K CSV/JSON, boundary-tie CSV/JSON, four-way JSON, rank-gap JSON, distribution CSV/JSON.
- [Complete statin pair counts](../artifacts/manifests/weka-showcase-metrics/run/statin_pair_counts.csv), threshold comparisons CSV and the bound/proof JSON.
- [Spearman matrix](../artifacts/manifests/weka-showcase-metrics/run/charts/spearman_matrix.png).
- [Highest-agreement scatter](../artifacts/manifests/weka-showcase-metrics/run/charts/rank_scatter_highest.png): confidence/conviction, rho 0.9648123764153352.
- [Lowest-agreement scatter](../artifacts/manifests/weka-showcase-metrics/run/charts/rank_scatter_lowest.png): confidence/lift, rho 0.46369169898167756.

Exactly three charts are supplied in PNG and SVG, selected from the full-pool correlations with canonical metric-name pair tie breaks. No additional or decorative plots. All three were visually inspected; source/axes/tie/range limitations are legible. Plotting uses a separately pinned existing local Python/Matplotlib environment, recorded in the lock and validation; the primary environment/dependencies were not modified. Rendering all three a second time produces identical bytes.

### Bounded conclusion and next checkpoint

Within the same 586 WEKA rules already satisfying support 0.002 and lift >= 1.2, confidence, lift, leverage, and conviction can prioritize rules differently because they measure different properties of association.

No metric is declared universally superior. The rules do not establish validated safety signals, causality, clinical interactions, incidence or risk. Student interpretation and authorship remain required for presentation use.

The unrestricted WEKA showcase is an algorithm and metric study on reaction co-reporting. The projected experiment is the FAERSight drug-safety analysis.

Unrestricted Apriori study, Apriori/FPGrowth comparison, Fallback A and metric-ranking comparison are complete. **WEKA Explorer demonstration is next, pending explicit authorization.** Final showcase summary/demo packaging follows Explorer; neither is executed here. No additional supports, algorithms, statin-rule mining or scaling diagnostics are scheduled. Preserve this framing in later Explorer/demo/report/slide support material.


## Validation record

All **171 tests pass**, zero failures/errors/skips: 153 retained and 18 new.
Actual WEKA fixture tests remain enabled; the new native probe performs zero
association builds. Ruff check and format pass (71 files). Independent SciPy
checks all 12 full/subset correlations within **1.1102230246251565e-16** and
matches all full-pool average ranks exactly; no p-values are used. All four
ranking orders and deterministic JSON serialization pass independent checks;
all three full-pool PNG/SVG charts reproduce byte-for-byte.

All **336 protected prior tracked files** match frozen A3 `0c80bd1`; all
**108 scientific-core files** match `69d27d7`; all **1,096 primary and 1,106
sensitivity generated artifacts** retain their hashes. The full-data mining
invocation inventory is unchanged. No primary/sensitivity artifact, configuration,
manifest or scientific validation flag changed.

Evidence includes the locked analysis manifest, both-miner source hashes,
count-only probe raw/parsed/recomputed values, JUnit results, independent
validation record and SHA-256 index. `scientific_findings_validated` remains false.

Evidence-index SHA-256: `1980910f61406bed9cc26209f9075ced1ada381357dd09e9ab34704fdeb4a49b`.

Read-only reproduction audit: `.venv/Scripts/python scripts/verify_showcase_metrics.py`.
The offline calculation entry point is `.venv/Scripts/python -m showcase_metrics.runner run`; it requires the committed lock, original inputs/runtimes and a previously absent output directory. It launches no associator.
