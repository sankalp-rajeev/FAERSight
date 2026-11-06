# WEKA Explorer demonstration verification

The unrestricted WEKA showcase is an algorithm and metric study on reaction co-reporting. The projected experiment is the FAERSight drug-safety analysis.

Explorer is a presentation/demo layer. Scripted runs and frozen evidence remain authoritative. This checkpoint permits a repeat of one deterministically selected projected search for demonstration, not a new experiment. No support search, original expensive 0.001 Apriori rerun, new comparison, metric search or statin-recovery study is authorized.

## GUI checkpoint complete: November 6, 2026

The student completed the manual Explorer verification and supplied three GUI
screenshots, inspected for this completion record:

- [Full-data Preprocess view](../images/FAERSight-dataset.png): relation `faersight`,
  **385,288 instances / 366 attributes**, filter `None`, and nominal
  `DRUG_atorvastatin` counts **384,131 absent / 1,157 present**, with no missing values.
- [Projected Apriori settings and results](../images/results.png): relation
  `faersight_projection`, **385,288 instances / 8 attributes**, the exact frozen
  Apriori command, one cycle, minimum count **4**, and all **four expected rules**.
- [Full-data FPGrowth settings and results](../images/FPGrowth.png): relation
  `faersight`, **385,288 instances / 366 attributes**, the exact frozen A1 FPGrowth
  command and **70 rules**. The visible leading reaction-only rules agree with
  the preserved A1 output; the screenshot is not a full-precision 70-rule export.

The [completed verification checklist](weka_explorer_verification_checklist.md)
distinguishes supported observations from measurements that were not captured.

**Status: GUI checkpoint complete by manual verification.** The earlier automated
computer-use connection failure did not prevent the student from using Explorer.
Full-data loading and completed association results are now evidenced. No 10k
fallback was needed for these demonstrated runs.

Load duration, navigation latency, the live JVM heap and the live Java/WEKA version
were not captured in these screenshots; no new timing or runtime attestation is
claimed. The frozen runtime below remains the reproduction specification.
The original preparation manifests retain their historical pending statuses;
this dated record supplies the subsequent manual GUI evidence. Scientific findings
remain `scientific_findings_validated: false` pending the separate student reviews.

Previously, the Windows computer-use helper failed with `Computer Use native pipe
is unavailable: failed to connect native pipe: The system cannot find the file
specified. (os error 2)` during initial discovery and two recovery attempts. That
history remains relevant to the automated preparation, not the current manual
checkpoint status.

## Prepared inputs, runtime and expected scientific result

Preparation code commit `296b8a2`. WEKA **3.8.6**, pinned OpenJDK
**21.0.10+-14961533-b1163.108**; intended Explorer JVM heap **4 GiB**
(`-Xmx4g`, observed in the non-GUI preflight as 4294967296 bytes),
`-XX:ActiveProcessorCount=2` as a JVM hint, not parallel mining or CPU quota.
The exact launch command is recorded in `preparation_manifest.json`; it was not
executed during automated preparation. The manual screenshots do not show the
launch invocation.

From the repository root, the prepared launch command is:

```powershell
& 'C:\Program Files\Android\Android Studio\jbr\bin\java.exe' -Xmx4g -XX:ActiveProcessorCount=2 -cp '.tools/weka/weka-stable-3.8.6.jar;.tools/weka/bounce-0.18.jar' weka.gui.explorer.Explorer
```

Run only one JVM at a time. This command opens Explorer; it does not load a file
or start mining automatically. Manual GUI observations are recorded above.

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

The unmodified scripted primary ran 1,077 projected searches. The manual demo
repeated the selected projected search. The frozen raw r0239 result
contains **four general rules**; its scientific CSV retains **two statin->reaction
rules** after the frozen direction/output filter. The screenshot confirms the
native general four-rule display; the scientific export contract is unchanged.

The selected rule's frozen printed confidence/lift are approximately **0.02/37.66**.
Printed fractional support may appear as **0**, while the integer cutoff is **4**.
The GUI shows the same rounded confidence/lift and `Minimum support: 0 (4 instances)`
as the frozen output. Full-precision API values remain authoritative.

## Verified GUI options and reproduction settings

The separate Java preflight sets options and inspects JavaBean getters, setters,
display-name metadata, selected tags and tooltips from the exact pinned binary.
It performed **zero association builds and zero GUI input** during preparation.
The subsequent manual screenshots show the actual Apriori and FPGrowth option
strings and completed results. Individual property dialogs were not captured;
the settings below also retain the prior bean/API verification.

Primary projected Apriori bean settings:

- `numRules=10000` (`-N`); `metricType=Lift`, tag 1 (`-T 1`);
  `minMetric=1.2` (`-C`).
- `lowerBoundMinSupport=0.00001` (`-M`);
  `upperBoundMinSupport=1.0` (`-U`); `delta=1.0` (`-D`).
- `treatZeroAsMissing=true` (`-Z`): first nominal label 0 is absence, present label 1.
- `significanceLevel=-1.0` (`-S -1.0`), disabled; this is not the fixed-support flag.
- `car=false`; `classIndex=-1`; `removeAllMissingCols=false`;
  `outputItemSets=false`; `verbose=false`; `doNotCheckCapabilities=false`.
- The screenshot retains all eight columns, including all-zero lovastatin, and
  all reports. Its option string uses `-c -1` with CAR disabled; individual class,
  capability and filter property dialogs were not captured.

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
- The manual FPGrowth screenshot confirms the exact option string below and a
  completed full-data run reporting 70 rules. Individual property dialogs and a
  complete GUI rule export were not captured.

Exact frozen FPGrowth options:

```text
-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.004 -D 1.0 -S
```

Frozen A1 FP minimum count is **1542**, **70 rules**; build **0.32545 s**,
JVM wall **0.7356508999946527 s**. Disclose Apriori's 1541 versus FP's 1542
native count mismatch: the already validated common-count comparison at 1542
also returns identical 70-rule sets. Do not rerun comparisons, calculate a new
speed ratio or claim universal performance from these demonstrations.

## Completed manual checks and evidence limits

The full-data Preprocess screenshot confirms **385288 reports / 366 attributes**
and shows the atorvastatin presence distribution. The projected result retains
all seven statins, including lovastatin, plus MYOPATHY. Completed Apriori and
FPGrowth output is visible in Associate. These captures establish successful
loading and execution; they do not measure load time or navigation responsiveness.
The full-data Preprocess class visualization selects the last reaction attribute;
the projected Apriori command explicitly uses `-c -1` and does not enable CAR.

**No 10k fallback was needed for the demonstrated runs.** The full file loaded,
and FPGrowth completed on all 385,288 reports and 366 attributes. The primary
eight-column projection also retains all reports; it is not a row subset.

The projected Apriori screenshot matches frozen r0239 at displayed precision:

- `DRUG_atorvastatin=1 -> REAC_MYOPATHY=1`: antecedent **1157**, joint **19**,
  displayed confidence **0.02**, lift **37.66**.
- Reverse atorvastatin rule: antecedent **168**, joint **19**, displayed
  confidence **0.11**, lift **37.66**.
- `DRUG_rosuvastatin=1 -> REAC_MYOPATHY=1`: antecedent **864**, joint **12**,
  displayed confidence **0.01**, lift **31.85**.
- Reverse rosuvastatin rule: antecedent **168**, joint **12**, displayed
  confidence **0.07**, lift **31.85**.

Minimum support displays as **0 (4 instances)**, lift floor is **1.2**, one cycle
is reported, and frequent-itemset counts are **L(1)=7 / L(2)=2**. All match the
frozen raw result. The four general GUI rules include two reverse directions;
the scientific CSV retains only the two statin-to-reaction rules.

The projected screenshot captures both the complete option string and results,
so a separate settings-dialog screenshot is not required for this record.
The optional full-data FPGrowth screenshot additionally shows the registered
`-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.004 -D 1.0 -S` settings and
70-rule result. Complete rule-set equality and exact metric agreement remain
supported by the frozen scripted evidence, rather than inferred from a partial
GUI display. No new GUI timing comparison is made.

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
contains the historical blocked GUI statuses, exact launch/configuration options, all prior
file hashes, source selection, projected-file provenance and native preflight.
Frozen raw result copies are preserved with source-archive/member provenance:
`frozen_primary_projected_result.log`, `frozen_A1_apriori_result.log` and
`frozen_A1_fpgrowth_result.log`. They are preserved scripted outputs, not newly
observed Explorer results or an importable serialized Explorer model.

The [rehearsal cues](weka_explorer_demo_script.md) are preparation support for
student adaptation, not final report/slide packaging. No new mining stage or final
packaging is authorized by this documentation update. **Explorer GUI verification
is complete**, supported by the linked manual screenshots. Final showcase/project
packaging remains a separate step requiring explicit authorization. Core scientific
review and student-authored course work remain outstanding.


## Historical preparation validation and current checks

At the preparation checkpoint, all **180 tests passed**, zero failures/errors/skips
(171 retained, 9 new), including
actual pinned WEKA fixture tests and the new parse/option preflight. Lint/format
pass (75 files). All **393 protected prior files**, **108 frozen-core files**,
**1096 primary** and **1106 sensitivity generated artifacts** retain their
registered hashes. The full-data mining inventory is unchanged. No original
configuration, evidence, manifest or scientific-validation boundary changed.

Verification: `.venv/Scripts/python scripts/verify_explorer_preparation.py`.
The evidence index SHA-256 is `550ef16e0aee10a47d177a8f287092ad31983bfe76c3c00c4989e46aa6bf6ede`.

On November 6, 2026, the current local suite passed **192 tests**, with WEKA
enabled and no skips. Ruff lint, format checks for all Python source/test/showcase
directories and scripts (80 files), and frozen configuration validation also passed.
The [current validation record](../artifacts/manifests/weka-explorer-verification-20261106/validation.json)
records these checks and artifact-integrity results. Automated checks do not
replace the manual GUI evidence above.

This completion update records the student-provided screenshots and updates the
engineering record, checklist, roadmap, README and rehearsal status. The
[dated manual manifest](../artifacts/manifests/weka-explorer-verification-20261106/manual_verification.json)
and companion validation record preserve the new evidence separately. Historical
evidence manifests, scientific outputs, exact version information and scientific
validation boundaries remain unchanged.
