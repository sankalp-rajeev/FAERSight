# Explorer rehearsal cues: target 2-3 minutes

Preparation aid for student adaptation. This sequence has **not been rehearsed in
Explorer** because the Windows GUI connection is unavailable. It is not a final
report, slide deck or completed GUI validation. Use reports/cases, never patients.

The unrestricted WEKA showcase is an algorithm and metric study on reaction co-reporting. The projected experiment is the FAERSight drug-safety analysis.

1. **0:00-0:25 - full Preprocess view.** Open the pinned Explorer with the prepared
   4 GiB launch command, then open the frozen full ARFF. Show 385,288 reports and
   366 attributes. "Python handled acquisition, cleaning, deduplication, exact drug
   mapping and ARFF construction. WEKA performs association-rule mining. One report
   is one transaction; reports without target statins remain in the denominator."
2. **0:25-0:45 - transaction structure.** Point to `DRUG_atorvastatin` and a `REAC_*`
   attribute. "These are nominal zero/one presences. Sparse omissions mean zero.
   The full data contains seven statins and 359 reactions." Inspect controls without
   applying filters or dropping reports.
3. **0:45-1:15 - primary projected setup.** Open the prepared all-report MYOPATHY
   projection: still 385,288 reports, now eight attributes. "This keeps all seven
   statins and one reaction. The selected atorvastatin/MYOPATHY pair is the first
   canonical frozen benchmark-positive pair accepted at support 0.00001." Open
   Associate/Apriori and show the exact documented settings: lift, 1.2 floor,
   minimum support 0.00001, upper 1, decrement 1, first-value-zero handling on.
4. **1:15-1:40 - one projected rule.** Once GUI settings are verified, run only this
   authorized projected demonstration. Point out the expected frozen result:
   "19 reports contain both; confidence is 19/1157, about 0.01642; lift is about
   37.66. These are reporting associations, not incidence or causal effects."
   Annotate rounded GUI text. If a repeat fails or differs, use the labeled frozen
   scripted result and state the observed limitation; never silently substitute it
   for a verified GUI result.
5. **1:40-2:05 - unrestricted study, secondary.** Briefly show A1 support 0.004
   settings and preserved 70-rule outputs for Apriori/FPGrowth. Do not run Apriori
   live: measured JVM wall was 394.35 s versus FP 0.736 s under the recorded
   envelope. Mention the 1541/1542 cutoff difference and validated common-count
   agreement if discussing direct equivalence. Use preserved results; a live FP
   repeat is optional only after exact GUI configuration/usability verification.
6. **2:05-2:25 - metric matrix.** Show the existing 586-rule matrix. "These four
   metrics ranked exactly the same already lift-qualified pool. Confidence and
   conviction ranked similarly; other pairs overlapped less. No metric is
   universally best, and these overlapping rules are not independent observations."
7. **2:25-2:40 - joint-support explanation.** "The largest statin-containing itemset
   count was 141, below every unrestricted threshold. Singleton eligibility does
   not imply joint-support eligibility. Zero unrestricted statin rules does not
   mean there are no statin adverse-event associations."
8. **2:40-2:55 - finish with scope.** "The unrestricted WEKA showcase is an algorithm
   and metric study on reaction co-reporting. The projected experiment is the
   FAERSight drug-safety analysis."

Preload the frozen result logs and metric matrix outside the timed sequence.
The clock allocation is a target, not an observed rehearsal duration. The GUI-only
10k fallback may be used only after documented full-file impracticality, labeled
"GUI DEMO SUBSET — not used for scientific results."

Pending minimal screenshots: full Preprocess dimensions, projected Apriori
configuration, projected rule result; optional FPGrowth configuration/result.
See [the exact settings and pending checks](weka_explorer_demo.md).
