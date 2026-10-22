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


## Completed single invocation

Launched from locked commit `f87b53f` exactly once; CLI exit 0 and JVM exit 0.
Total CLI wall time **5.8495633 s**; JVM load/build/export wall **1.1863082 s**;
runner including compilation **1.8429283 s**; association-build **0.6003145 s**.
The total CLI interval includes Python preflight as well as compilation/JVM work.
No peak-memory comparison was measured. All resource settings remained locked.

Normal build returned **4,884 internal rules and 4,884 exported rules**, with a
completion marker, no non-presence items, one observed tree-build pass and
resolved minimum count 386. The 100,000 policy threshold was not reached; N did
not truncate this -S result. There were 1,736 frequent itemsets, maximum length 4.
The CSV column named `rule_cap` records the requested N=100000 for schema
compatibility; it does not assert an enforced FPGrowth -S cap.
Maximum antecedent size 3, consequent size 3, total rule size 4. FPGrowth uses a
boolean-array partition counter; Apriori's >=31 int-partition caveat was not
encountered here and is not an implementation restriction of FPGrowth.

Mechanical categories (multi-item consequent overlaps other categories):

- Single statin -> single reaction: **0**.
- Two statins -> single reaction: **0**.
- Statin + one reaction -> single reaction: **0**.
- Single reaction -> single reaction: **2,108**.
- Multi-item consequent: **1,475**.
- Reaction-only -> reaction-only: **4,884**, the entire qualifying rule pool.

Disjoint side-length counts, antecedent -> consequent: 1->1 = 2,108;
1->2 = 1,185; 1->3 = 116; 2->1 = 1,185; 2->2 = 174; 3->1 = 116.
Singleton statin eligibility does not imply recovery of statin-containing rules.
These are aggregate reporting co-occurrences without clinical or causal claims.

### Deterministic representative multi-item rules

The pre-run selector chose the eight rows below. All items have value =1;
`REAC_` prefixes are omitted only in this readable display. Counts are
joint / antecedent / consequent; all supports use N=385,288. Displayed metrics
are rounded; complete precision, all four metrics and original WEKA ranks remain
in `mechanical_summary.json` and archived `rules.csv`. Each representative's
three raw counts was independently verified against the pinned primary mart.

- {ABDOMINAL DISCOMFORT, ABDOMINAL PAIN UPPER} -> {DIARRHOEA}: counts 410/711/14774; support 0.001064139; confidence 0.576653; lift 15.038400.
- {ABDOMINAL DISCOMFORT, ALOPECIA} -> {ARTHRALGIA}: counts 407/553/10017; support 0.001056353; confidence 0.735986; lift 28.308515.
- {ABDOMINAL DISCOMFORT, ALOPECIA} -> {ARTHROPATHY}: counts 389/553/1186; support 0.001009634; confidence 0.703436; lift 228.520552.
- {ABDOMINAL DISCOMFORT, ALOPECIA} -> {FATIGUE}: counts 415/553/15718; support 0.001077116; confidence 0.750452; lift 18.395482.
- {ABDOMINAL DISCOMFORT, ARTHRALGIA} -> {ALOPECIA}: counts 407/690/3507; support 0.001056353; confidence 0.589855; lift 64.802989.
- {ABDOMINAL DISCOMFORT, ARTHRALGIA} -> {DIARRHOEA}: counts 400/690/14774; support 0.001038184; confidence 0.579710; lift 15.118137.
- {ABDOMINAL DISCOMFORT, ARTHRALGIA} -> {FATIGUE}: counts 442/690/15718; support 0.001147194; confidence 0.640580; lift 15.702232.
- {ABDOMINAL DISCOMFORT, ARTHRALGIA} -> {PAIN}: counts 417/690/10423; support 0.001082307; confidence 0.604348; lift 22.339822.

## Comparison boundary and next gate

Under this preregistered dataset/configuration/resource envelope, FPGrowth
completed while Apriori did not. Apriori's total CLI wall was 1,804.68 s at the
1,800-second JVM timeout; its build time and returned rules remain unavailable.
Both used the same hash-pinned PS input, nominal support .001, lift >=1.2,
4 GiB/1,800-second envelope and unrestricted presence rules. Differences are
Apriori round-to-nearest count 385 versus FPGrowth ceil count 386, and Apriori's
post-generation top-N clipping versus FPGrowth -S returning all internal rules.
There is no rule overlap, completed-runtime ratio, universal performance claim,
or established internal cause of Apriori's timeout.

The preregistered **Fallback A is now eligible after success**, retaining
0.004 -> 0.003 -> 0.002. It requires separate explicit authorization before any
paired runs. Fallback B is not eligible because both original algorithms did not
fail. No retry, lower support, higher-support pair, scaling, metric comparison or
Explorer attempt ran. Stop at this checkpoint. Student interpretation remains
manual and all `scientific_findings_validated` fields remain false.

## Verification and evidence

Post-run: **127 passed**, zero failures/errors/skips, actual WEKA enabled; 14 new
FPGrowth tests and all 113 pre-existing tests retained. Ruff lint and formatting
pass (51 checked source files). All 108 frozen scientific-core files match
`69d27d7`; all 151 prior showcase/manifest files match `6afd22d`. Milestone 4
evidence index, original primary inputs/source mart, sensitivity source/input
hashes and fresh-clone overlay hashes also pass their existing checks. No core
configuration, result, manifest, artifact hash or validation boundary changed.
Direct local output checks additionally match all **1,096 primary** and **1,106
sensitivity** artifacts against their frozen manifests. `validation.json` and
`validation.txt` retain the verification counts, commands and lint output.

Raw local output: `artifacts/generated/weka-showcase-fpgrowth/full/0.001/`.
Tracked evidence: `artifacts/manifests/weka-showcase-fpgrowth/run-0.001/`.
The [evidence index](../artifacts/manifests/weka-showcase-fpgrowth/run-0.001/evidence_index.json)
hashes every snapshot file and every original emitted output. The verified ZIP
retains all raw model/rules/logs/class files; capture records include exact CLI,
JVM command, timestamps, exit codes, versions, input/runtime hashes and timings.
The [mechanical summary](../artifacts/manifests/weka-showcase-fpgrowth/run-0.001/mechanical_summary.json)
contains complete structural counts and representative raw counts/metrics.

SHA-256:

- Raw archive: `1bd9def2d1d77c5e82fdc444d59dc3146060a4fd54ec990602d47d0778dd10ab`.
- Canonical rules CSV: `746b3972949863831ca268f34ba66ff75db190e234b1a009532a6e24f0b3a5a8`.
- Evidence index: `26cdd8a1177d0649ca047b73f22f72aea595cdccbb290a69079e80c46214dce3`.
