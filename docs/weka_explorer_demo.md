# WEKA Explorer demonstration preparation

The unrestricted WEKA showcase is an algorithm and metric study on reaction co-reporting. The projected experiment is the FAERSight drug-safety analysis.

Explorer is a presentation/demo layer. Scripted runs and frozen evidence remain authoritative. This checkpoint permits a repeat of one deterministically selected projected search for demonstration, not a new experiment. No support search, original expensive 0.001 Apriori rerun, new comparison, metric search or statin-recovery study is authorized.

## Current GUI blocker

The Windows computer-use helper failed with `Computer Use native pipe is unavailable: failed to connect native pipe: The system cannot find the file specified. (os error 2)` on initial app discovery, a delayed window-list retry, and a final window-list attempt after resetting and reinitializing the JavaScript session. No target window or screenshot was returned.

Actual Explorer load time, displayed counts, responsiveness, GUI settings, GUI rule agreement and screenshots are **pending, unverified**. Do not substitute API parsing or JavaBean metadata for those observations. No Explorer launch or live rule build is claimed. The checkpoint cannot be marked complete until GUI observation is available.

Proceed with independent preparation: pinned runtime/hash checks, deterministic projected-pair selection, all-row sparse projection, frozen result references, bean metadata inspection without mining, presenter rehearsal notes and validation. No 10k fallback is generated merely because computer use is disconnected; full-data usability must first be observed.


## Prepared inputs, runtime and expected scientific result

Preparation code commit `296b8a2`. WEKA **3.8.6**, pinned OpenJDK
**21.0.10+-14961533-b1163.108**; intended Explorer JVM heap **4 GiB**
(`-Xmx4g`, observed in the non-GUI preflight as 4294967296 bytes),
`-XX:ActiveProcessorCount=2` as a JVM hint, not parallel mining or CPU quota.
The exact launch command is recorded in `preparation_manifest.json`; **not executed**.

From the repository root, the prepared launch command is:

```powershell
& 'C:\Program Files\Android\Android Studio\jbr\bin\java.exe' -Xmx4g -XX:ActiveProcessorCount=2 -cp '.tools/weka/weka-stable-3.8.6.jar;.tools/weka/bounce-0.18.jar' weka.gui.explorer.Explorer
```

Run only one JVM at a time. This command opens Explorer; it does not load a file
or start mining automatically. GUI observations remain pending.

- Full input: `artifacts/generated/2025Q4-statins-mining/input/transactions.arff`;
  385,288 reports, 366 attributes, sparse binary `{0,1}`. SHA-256
  `de0f94f545ebae18033195524984fc842d3359154b864cb52bef2372a877dcf1`.
- Prepared primary demo input:
  `artifacts/generated/weka-explorer-demo/primary_MYOPATHY_projection.arff`;
  **385,288 reports, 8 attributes**, all seven statins followed by MYOPATHY.
  SHA-256 `c13b0b84f123c26d48be11b0662f96805eeaf34292c5d5b2388cea1f89c3d73b`.
  This is a column projection, not a row subset. All source report order and
  all empty baskets remain; **382,855** projected baskets are empty.
- Source columns (zero-based): 0,1,2,3,4,5,6,246. Full input has 117,325 empty
  baskets; projection creates further empty baskets without deleting reports.
- Runtime hashes: Java executable
  `7f7bc646f8697255fc98a950412c741a453360586e1208ce683212f638444d85`;
  WEKA jar `932ea2f342b58fe45736389e9c426d5b5955e610d1f5f6485117f532068915e9`;
  Bounce dependency `bffff1505335c02256b7ab2ccffbe4aa4d3ac9fe14c17557809b7c9d99d666ca`.
  All paths/hashes are preserved in the prior locked runtime configuration.

Representative selection is the first benchmark-positive drug/reaction in
canonical lexical order accepted by frozen primary WEKA at support `0.00001`:
**atorvastatin -> MYOPATHY**, projection **r0239**. It was not chosen for clinical
attractiveness. Frozen counts: joint **19**, antecedent **1157**, consequent **168**,
denominator **385288**; support `19/385288 = 4.931376009634351e-05`, confidence
**0.016421780466724288**, lift **37.66139852656707**. The projected ARFF and WEKA
parser independently recover the marginals/joint count. Native API parsing took
0.0703794 s; **this is not an Explorer load time or GUI usability observation**.

The unmodified scripted primary ran 1,077 projected searches. This demo repeats
only one, once actual GUI observation is possible. The frozen raw r0239 result
contains **four general rules**; its scientific CSV retains **two statin->reaction
rules** after the frozen direction/output filter. The expected GUI output is the
native general four-rule display, not a new scientific export contract.

The selected rule's frozen printed confidence/lift are approximately **0.02/37.66**.
Printed fractional support may appear as **0**, while the integer cutoff is **4**.
These are known text-format rounding effects in preserved results, not a GUI
comparison that has already passed. Full-precision API values remain authoritative.

## GUI settings to check, and what has actually been verified

The separate Java preflight sets options and inspects JavaBean getters, setters,
display-name metadata, selected tags and tooltips from the exact pinned binary.
It performs **zero association builds and zero GUI input**. These are verified
underlying properties, **not observed Explorer fields**. Actual UI availability,
labels, option round-trips and class handling remain a checklist for completion.

Primary projected Apriori bean settings:

- `numRules=10000` (`-N`); `metricType=Lift`, tag 1 (`-T 1`);
  `minMetric=1.2` (`-C`).
- `lowerBoundMinSupport=0.00001` (`-M`);
  `upperBoundMinSupport=1.0` (`-U`); `delta=1.0` (`-D`).
- `treatZeroAsMissing=true` (`-Z`): first nominal label 0 is absence, present label 1.
- `significanceLevel=-1.0` (`-S -1.0`), disabled; this is not the fixed-support flag.
- `car=false`; `classIndex=-1`; `removeAllMissingCols=false`;
  `outputItemSets=false`; `verbose=false`; `doNotCheckCapabilities=false`.
- Verify that Explorer has not assigned a class or changed capabilities/filters;
  preserve all eight columns, including all-zero lovastatin, and all reports.
  If any GUI setting cannot reproduce the scripted conditions, record that
  limitation and do not alter scientific settings to make a demonstration succeed.

Exact frozen projected options:

```text
-N 10000 -T 1 -C 1.2 -D 1.0 -U 1.0 -M 1.0E-5 -S -1.0 -Z -c -1
```

Unrestricted Apriori at **0.004** is configuration/result display only, not a live
several-minute search. The underlying fields are the same except `numRules=100000`
and `lowerBoundMinSupport=0.004`. Frozen A1: minimum count **1541**, **70 rules**,
build **393.9657375 s**, JVM wall **394.3502293000347 s**. Do not click Start for
this unrestricted Apriori demonstration; never run the expensive 0.001 search.

FPGrowth underlying properties and their verified meanings:

- `lowerBoundMinSupport=0.004` (`-M`); `upperBoundMinSupport=1.0` (`-U`);
  `delta=1.0` (`-D`).
- `metricType=Lift`, tag 1 (`-T 1`); `minMetric=1.2` (`-C`), inclusive floor.
- `positiveIndex=2` (`-P 2`), **one-based nominal value index** for label 1 in
  `{0,1}`. The bean tooltip says sparse data ignores the index; the already verified
  implementation shows that P also determines emitted labels. Keep 2; do not
  change it to 1 based on the tooltip. Stored sparse nonzero presences are counted.
- `findAllRulesForSupportLevel=true` (`-S` flag) disables iterative support descent
  and returns all qualifying rules at the lower support. This flag is unrelated
  to Apriori's significance option of the same name.
- `maxNumberOfItems=-1` (`-I -1`), no user length restriction.
- `numRulesToFind=100000` (`-N`), **not an effective cap in find-all/-S mode**.
  Original completeness checks compare native internal/API counts and stop at
  the registered policy threshold; a GUI rule count alone cannot replace those.
- `transactionsMustContain=""`, `rulesMustContain=""` and
  `useORForMustContainList=false`; no feature/outcome/direction filtering.
- Actual Explorer fields/configuration are **unverified**. A live FP repeat is
  conditional on full-data GUI usability and exact settings verification; none ran.

Exact frozen FPGrowth options:

```text
-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.004 -D 1.0 -S
```

Frozen A1 FP minimum count is **1542**, **70 rules**; build **0.32545 s**,
JVM wall **0.7356508999946527 s**. Disclose Apriori's 1541 versus FP's 1542
native count mismatch: the already validated common-count comparison at 1542
also returns identical 70-rule sets. Do not rerun comparisons, calculate a new
speed ratio or claim universal performance from these demonstrations.

## Full-ARFF and fallback completion checklist

Once the Windows GUI connection is available, launch the recorded Explorer
command with 4 GiB heap and one JVM at a time. Do not launch during fixture tests.
In Preprocess, time the actual full-ARFF load and record the start/ready timing
boundary; confirm **385288 reports / 366 attributes** on screen. Inspect one
`DRUG_*` and one `REAC_*` attribute; navigate to Associate and back, observing
responsiveness. Record any slow, frozen or failed operation without an invented
resource diagnosis. Inspect filtering controls without applying a data change.

**10k fallback not generated; need is undetermined.** Only if the observed full
ARFF is impractical for the live demo, use the first 10,000 reports in canonical
case-index order with all 366 attributes and sparse encoding, preserving empty
baskets and recording selection/source/output hashes and counts. Label it
**GUI DEMO SUBSET — not used for scientific results**. No rule-content/outcome
sampling or attribute filtering. Do not confuse the all-row eight-column primary
projection with this conditional row-subset fallback.

Load the prepared primary projection, inspect/configure Apriori, and perform the
one authorized GUI repeat. Compare the selected rule's direction, counts, support,
confidence and lift with frozen r0239 evidence. Rounded display differences should
be annotated, not fixed by editing scientific results. Verify the raw general
four-rule display and scientific filtered two-rule export distinction. Record any
other GUI/API difference as observed; no actual comparison is claimed yet.

Minimum screenshots pending: (1) full Preprocess dimensions and representative
attribute; (2) projected Apriori settings; (3) projected rule result; optionally
(4) FPGrowth settings/result if useful. Capture genuine current GUI states only;
crop paths/personal details only when needed, without changing scientific content.
**No screenshots have been captured or fabricated.**

## Frozen metric and statin explanation references

Use the [existing metric matrix](../artifacts/manifests/weka-showcase-metrics/run/charts/spearman_matrix.png)
and optionally the [registered confidence/conviction scatter](../artifacts/manifests/weka-showcase-metrics/run/charts/rank_scatter_highest.png).
No new metric searches, plots or ranking calculations. The same **586** rules,
already qualified by support 0.002 and lift >=1.2, were ranked with four full-precision
API metrics. Average-rank confidence/conviction rho is **0.9648123764153352**;
other metric pairs have substantially less Top-K overlap. No metric is universally
best. Rule dependence and the lift-qualified range limit the interpretation.

The exact maximum joint count over **all statin-containing itemsets size >=2** is
**141**, attained by rosuvastatin/MYALGIA; every statin-statin pair has count 0.
No such itemset reaches thresholds **385/386, 771, 1156, 1541/1542**. Singleton
eligibility does not imply that a statin-reaction joint itemset satisfies minimum
support. This explains unrestricted support eligibility, not absence of statin
adverse-event associations. The much lower-support projected scientific experiment
retains the full denominator and remains unchanged.

The unrestricted WEKA showcase is an algorithm and metric study on reaction co-reporting. The projected experiment is the FAERSight drug-safety analysis.

## Evidence and stop boundary

[Preparation manifest](../artifacts/manifests/weka-explorer-demo/preparation_manifest.json)
contains the blocked GUI statuses, exact launch/configuration options, all prior
file hashes, source selection, projected-file provenance and native preflight.
Frozen raw result copies are preserved with source-archive/member provenance:
`frozen_primary_projected_result.log`, `frozen_A1_apriori_result.log` and
`frozen_A1_fpgrowth_result.log`. They are preserved scripted outputs, not newly
observed Explorer results or an importable serialized Explorer model.

The [rehearsal cues](weka_explorer_demo_script.md) are preparation support for
student adaptation, not final report/slide packaging. No new mining stage or final
packaging is authorized. Explorer remains **incomplete pending GUI connection**;
final showcase/project packaging remains after completed Explorer and explicit
authorization.


## Preparation validation and resume requirements

All **180 tests pass**, zero failures/errors/skips (171 retained, 9 new), including
actual pinned WEKA fixture tests and the new parse/option preflight. Lint/format
pass (75 files). All **393 protected prior files**, **108 frozen-core files**,
**1096 primary** and **1106 sensitivity generated artifacts** retain their
registered hashes. The full-data mining inventory is unchanged. No original
configuration, evidence, manifest or scientific-validation boundary changed.

Verification: `.venv/Scripts/python scripts/verify_explorer_preparation.py`.
The evidence index SHA-256 is `550ef16e0aee10a47d177a8f287092ad31983bfe76c3c00c4989e46aa6bf6ede`.

To finish this authorized checkpoint, restore the Windows computer-use connection
and resume the actual GUI checklist: full-file load/usability/timing, Preprocess
attribute inspection, primary projected Apriori configuration/result agreement,
FPGrowth UI-property confirmation and minimal genuine screenshots. Determine
whether a 10k fallback is needed from actual full-file usability, not this tool
failure. Then update this record/roadmap to complete, validate and commit/push.
Until those checks are observed, Explorer is incomplete and final packaging has
not begun.
