# Engineering decisions and pending experiment choices

Private technical notes; not course-submission prose. Baseline: October 18, 2026.

## Implemented for the synthetic milestone

- Python package and CLI; uv dependency lock; DuckDB presence-item mart.
- WEKA 3.8.6, lift ranking (`-T 1`), `{0,1}` nominal order and `-Z`.
- Synthetic primary role policy: PS; PS+SS available in transaction-building tests.
- Latest case selection: numeric maximum caseversion, then numeric primaryid,
  then quarter, with conflicting same-report case/version metadata rejected.
- Apply latest-version selection before eligibility. Require at least one DRUG
  and one REAC record on the latest report; do not fall back to an older version.
- Preserve all eligible background cases, even when no target drug or candidate
  reaction survives. Deduplicate normalized drugs and reactions per case.
- Candidate reaction floor counts distinct target-exposed cases. Synthetic floor
  is 2; real-data floor remains pending.
- Only reviewed exact aliases map drugs. Audit all unknown eligible-role names;
  these include background products and are not automatically target-class gaps.
- No continuity correction: retain original counts, emit `nan`/`inf` in CSV and
  explicit score flags. JSON manifests contain no non-finite statistics.
- The initial parser fails on malformed rows instead of silently dropping them;
  real-quarter source README must establish the actual encoding and schema.

## Frozen real-data integration

Statins and 2025 Q4 are verified and frozen in `config/experiment.yaml` and
`config/therapeutic_class.yaml`. The official source has been downloaded,
checksum-pinned and integrated into the full DuckDB mart with its complete
eligible report population. Source documentation and the FDA deleted-case list
are retained. Real-data role policy, reaction floor and later mining grid are
frozen. See [the Milestone 2 decision and evidence](milestone2.md) for exact
policies, counts, hashes, reproduction and outstanding quality gates.

## Pending before real-data mining and interpretation

- Student manually audits the retained source sample; automated independent
  membership checks are complete.
- Review unmapped target-like C/SS names before a role sensitivity experiment.
  Unknown spellings remain unmapped; the frozen alias map is not changed silently.
- Freeze 5–10 externally supported positive benchmark pairs before final mining.
- Export and validate the real sparse ARFF over the same full case universe.
- Run actual WEKA Apriori with the prespecified grid and record any resource-driven
  change as a new decision before interpreting results.
- Complete benchmark recovery, ranking agreement, role/threshold sensitivity and
  student interpretation before treating reporting signals as validated findings.

## Course items owned by the student

- Confirm Canvas deadlines; PRD planning target for Milestone 2 is October 20,
  2026, with conflicting dates in supplied materials still unresolved.
- Verify permitted AI-assisted code use/disclosure with course guidance.
- Author all submitted literature/progress/final reports, slide prose and narration.

No PRD course-complete or real-data acceptance boxes are checked by this milestone.

## October 22 role-sensitivity decision

The historical pending items above are superseded by Milestone 3 mining evidence
and the separate [Milestone 4 record](milestone4.md). The new run stays within
2025 Q4 and preserves the frozen primary population, vocabulary, support grid,
lift floor, alias map and benchmark. One independently supported exact SS
ingredient-token overlay resolves both rosuvastatin-zinc candidate rows, without
changing PS or C mappings. The broader SS reaction vocabulary is listed but not
searched. Benchmark ranks use declared finite pools and average ties. Screening
uses uncorrected raw cells for log-Wald ROR intervals and an explicitly
Yates-corrected PRR convention; none constitutes clinical validation.

Student source/alias/label review and interpretation remain pending in the
unsigned packet. Stop before the optional WEKA showcase extension; no new
quarter, discovery vocabulary, reference pairs or ranking thresholds are added.

## October 22 post-core WEKA showcase plan

Add a separate **WEKA Showcase / Tool-Study Extension**, after the frozen
2025 Q4 scientific core, for course alignment and demonstration of WEKA itself.
The ordered plan and pre-execution gates are in the [roadmap](roadmap.md):

1. Freeze/document the extension plan.
2. Study actual full-ARFF WEKA Apriori feasibility at supports 0.001, 0.0005,
   0.0002 and 0.0001, initially lift >= 1.2, with the existing 4 GB / 30-minute
   bounds and an explicitly checked 100,000-rule cap. Stop descending on the
   first resource/time failure; preserve all failures and truncation evidence.
3. Analyze general multi-item and reaction-to-reaction rules separately from
   the scientific pair table, with non-causal interpretation.
4. Compare confidence, lift, leverage and conviction rankings after verifying
   exact WEKA 3.8.6 semantics and registering a common pool or distinct thresholds.
5. Compare actual WEKA Apriori and FPGrowth only under verified comparable
   conditions, including sparse binary positive-value handling.
6. Attempt a full-ARFF Explorer demo and capture factual screenshots/notes;
   document any GUI-only subset explicitly.
7. Summarize completed/failed supports, rule structures, metric rankings,
   algorithm runtime/agreement, Explorer feasibility and a 2-3 minute demo flow.

Use the existing primary full sparse ARFF: **385,288 reports and 366 attributes
(seven statins + 359 reactions)**. No extra FDA quarter, non-statin co-drug
feature expansion, classifier or alteration/reinterpretation of primary PS or
completed PS+SS work is part of this milestone. Preserve existing artifacts,
hashes, manifests and `scientific_findings_validated: false` boundaries.

**Only Step 1 documentation is authorized now. Stop after committing/pushing
this plan; do not begin Step 2 until the user explicitly says to continue.**
All applicable settings must be pre-registered in a separate extension record
before any new mining run. No extension run or GUI attempt has been performed.

## October 22 Step 2A prerequisite checkpoint

The user subsequently authorized **Step 2A only**: inspect the exact pinned
WEKA 3.8.6/JDK semantics, validate a separate unrestricted exporter with a small
fixture, and lock the execution configuration. Implementation commit `11d81fa`
contains that code, configuration, fixture/tests and raw inspection evidence.
The [locked execution manifest](../artifacts/manifests/weka-showcase-step2a/locked/execution_manifest.json)
references that exact code commit. [Verified semantics](../showcase/SEMANTICS.md)
document fixed support, cap ambiguity, JVM-versus-Apriori processor applicability,
the conviction convention and the long-itemset implementation caveat.

Step 2 prerequisites are **locked and validated**: all 113 local tests pass
with actual WEKA enabled, including all 100 existing tests. The committed-code
fixture recovers every planned rule form and its complete 50-rule qualifying
pool, with independent counts/four-metric checks and identical repeated exports.
All 108 tracked frozen core files match roadmap commit `69d27d7` byte for byte.

The existing full primary ARFF has been hash-verified only. **No full-data
showcase mining has begun**, no Step 3-7 work or GUI attempt has run, and no
primary/sensitivity artifact, configuration, manifest or validation flag changes.
Stop after this checkpoint's commit/push. The first full-data support 0.001
invocation requires a new explicit user authorization; the registered ladder,
lift threshold, resource limits and non-causal boundaries remain unchanged.

## October 22 Step 2B support 0.001 attempt

The user subsequently authorized exactly one registered full-data Apriori
invocation at support 0.001, using the Step 2A lock without modifications.
The JVM timed out at 1,800 seconds; total command wall time was 1,804.68 seconds,
and the runner exited 1. No completed rule export or association-build timing
was returned. Cap status, long-itemset caveat status, side lengths, structural
counts and representative rules are unavailable rather than zero. Mechanical
rule analysis was skipped because the successful-below-cap condition was unmet.

The [Step 2B record](weka_showcase_step2b.md) and separate tracked evidence under
`artifacts/manifests/weka-showcase-step2b-0.001/` preserve the exact invocation,
options, versions, failure logs and all emitted raw-file hashes. All 108 frozen
core files and the Step 2A source/configuration remain unchanged. No retry,
lower support, resource tuning, metric comparison, FPGrowth or Explorer work ran.

The first resource/time failure stops the registered ladder. **Do not proceed
to 0.0005; stop after recording/committing/pushing this checkpoint.** Any retry
or changed execution requires separate review and plan amendment. This tool
feasibility outcome does not replace or reinterpret Milestone 3/4 findings or
alter their `scientific_findings_validated` boundaries.

## Post-timeout FPGrowth amendment and preregistered contingency

Apriori evidence is committed at `6afd22d`: one 0.001 attempt exceeded the
registered 4 GiB / 1,800-second budget, no model returned. This establishes a
feasibility outcome, not its internal cause (memory, candidate generation and
itemset width are unproven explanations). All rule statistics/build time are
unavailable. No retry or lower-support descent is authorized.

Before any FPGrowth full-data result, authorize exactly one full-ARFF FPGrowth
0.001 run after pinned implementation/fixture verification and a separate locked
manifest. Preserve the original plan/history. The appended
[roadmap amendment](roadmap.md#post-timeout-amendment-one-fpgrowth-attempt-and-bounded-contingency)
is the controlling new authorization; the original Apriori stop rule stays in
force. Resolve cap/completeness and any integer-count difference before execution.

Preregister Fallback A **0.004 -> 0.003 -> 0.002** now, replacing the unexecuted
proposal 0.01 -> 0.005 -> 0.002 in the attached request as explicitly corrected
by the user. Frozen marginal audit confirms no statins at 0.004, atorvastatin only
at 0.003, atorvastatin plus rosuvastatin at 0.002; eligibility is not rule recovery.
The ladder is fixed before rule results. Fallback A becomes eligible after either
FPGrowth success or failure, providing a paired-completion opportunity even if
FPGrowth 0.001 succeeds; **separate explicit authorization remains required**.

If both algorithms fail, end the original full-data feasibility study; bounded
Fallbacks A/B become eligible without automatic execution. Fallback B's exact
row hash/seed, nested sizes, constant row population and support-frequency/lexical
attribute ordering are preregistered in the roadmap and independent of rules.
Scaling does not prove an internal failure mechanism. All configs/evidence remain
separate from Milestone 3/4 and from the locked Apriori source/configuration.

### FPGrowth semantic gate resolved before execution

Pinned implementation and fixture inspection confirms `-S` fixes support and
returns all internal qualifying rules, ignoring `-N` clipping. Without `-S`,
`-U 1 -D 1` takes two passes (starts at 1, then clamps to the lower bound), not
one; U filters maximum joint rule support. Select **Mode 1 / -S** before results.
Use internal/API count equality plus normal build/complete export as the reliable
completeness signal. Retain N=100000 as a requested value and post-completion
stop threshold, explicitly not an enforceable generation/export cap in this mode.
Heap/time are the resource bounds. At or above that threshold preserve and stop.

FPGrowth's `ceil(.001*385288)` gives **386**, versus Apriori's **385**. This
pre-run difference limits equivalence; no support adjustment is authorized.
Explicit P=2 is required for correct sparse presence labels. I=-1 retains general
rule partitions including multi-item consequents. See
[verified implementation/fixture semantics](../showcase_fpgrowth/SEMANTICS.md).
Exactly one locked full-data attempt follows; fallback eligibility is distinct
from authorization to execute either fallback.

### Completed single FPGrowth 0.001 checkpoint

Execution lock committed/pushed at `f87b53f`, implementation `d425714`, before the
single invocation. CLI/JVM exited 0; total CLI wall 5.8495633 s, JVM wall
1.1863082 s, association-build 0.6003145 s. Normal return and complete export
contain 4,884 internal/API rules, one observed tree-build pass, 1,736 frequent
itemsets, no non-presence items and no policy-limit hit. Cutoff remains 386
versus Apriori 385. All rules are reaction-only; multi-item consequents number
1,475. Maximum side sizes 3/3 and maximum total 4. Eight deterministic examples
reconcile independently against the unchanged primary mart. No clinical meaning
or internal cause of Apriori's failure is inferred.

See the [complete factual record](weka_showcase_fpgrowth.md) and aggregate/raw
snapshot under `artifacts/manifests/weka-showcase-fpgrowth/run-0.001/` for counts,
options, versions, logs, timing boundaries, hashes and the comparison limitation.
Apriori returned no model, so overlap and a completed-runtime ratio are undefined.

Post-run: all 127 tests pass (14 new, 113 existing), no skips; lint/format pass.
All 108 scientific-core files and all 151 prior showcase/manifest files retain
their committed bytes. Existing Milestone 4 source/input/mart/overlay hash checks
pass. Scientific validation fields remain false. **Fallback A is eligible but
not authorized to run; Fallback B is not eligible. Stop after commit/push.**
No retry, lower support, higher-support pair, scaling, metric comparison or
Explorer was executed. The 0.004 -> 0.003 -> 0.002 ladder stays preregistered.

## Fallback A1 authorization: 0.004 paired-completion checkpoint

The user now authorizes only Fallback A1 at 0.004: Apriori first, FPGrowth only
after complete below-cap Apriori output. Preserve all previous evidence and
settings. Exact cutoffs are Apriori 1,541 and FPGrowth 1,542. Preregister raw-set
statistics with that limitation plus common-support comparison at joint >=1,542
using complete canonical finite-metric outputs, tolerance 1e-12. No support
adjustment, extra mining or speed ratio is registered. See the separate
[A1 preregistration and outcome record](weka_showcase_fallback_a1.md).

The purpose is a tractable algorithm comparison, not statin rule recovery.
Increasing support cannot introduce statin-containing rules absent from the
complete 0.001 FPGrowth pool with other settings fixed. At 0.004, no statin
singleton survives either cutoff (largest primary count 1,157). No clinical
interpretation or diagnosis of the earlier timeout's internal cause follows.
Lock a separate manifest before execution; stop after A1 validation/commit/push.
0.003, 0.002 and all other extension steps require new explicit authorization.
