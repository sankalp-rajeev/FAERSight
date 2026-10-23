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

### Completed Fallback A1 at 0.004

Pre-run lock `2504de6` references implementation/preregistration `b5b151f`.
Apriori completed first (JVM wall 394.350229 s; build 393.9657375 s), then
FPGrowth completed (JVM wall 0.735651 s; build 0.32545 s). Both exited 0,
returned 70 complete rules and 154 frequent itemsets, and passed their unchanged
cap/completeness checks. The exact native cutoffs remain 1,541 and 1,542.

Raw canonical intersection is 70, each algorithm-only count 0, Jaccard 1.0.
The preregistered common joint-count >=1,542 comparison excludes no rules and
has the same overlap. All shared metrics agree exactly (maximum absolute
difference 0), within 1e-12; all rule counts independently match the frozen ARFF.
No speed ratio, metric-ranking experiment, clinical interpretation or diagnosis
of the 0.001 timeout's internal cause is claimed.

Both outputs: 64 single reaction -> single reaction; 3 multi-reaction antecedent
-> reaction; 3 reaction -> multi-reaction consequent; zero total size >=4;
maximum side/total sizes 2/2/3. All 70 are reaction-only, as expected from
pre-run statin singleton counts and monotonic support. No statin-rule recovery
is an objective of this fallback.

See [A1 evidence and hashes](weka_showcase_fallback_a1.md). Post-run: all 137
tests pass (10 new, 127 retained), zero skips; lint/format pass. All 251 protected
prior files, 108 frozen core files, 1,096 primary generated artifacts and 1,106
sensitivity generated artifacts retain their hashes. The 0.001 records and all
scientific validation boundaries are unchanged. **0.003 is eligible, awaiting
new explicit authorization. Stop after commit/push; no later run was executed.**

## Fallback A2 authorization: 0.003 only

The user now authorizes A2 after frozen A1 `b5daa01`. Use a separate committed
execution manifest and hash before either run; Apriori first, FPGrowth only
after complete eligible Apriori output. Preserve all old sources, configs and
evidence, resource limits, cap/completeness policies and A1 timing boundaries.
Verified Apriori/FPGrowth cutoffs both equal **1,156**. Only atorvastatin (1,157)
is singleton-eligible; record all seven primary statin counts per algorithm.

Clarify the purpose: singleton eligibility does not override monotonic rule
support. Higher support cannot introduce qualifying statin rules absent from
the complete 0.001 FPGrowth pool when other definitions are fixed. Count A2's
actual statin-rule output nonetheless, preserve every rule and direction with
algorithm provenance, and use metric-independent canonical deterministic export
and up to eight representatives. No clinical interpretation or reinterpretation
of frozen primary/sensitivity findings. See [A2 preregistration](weka_showcase_fallback_a2.md).

Run full tests/lint/frozen-history hash checks, commit/push and stop. No 0.002,
metric-ranking, Explorer, scaling or additional algorithm is authorized.

### Completed Fallback A2 at 0.003

Implementation/preregistration `4741fbc`; separate lock `a41bb28` and manifest
SHA-256 `752db0a8fa8197a7b764b4c4843ed320af9b013ed655298d804cce2162f38fd3`
preceded both invocations. Both verified native cutoffs are 1,156; the frozen
input scan confirms only atorvastatin (1,157) is singleton-eligible under each.
Apriori completed first: JVM wall 360.891450 s, build 360.5035305 s. Then
FPGrowth completed: JVM wall 0.750769 s, build 0.3391509 s. Both exited 0,
returned 194 complete rules and 241 frequent itemsets, with unchanged
cap/completeness policies passed and no >=31 Apriori caveat.

Native canonical intersection 194, algorithm-only counts 0/0, Jaccard 1.0.
All shared metrics agree exactly (maximum difference 0), within 1e-12;
every raw count independently reconciles against the frozen ARFF. No common-
count adjustment is required because both native thresholds equal 1,156.
Record raw times with A1's timing boundaries; no extrapolation or ratio here.

Observed statin-containing rules: **0 for each algorithm**, with zero in all
seven statin categories and complete explicit empty CSV/JSON exports; no
representatives are fabricated. Atorvastatin singleton eligibility does not
imply a qualifying co-occurrence rule or override monotonic support. Both
outputs contain 176 reaction->reaction rules, 9 multi-reaction->reaction and
9 reaction->multi-reaction; none has total size >=4. Maximum side/total sizes
2/2/3; each side-size histogram is 185 single-item and 9 two-item sides.
All interpretation remains factual and non-causal.

See [A2 outcome and hashes](weka_showcase_fallback_a2.md). Post-run: all 145
tests pass (8 new, 137 retained), zero skips; lint/format pass. All 270 protected
earlier files, 108 frozen core files, 1,096 primary generated artifacts and
1,106 sensitivity generated artifacts retain their hashes. Earlier 0.001/A1
evidence and all scientific validation boundaries remain unchanged. **0.002 is
eligible, awaiting new explicit authorization. Stop after commit/push.** No
later support, metric-ranking, Explorer, scaling or additional algorithm ran.

## Final Fallback A authorization: A3 at 0.002 only

After frozen A2 `a1113d0`, authorize the last registered level, 0.002. Create
and hash a separate manifest before either run. Apriori first; if it fails or
is incomplete/ambiguous, retain evidence, skip FPGrowth and terminate Fallback A.
Otherwise run the fixed preregistered FPGrowth configuration. No configuration
or earlier evidence changes. Both exact native minimum counts resolve to 771.
Atorvastatin 1,157 and rosuvastatin 864 are singleton-eligible under each; the
other five statins are not. Verify the frozen input marginals before locking.

Preserve all statin rules and directions, or explicit empty exports; multiple
reaction->statin includes two or more reactions. Singleton eligibility is not
rule recovery; count the actual output without clinical interpretation. Retain
native/common-count canonical agreement, all independent count/metric checks
and the same A1/A2 timing boundaries. The
[A3 preregistration](weka_showcase_fallback_a3.md) fixes the scope and commands.

Add a read-only CSV/JSON progression over A1/A2/A3 with source hashes, exact
cutoffs, counts, eligibility, maxima, raw times and Jaccard. Do not extrapolate
or assume monotonic runtime; Apriori A2 was measured below A1. Conclusions stay
specific to this dataset, WEKA version, configuration and resource envelope.
Validate, commit/push and stop: no support level follows A3 and no metric-ranking,
Explorer, scaling or new algorithm is authorized.

## Final Fallback A3 result and terminal gate

A3 was locked before execution: implementation/preregistration `602c1ab`,
manifest commit `adb5f35`, manifest SHA-256
`589c32b4aaa0299ac24fe1a1ebae727f87ff2a81f4804d5b7b9377895f035132`.
Both native minimum counts are 771. Atorvastatin 1,157 and rosuvastatin 864 are
singleton-eligible; the remaining five are not. Apriori completed first, then
FPGrowth; each returned 586 rules and 447 frequent itemsets. Both cap/completeness
gates passed; maximum frequent-itemset/rule total size is 3, side maxima 2/2.
No >=31-itemset caveat was encountered.

Canonical native and common-count comparisons both give intersection 586,
Apriori-only 0, FPGrowth-only 0 and Jaccard 1.0. All five metric differences are
exactly zero (tolerance 1e-12); every rule's counts/metrics reconcile independently
against the frozen ARFF. Every statin-containing category is zero; complete empty
CSV/JSON exports are retained. Both outputs partition into 472 reaction->reaction,
57 two-reaction->reaction and 57 reaction->two-reaction rules. No clinical or
causal interpretation is implied.

Apriori build/JVM/driver seconds: 828.229460/828.657024/829.371142.
FPGrowth: 0.395028/0.831523/1.494203. A1/A2/A3 progression is recorded in
[the final engineering record](weka_showcase_fallback_a3.md) and hashed CSV/JSON.
A1's native 1541/1542 mismatch and common-count agreement remain disclosed;
A2/A3 thresholds match. These single measurements establish no monotonic runtime
law or universal performance claim. The original Apriori 0.001 timeout and
FPGrowth success remain unchanged; no internal timeout cause is established.

All 153 tests pass (8 new A3; 145 retained), zero skips; lint/format pass.
All 292 prior protected files, 108 scientific-core files, 1,096 primary generated
artifacts and 1,106 sensitivity generated artifacts retain their registered
hashes. No frozen configuration, manifest or scientific validation flag changed.
**Fallback A is complete.** Stop after commit/push. No further support level,
metric-ranking, Explorer, scaling diagnostic or additional algorithm is authorized.

## Authorized offline metric-ranking checkpoint

After frozen A3 `0c80bd1`, authorize only the [registered metric study](weka_showcase_metrics.md)
of its exact 586-rule common pool. No new mining. Use full-precision API values,
average statistical ties, lexical Top-K ties and fixed gap/chart selectors. Report
lift-range restriction and rule non-independence. The statin explanation covers
every statin-containing itemset of size >=2 via all statin-reaction/statin-statin
pair counts and support anti-monotonicity. Preserve all earlier artifacts. Commit
and push, then stop before Explorer or final packaging.

## Offline metric-ranking result and stop gate

The exact common A3 pool remains 586 rules, identical between the two miners.
API values are used at full precision; no printed/rounded model values enter
rankings. Every count/metric independently reconciles with zero difference.
Confidence/conviction has the highest Spearman (0.9648123764153352), and
confidence/lift the lowest (0.46369169898167756). The 472-rule single-to-single
analysis preserves the ordering of the six pairwise correlations. These dependent
rules and the lift >=1.2 range restriction preclude general metric or inferential
claims. Lexical tie breaks apply to exports/Top-K only; statistical ties average.

Top-K four-way intersections at 10/25/50 are 0/0/2. Lift and leverage each split
a two-rule tie 1-inside/1-outside at K=25; other inspected boundaries do not split.
Three registered example categories export three rules each; conviction relative
to confidence has no gap >=100 and stays empty. The common pool has no confidence-1
rules, infinite conviction or sentinel values. Count-only pinned WEKA API probes
verify finite conviction at confidence 1 using the +1 denominator correction.

All 2,513 statin-reaction and 21 statin-statin pairs were counted. The maximum
joint count over every statin-containing itemset of size >=2 is exactly 141,
attained by rosuvastatin/MYALGIA; all statin-statin pairs have count zero. Any
larger itemset contains one of these pairs and cannot increase its support.
**No statin-containing itemset of size 2 or more reaches the minimum:** 385/386,
771, 1156 and 1541/1542 at the showcased supports. This concerns joint support,
not a clinical absence claim. No statin-recovery extension is scheduled.

The unrestricted WEKA showcase is an algorithm and metric study on reaction co-reporting. The projected experiment is the FAERSight drug-safety analysis.

[Metric evidence](weka_showcase_metrics.md) contains complete rankings, Top-K/tie
tables, distributions, rank-gap examples, the complete statin pair table and
exactly three deterministic charts. All 171 tests pass (18 new, 153 retained),
lint/format pass; independent SciPy verifies all 12 descriptive correlations
within 1.12e-16 and exactly matches average ranks. All 336 protected prior files,
108 frozen-core files, 1,096 primary and 1,106 sensitivity generated artifacts
retain their hashes. No scientific validation flag changed; no new mining ran.

Unrestricted Apriori study, Apriori/FPGrowth comparison, Fallback A and metric
ranking are complete. Explorer is next, pending explicit authorization; final
showcase summary/demo packaging follows Explorer. Commit/push and stop here.

## Explorer demonstration preparation authorization and connection limitation

After frozen metric checkpoint `0fd1aef`, authorize only Explorer demonstration
preparation and the explicitly scoped GUI repeats. No new mining experiment.
Use the first canonical accepted frozen benchmark pair at support 0.00001:
atorvastatin/MYOPATHY, projection r0239, joint count 19. Prepare all-row sparse
projection and exact frozen settings; retain original scripted results as authority.

The computer-use native pipe is unavailable after app/window-list retries and a
session reset. Actual Explorer usability, GUI configuration/results and screenshots
remain pending. No GUI or fallback usability result can be inferred from API parsing.
Complete independent preparation/tests/hash checks and preserve this blocker in
[the Explorer record](weka_explorer_demo.md); do not mark the demonstration complete
or advance to final packaging without the required GUI observations.

## Explorer preparation result: validated material, GUI still pending

Preparation code `296b8a2` deterministically regenerates the primary r0239
projection as 385,288 rows and 8 attributes, retaining all seven statins, MYOPATHY,
original order and 382,855 empty projected rows. SHA-256
`c13b0b84f123c26d48be11b0662f96805eeaf34292c5d5b2388cea1f89c3d73b`.
Native WEKA parser/JavaBean inspection confirms binary counts and underlying
options without GUI input or any association build. It does not establish
Explorer usability, screen labels, timing or rule agreement. The full original
ARFF/hash remains unchanged; 10k fallback need is unobserved and none was generated.

Selected frozen atorvastatin/MYOPATHY counts are joint 19, antecedent 1157,
consequent 168, N=385288; confidence 0.016421780466724288 and lift
37.66139852656707. Frozen raw output has four general rules, while the scientific
CSV retains two statin->reaction rules. Presenter notes explain that expected
display/export distinction and rounding without claiming a completed GUI comparison.
Preserved A1 result logs, exact Apriori/FPGrowth bean mappings and the existing
metric matrix are referenced; no unrestricted search was repeated.

All 180 tests pass (9 new; 171 retained), lint/format and frozen/prior hash checks
pass. All 393 protected prior tracked files, 108 frozen-core files, 1,096 primary
and 1,106 sensitivity generated artifacts retain their hashes. Scientific validation
flags remain false. [Rehearsal cues](weka_explorer_demo_script.md) are preparation
support for student adaptation, not final report/slide packaging.

**Explorer remains incomplete pending the Windows GUI connection.** No screenshots
or actual GUI observations were obtainable. Resume that authorized checklist after
connection restoration; final packaging still requires completed Explorer and new
explicit authorization. Stop after committing/pushing this preparation evidence.
