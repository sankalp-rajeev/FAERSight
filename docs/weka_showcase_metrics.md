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
