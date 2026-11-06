# Reproduction and Session 2 submission readiness

Engineering checklist, November 6, 2026. This document indexes technical inputs
for student-authored work; it is not final-report prose, slide copy or narration.
See the [requirement audit](final_readiness_20261106.md) for unresolved gates.

## Verified scope and limits

- Frozen core: statins, 2025 Q4, 385,288 eligible reports, seven statins and 359
  reactions; primary PS and separate PS+SS sensitivity. WEKA 3.8.6 performs Apriori.
- The [15-case audit](case_source_evidence_review_20261106.md) was independently
  rerun: 15 PASS, zero discrepancies across 679 DRUG and 131 REAC rows. All cases
  have one DEMO row in this quarter. Within-quarter selection agrees; no older
  or newer-quarter histories were obtained. Do not describe this as a global
  longitudinal deduplication study. Synthetic tests exercise competing versions.
- The [reference review](rosuvastatin_zinc_reference_review_20261106.md) supports
  both exact SS rosuvastatin-zinc ingredient mappings. Student approval remains
  unsigned; no frozen configuration, mapping, result or scientific flag changed.
- The [Explorer checkpoint](weka_explorer_demo.md) is complete for the captured
  dimensions, settings and displayed results. Load time, latency, live versions
  and live heap were not captured. Frozen runtime hashes are reproduction
  specifications, not inferred GUI measurements.

## Safe verification workflow

Use Python 3.11+ and uv. CI uses Python 3.11 and Java 21; the frozen Windows
showcase uses OpenJDK `21.0.10+-14961533-b1163.108`. Existing snapshot directories
must never be overwritten. Keep one WEKA JVM active at a time.

```powershell
uv sync --frozen --extra dev --cache-dir .tools/uv-cache
powershell -ExecutionPolicy Bypass -File scripts/setup_weka.ps1
$env:WEKA_JAR = (Resolve-Path '.tools/weka/weka-stable-3.8.6.jar').Path
.venv/Scripts/python -m faersight.cli validate-config config/experiment.yaml --require-frozen
# Provision the pinned plotting environment before the full test suite:
# docs/plotting_runtime.md
.venv/Scripts/python -m pytest -q --basetemp=.tools/readiness-tests
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check src tests showcase showcase_fpgrowth showcase_fallback_a1 showcase_fallback_a2 showcase_fallback_a3 showcase_metrics showcase_explorer scripts
# Read-only checks of local frozen evidence; these do not start mining:
.venv/Scripts/python -m faersight.cli validate-mart data/processed/2025Q4-statins/analytical.duckdb
.venv/Scripts/python scripts/verify_explorer_preparation.py
```

The historical preparation auditor deliberately reports `GUI_verified: false`
for its original checkpoint. Current manual evidence lives in the separate
[November 6 manifest](../artifacts/manifests/weka-explorer-verification-20261106/manual_verification.json)
and three genuine screenshots. Historical documentation hashes in that evidence
index refer to commit `b4fa3c1`; compare those documentation bytes to that commit,
rather than rewriting the index when a later README changes. Scientific artifact
and screenshot hashes must continue to match their actual files.

The metric auditor additionally requires SciPy for its independent historical
cross-check and a host-compatible plotting environment to reproduce historical
chart bytes. SciPy is not a core runtime dependency or a fresh-clone prerequisite
for the 192-test suite. See [plotting runtime](plotting_runtime.md).

## Clean-environment evidence and boundaries

The current checkpoint exports tracked source at `f6816ff` into a new directory,
installs the frozen lock in a fresh Python 3.11.14 virtual environment, and tests
from that directory. No processed FDA data or scientific outputs are copied into
it. Verified WEKA/Bounce jars and the already provisioned pinned plotting runtime
are reused; the existing JDK remains host-provided. This is an isolated source
and Python-environment check on the same Windows host, not a new machine or a
new full-data reproduction. The initially offline install lacked the locked
Python-3.11 DuckDB wheel; a normal locked dependency download resolved that.
All 192 tests passed without skips in this environment. A separate synthetic
end-to-end invocation produced byte-identical ARFF, case index, count and
comparison CSV files relative to the existing local fixture outputs.

The historical [fresh-clone reproduction](../artifacts/manifests/2025Q4-statins-sensitivity/fresh_clone_reproduction.json)
records successful primary/sensitivity key-artifact and 1,077-log comparisons
on the same host using cached official inputs, including preserved failed
attempts and recovery. It is narrower than a claim that every database/environment
byte is identical on any OS. No full-data mining is repeated in this checkpoint.

The latest checked Ubuntu CI run and current local/isolated test results are
recorded in [final readiness](final_readiness_20261106.md#verification-record).
Ubuntu showcase tests tied to the original Windows runtime can skip; a green
workflow must not be reported as 192 Linux passes.

## Demonstration assets

- [Full-data Preprocess screenshot](../images/FAERSight-dataset.png): 385,288
  instances, 366 attributes; atorvastatin has 1,157 present reports.
- [Projected Apriori screenshot](../images/results.png): all 385,288 reports,
  eight attributes, exact frozen options, four general rules. Selected
  atorvastatin -> MYOPATHY joint count 19, displayed confidence 0.02, lift 37.66.
  Frozen exact confidence is `0.016421780466724288`; exact lift is
  `37.66139852656707`. Displayed support `0 (4 instances)` is rounding.
- [Full-data FPGrowth screenshot](../images/FPGrowth.png): support 0.004, 70
  rules. Complete full-precision set agreement belongs to the frozen scripted
  A1 evidence; the screenshot shows a count and visible leading rules.
- [Metric matrix](../artifacts/manifests/weka-showcase-metrics/run/charts/spearman_matrix.png)
  concerns the same 586 lift-qualified reaction-co-reporting rules. It is a
  separate tool study, not a drug-safety ranking or causal result.
- [Primary ranking comparison](../artifacts/manifests/2025Q4-statins-mining/ranking_comparison.json),
  [positive benchmark recovery](../artifacts/manifests/2025Q4-statins-mining/benchmark_recovery.csv),
  and [role comparison](../artifacts/manifests/2025Q4-statins-sensitivity/role_comparison.json)
  supply source values for the student to interpret.
- [Rehearsal cues](weka_explorer_demo_script.md) are an engineering aid. Their
  2-3 minute clock allocation is a target, not a measured complete presentation.

Do not rerun unrestricted Apriori 0.001 (preserved timeout), lower support levels,
or the frozen real-data experiments for presentation effect. Use captured results;
any future live repeat must retain its exact population and settings.

## Student's submission checks

The local course guide `docs/01_Introduction_to_Data_Mining.pdf`, visually
inspected pages 4-5, specifies a **five-page final report including everything**:
numbered Introduction, work/evaluation/discussion sections, Conclusion, and
references within the limit. Use the final report template from Canvas; that
template is not present locally and has not been validated here.

Session 2 is online asynchronous: slides accompany the final report, without
an in-person presentation requirement for Session-2-only participants. Prepare
one PowerPoint presentation file for the team. The guide requires the first
slide to identify title/team and the second to identify slide-number contributions,
including a solo author's contribution allocation. Confirm any file-format or
recording additions against Canvas; the local guide alone does not settle them.

The rendered guide displays November 19, 2026, 11:59 p.m. for final uploads and
November 17 for the in-person session. Its PDF text layer also contains superseded
December dates. The rendered page takes precedence over blind text extraction;
Canvas/instructor confirmation remains outstanding. Do not infer Session 2 must
attend the in-person date. Required filenames include a student's last name;
submit report, slides and any required programs separately, without a ZIP.

Before submission, the student must:

- Complete their own 15-case checklist, exact-alias/benchmark label review and
  selected-rule interpretation. The agent has not filled these fields.
- Confirm Canvas deadlines, final template, Session 2 file requirements and
  permitted AI-assisted code/disclosure policy.
- Write the report, slide text and any narration independently; do not paste
  these engineering notes or generated explanations into graded prose.
- Verify every claimed number against its frozen source, and distinguish
  reporting association from incidence, causality and clinical risk.
- Check the authored report is at most five pages including references, slide
  attribution is present, final files open correctly, and Canvas uploads succeed.

No graded report, slides, narration or submission receipt was generated here.
