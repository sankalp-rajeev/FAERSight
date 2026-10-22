# FAERSight roadmap

Engineering planning record, October 22, 2026. These are implementation and
demonstration aids; submitted reports, slides and narration remain student-authored.

## Frozen 2025 Q4 scientific core

The [Milestone 3 primary PS experiment](milestone3.md) and
[Milestone 4 PS+SS sensitivity](milestone4.md) are completed computational
checkpoints. Their input definitions, mappings, results, hashes, evidence and
manifests remain unchanged. Student source/alias/benchmark inspection and final
interpretation remain unsigned. Planning this extension does not complete those
reviews or change any `scientific_findings_validated: false` boundary.

## Post-core milestone: WEKA Showcase / Tool-Study Extension

**Subsequent authorization:** the appended post-timeout amendment below authorizes
one FPGrowth 0.001 feasibility attempt after semantic/fixture/configuration gates.
The original Apriori ladder remains stopped. Historical checkpoint statements
below describe their respective authorizations; they are preserved as history.

Purpose: stronger course alignment and demonstration of WEKA's association
analysis tools, separately from the scientific pair-comparison question.

**Current checkpoint: Step 2B support 0.001 attempted once and stopped at the
registered 1,800-second timeout.** See the [attempt record](weka_showcase_step2b.md).
Step 2A prerequisites remain locked and unchanged. The registered first-failure
rule blocks descent; no lower support or Step 3-7 execution has begun. Preserve
the failed attempt, commit/push its evidence, and stop. Any retry or change needs
a separate review/plan amendment; subsequent listed steps are not authorization
to execute the extension unattended.

### 1. Freeze/document the extension plan

Status: plan recorded here and in [decisions.md](decisions.md). No new mining,
benchmark interpretation or GUI execution is part of this documentation step.

Use the existing **primary PS full sparse ARFF**, not a regenerated PS+SS input:

- Local input: `artifacts/generated/2025Q4-statins-mining/input/transactions.arff`.
- 385,288 reports; 366 attributes: seven statins and 359 reactions.
- Nominal order `{0,1}`; present items are `1`, and omitted sparse values are `0`.
- Retain all reports, including the 117,325 empty transactions.
- Registered SHA-256:
  `de0f94f545ebae18033195524984fc842d3359154b864cb52bef2372a877dcf1`.
- Authoritative input record:
  [primary ARFF manifest](../artifacts/manifests/2025Q4-statins-mining/arff_manifest.json).

No extra FDA quarter, non-statin co-drug attributes, classifier, new reaction
vocabulary, or change to the primary PS experiment or PS+SS sensitivity belongs
to this milestone. Multi-item rules use only attributes already in this ARFF.
All interpretation remains non-causal.

Before any new mining invocation, create and lock a **separate** extension
configuration and decision record. Record its commit/hash, verified input hash,
WEKA 3.8.6 jar/runtime hashes, exact options and resolved defaults, binary presence
semantics, support schedule and integer cutoff policy, rule-length/direction
policies, metric thresholds/pool definition, rule cap, heap, processors, timeout,
timing boundary and failure/stop rules. Verify option semantics with the pinned
3.8.6 implementation/help and a small semantic fixture before the full-data run.
No full-data mining begins while any applicable setting is unspecified.

The support ladder, lift floor, resource bounds, cap and ranking policies below
are registered planning choices now. Exact associator options and the later
metric/FPGrowth equivalence decisions remain pre-execution gates, not claims
that those checks have already been performed. Lock each later phase's remaining
settings before executing that phase; do not choose them from desirable results.
Any necessary change requires a separately documented plan amendment before a
new run, preserving the original plan and failed evidence.

Keep new configuration, outputs, failures and evidence in separate showcase
paths. Never overwrite or re-export Milestone 3/4 snapshots. No new result can
replace a core result or change its validation status.

### 2. Full-ARFF WEKA Apriori feasibility study

Status: **Step 2A complete; Step 2B 0.001 timed out; ladder descent stopped.** Implementation
commit `11d81fa` validates the separate runner/configuration on the small fixture.
The [verified semantics](../showcase/SEMANTICS.md) and
[locked execution manifest](../artifacts/manifests/weka-showcase-step2a/locked/execution_manifest.json)
record the exact prerequisites, runtime applicability and implementation caveats.
No registered support/metric/resource choice was substituted. The user separately
authorized exactly the first 0.001 full-data invocation; its
[preserved timeout evidence](weka_showcase_step2b.md) supplies the current decision
gate. Do not retry, descend to 0.0005 or begin later showcase work under this plan.

Run actual WEKA 3.8.6 Apriori on all 366 attributes together, without per-reaction
projection. Retain general association rules; do not impose the primary
one-drug antecedent / one-reaction consequent restriction. Keep all presence-only
directions and multi-item antecedents/consequents available. Register any
associator-imposed length limits explicitly rather than silently imposing one.

Execute the registered minimum-support ladder serially, in this order:

1. `0.001`
2. `0.0005`
3. `0.0002`
4. `0.0001`

Initial ranking metric: **lift**, with floor **1.2**. Preserve the existing
**4 GB Java heap** and **30-minute wall-clock limit per full-data invocation**;
use two active processors and one JVM at a time. Record both whole-process time
(including load/export) and association-build time when available. Use a fixed
support run at each ladder value, not a rule-count-driven support descent.
Verify WEKA's upper/lower-support and cycle semantics before registering exact
flags; retain reported integer minimum counts and actual cycle/support output.

Register a **100,000-rule output cap**. Record the requested cap, returned count,
and any internal cap/early-stop behavior. Treat reaching the cap as possible
truncation, not a complete rule universe. Preserve that run and stop the ladder
at a cap hit until a separately registered decision; do not increase the cap
after inspecting desirable rules. A below-cap count alone is insufficient if
the associator has another restriction that limits enumeration.

**Stop descending after the first memory/resource failure or timeout.** Preserve
the failing support, command, timestamps, exit status, partial files, stdout and
stderr as feasibility evidence. Mark lower levels not attempted due to the stop
rule. Do not tune heap, timeout, support, feature set or rule restrictions around
the failed run within this registered study. Distinguish resource failure,
truncation and semantic/implementation errors; none is a successful result.

Implementation prerequisite: the existing Java bridge's `full` mode still
filters its exported rules to one drug -> one reaction. A separate showcase
runner/exporter must capture complete rule itemsets and metrics. Do not change
the frozen bridge or interpret its restricted export as general full-ARFF output.

### 3. Multi-item rule analysis

Status: not started; uses successful, clearly scoped Step 2 outputs.

Identify, count and summarize observed structures, especially:

- `{statin_A, statin_B} -> reaction`.
- `{statin, reaction_A} -> reaction_B`.
- `reaction_A -> reaction_B`.
- Other interpretable multi-item patterns, including larger consequents if present.

Retain complete antecedent/consequent itemsets, joint and side counts, support
and WEKA metrics for examples. Report structures absent from successful runs
as absent; do not manufacture examples or expand the attributes to obtain them.
Explain that the original two-by-two PRR/ROR pair table cannot express these
conditional or reaction-to-reaction structures directly. Do not apply pair-table
scores to a multi-item rule as though it were the same estimand.

There are no non-statin co-drug features in this input. Co-occurrence, conditioning
on reported reactions, co-suspected statins and reaction clusters do not establish
causality, chronology, interactions or clinical risk. Preserve sparse-count and
report-composition cautions for student inspection.

### 4. WEKA rule-metric comparison

Status: not started; metric semantics must be verified before execution.

Compare **confidence, lift, leverage and conviction**. Verify WEKA 3.8.6's exact
metric identifiers, threshold direction/scale, formulas, conviction convention,
zero/infinite handling, ranking behavior and defaults directly. Do not assume
the same numeric threshold is meaningful for all four metrics.

Preferred registered approach: rescore/rank the **same complete rule pool** from
each successful, untruncated Step 2 support run using all four WEKA metrics.
This pool is explicitly conditional on the Step 2 lift floor of 1.2; conclusions
compare metrics within that pool, not unrestricted global confidence/leverage/
conviction leaders. Obtain/verify all four metric values through WEKA; preserve
the original lift-ranked output. Do not silently union independently truncated
top-N lists and call that an exhaustive common pool.

If the common-pool approach cannot be implemented faithfully, stop and register
metric-specific thresholds and exact commands **before** new metric runs. No
shared `1.2` threshold across metrics and no post-result threshold optimization.

For each support pool, report top-K overlap and rank changes for all six metric
pairs, with **K = 10, 25, 50**. Use descending average ranks for ties; fixed-size
top-K ties break by canonical antecedent then consequent itemset. Record boundary
ties and effective K. Use a declared common finite-score intersection for
numerical comparisons; separately retain nonfinite/undefined values and counts,
especially conviction. Never silently discard these rules or imply identical
comparison denominators when pools differ.

### 5. Apriori vs WEKA FPGrowth

Status: not started; exact algorithm conditions must be registered first.

Use WEKA 3.8.6 FPGrowth on the **same full ARFF**, initially at Step 2's successful,
untruncated support levels, in the same descending-support order. Do not descend
past the Apriori resource-stop boundary under this plan. Stop FPGrowth's descent
on its first resource/time failure and retain the failed evidence as well.

Verify FPGrowth's own option semantics directly; do not reuse Apriori flags by
name or assume identical support/rule-generation schedules. Pre-register its
fixed-support behavior, metric selection and threshold, rule cap, length and
direction constraints, heap, processors and timeout. Match the lift floor 1.2,
100,000-rule cap, 4 GB heap and 30-minute bound as far as the associator permits.
Record every remaining difference, including integer support rounding and any
unsupported rule structures, before claiming comparability.

For sparse `{0,1}` input, the positive item is the **declared nominal value `1`**
(the second nominal value), not implicit sparse `0`. Distinguish the zero-based
API nominal index from any one-based CLI value index. Verify the pinned
FPGrowth binary positive-value option/default and its sparse-instance behavior
on a fixture with both values and empty baskets; record the exact resolved
setting. Do not assume Apriori's zero-as-missing flag applies to FPGrowth.

Where both algorithms complete, compare runtime, qualifying rule counts and
overlap/agreement of canonical comparable rules. Record frequent-pattern counts
separately when available; patterns and rules are different counting units.
Use identical timing boundaries and report raw times. Resource measurements
(such as process peak memory) are optional only if measured reliably with the
same method; otherwise mark them unavailable and report failures/limits without
inventing measurements.

Check actual rule-cap hits for both algorithms. Compare complete rules only on
a verified common definition of support, presence, itemsets, direction, length
and metric threshold. If WEKA's associators cannot emit equivalent rule families,
report the limitation and restrict any agreement statistic to an explicit common
family; do not claim algorithmic disagreement from unmatched definitions,
truncation, timeouts or threshold differences.

### 6. WEKA Explorer GUI demo

Status: not started; GUI output is a demonstration aid.

Attempt to load the same full 366-attribute sparse ARFF in WEKA Explorer with
an explicitly configured 4 GB Java heap. Record the Java/WEKA version, launch
settings, load outcome and responsiveness. Demonstrate:

- Preprocess tab and loaded report/attribute counts.
- Attribute inspection and filtering controls.
- Associate tab and Apriori configuration.
- Resulting rules and their metrics.

Prefer the **highest numeric support that succeeded** in the registered ladder
for the stable live demo (0.001 if it succeeds). Do not choose the lowest support
to maximize spectacle. Register and record the GUI rule count/other settings
before execution, and label any display limit separately from automated results.

If the full file is impractical in Explorer, use a clearly labeled **GUI-only
subset**: the first 10,000 rows in the existing case-index order, retaining all
366 attributes and empty baskets, with no outcome-based selection. Record its
selection rule, row count, hash and full-input provenance. Do not substitute
subset outputs for full-data experiment evidence or compare their rule counts
as though the populations were equal. If no full-data run succeeded, say so.

Capture screenshots and factual demo notes for the student's presentation
preparation: input counts, Preprocess, controls, Associate/settings, results and
any fallback. Student slide text and narration remain student-authored.

### 7. Final showcase summary

Status: not started; write only after the preceding work is complete or its
registered failures/limitations are resolved and documented.

Produce a factual engineering summary containing:

- What was added and where separate showcase evidence lives.
- Which support levels completed, failed, truncated or were not attempted, and why.
- Observed multi-item rule types and count-supported examples.
- Ranking changes and top-K overlap across WEKA metrics, with pool boundaries.
- Apriori/FPGrowth runtime and comparable-rule agreement, including limitations.
- Whether the full ARFF worked in Explorer and any documented GUI-only fallback.
- A recommended **2-3 minute** WEKA demo flow grounded in the captured screens.
- Remaining manual student interpretation and the unchanged non-causal boundary.

Do not rewrite the primary/sensitivity findings using showcase outputs. Preserve
all Milestone 3/4 evidence and validation fields. Commit/push the final factual
checkpoint and stop; this extension does not authorize further scope expansion.

## Post-timeout amendment: one FPGrowth attempt and bounded contingency

Registered before any FPGrowth full-data result. Apriori timed out at the highest
registered support (0.001), leaving no successful Apriori full-data support level
for the planned algorithm comparison. Exactly **one FPGrowth full-data feasibility
run at 0.001** is authorized on the same frozen primary PS input and resource
envelope. Verify pinned 3.8.6 semantics and fixtures, lock a separate manifest,
commit/push it, then execute that one run. Do not retry Apriori, descend either
original ladder, run metrics/Explorer, or alter any core artifact.

Retain 4 GiB heap, 1,800-second JVM wall limit, one JVM, lift >= 1.2 and presence
semantics. Verify FPGrowth's own support rounding, -S/-N/-U/-D interactions,
positive value handling, length/direction family, completeness and processors.
Choose fixed-support/cap mode from implementation and fixtures before the result;
stop on semantic incompatibility rather than silently substitute. Record any
Apriori/FPGrowth integer-count difference before execution. Do not infer rule
overlap or a runtime ratio from Apriori's timeout. Any completion comparison is
specific to this dataset/configuration/resource envelope, without a causal claim
about why either algorithm completed or failed.

If FPGrowth also fails to return an interpretable complete result, the original
unrestricted full-data feasibility study ends. Preserve its evidence and stop.
No improvised configuration follows. The bounded tool-study below then becomes
eligible, with a **new explicit user authorization** required to execute it.

### Fallback A: separately authorized higher-support paired comparison

Eligible after **either** FPGrowth 0.001 outcome: success permits a comparable-output
point; failure permits a bounded feasibility comparison. Eligibility never means
automatic execution. Preserve all original failed evidence and configurations.

Lock the corrected sequence now: **0.004, 0.003, 0.002**. The proposed 0.01 and
0.005 levels are excluded before results because neither retains a statin item.
The [marginal-only eligibility audit](../artifacts/manifests/weka-showcase-amendment/statin_eligibility.json)
scans the hash-pinned PS ARFF without mining association rules:

- Atorvastatin 1,157; rosuvastatin 864; simvastatin 188; pravastatin 67;
  pitavastatin 16; fluvastatin 6; lovastatin 0 presence reports.
- 0.004: Apriori count 1,541 / FPGrowth ceil count 1,542; no statin survives.
  This rung is a reaction-only tractability/comparison baseline.
- 0.003: both counts 1,156; only atorvastatin survives.
- 0.002: both counts 771; atorvastatin and rosuvastatin survive.

FPGrowth ceil counts were subsequently confirmed against the pinned implementation
before its execution lock. Item eligibility does not promise any statin rule.
This ladder is based solely on existing singleton counts, never discovered rules.

For each algorithm start at 0.004 and descend only after a successful complete,
below-cap result. Stop that algorithm at its first timeout/resource failure or
unresolved truncation. Keep the same input, 4 GiB/1,800 seconds, one JVM, lift
floor, presence semantics, 100,000-rule stop policy and non-causal boundary.
Use separate milestone/config/output paths. Compare overlap and runtime only
where both complete under verified equivalent definitions; disclose the 0.004
integer-count mismatch, or preregister an equivalent-count comparison separately.

### Fallback B: separately authorized deterministic scaling diagnostics

Eligible only if both original full-data algorithms fail; no diagnostic runs are
authorized now. These are tool studies, never replacements for scientific/core
results. Retain the same association settings at support 0.001 across sizes and
algorithms, subject to the pre-run verified semantics/completeness policy. Use
the same 4 GiB/1,800-second/one-JVM bounds and stop an algorithm's increasing-size
sequence on its first failure or truncation ambiguity.

Row design: exact nested 10,000, 50,000 and 100,000 reports, all 366 attributes.
Rank the frozen primary case-index `primary_id` report identifiers by SHA-256 of UTF-8
`FAERSight-WEKA-scaling-v1|` followed by the exact `primary_id` string; break hash ties
lexically by report ID. Take the first N then emit in original case-index order.
Retain empty baskets naturally; do not select by reactions, exposure or rule
content. Freeze selected-ID/input hashes before mining; publish aggregate hashes
rather than report identifiers. Verify one-to-one mapping to the primary ARFF.

Attribute design: separately eligible for an additional dimensionality check
after the row sequence is recorded and reviewed. Use the fixed 10,000-report
subset above at every size, retaining all its rows (including newly empty rows).
Use exactly 50, 100, 200 and 366 attributes: all seven statins first in frozen
order, then reactions by descending singleton frequency in the **full frozen PS
population**, lexical attribute-name tie break. Freeze frequencies, attribute
lists/order and hashes before any diagnostic mining. Do not use discovered rules
or attractiveness to choose features or rows. No non-statin co-drugs are added.

Report observed transaction-count and dimensionality scaling only. Neither
diagnostic proves the precise internal cause of the Apriori timeout. No later
support, metric, fallback, GUI or clinical interpretation follows automatically.
