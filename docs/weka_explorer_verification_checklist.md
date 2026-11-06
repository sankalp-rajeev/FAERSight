# WEKA Explorer verification checklist

**Complete by manual verification: November 6, 2026.** The student supplied the
observations below and three screenshots. This checklist records GUI evidence;
scientific interpretation and course submissions remain separate student work.

## Verified observations

- [x] Full ARFF loaded successfully: **385,288 instances / 366 attributes**.
  [Preprocess screenshot](../images/FAERSight-dataset.png) shows relation
  `faersight`, filter `None`, and `DRUG_atorvastatin` with **1,157 present**,
  **384,131 absent**, and zero missing values.
- [x] Projected ARFF retained **385,288 instances / 8 attributes**: all seven
  statins and MYOPATHY, including the all-zero lovastatin column.
  [Projected Apriori screenshot](../images/results.png) lists those dimensions
  and all eight attribute names.
- [x] Projected Apriori used the frozen options:
  `-N 10000 -T 1 -C 1.2 -D 1.0 -U 1.0 -M 1.0E-5 -S -1.0 -Z -c -1`.
  The same screenshot shows **four general rules**, one cycle, minimum support
  **0 (4 instances)**, lift floor **1.2**, and **L(1)=7 / L(2)=2**.
- [x] `atorvastatin -> MYOPATHY` matches the frozen result at displayed precision:
  antecedent **1,157**, joint **19**, confidence approximately **0.02**, lift
  **37.66**. The reverse rule and both rosuvastatin/MYOPATHY directions also match.
  The scientific export retains only the two statin-to-reaction directions.
- [x] Full-data FPGrowth at support **0.004** reported **70 rules** using
  `-P 2 -I -1 -N 100000 -T 1 -C 1.2 -U 1.0 -M 0.004 -D 1.0 -S`.
  [FPGrowth screenshot](../images/FPGrowth.png) shows **385,288 instances / 366
  attributes**, the command, total rule count and leading rules. The student
  reported a match to the frozen result; visible leading rules and total agree.
- [x] Full-data and all-row projected demonstrations succeeded without a 10,000-row
  fallback. No new scientific threshold search was performed for this update.

## Evidence limits

- Load time, navigation latency, peak memory and GUI association-build times were
  not measured or supplied. Screenshot clock labels are not elapsed durations.
- Live Java/WEKA versions, JVM launch flags and actual heap were not captured.
  The unchanged reproduction specification is **WEKA 3.8.6**, OpenJDK
  **21.0.10+-14961533-b1163.108**, **4 GiB** intended heap, and two active
  processors. Historical version/hash evidence is preserved in the
  [Explorer record](weka_explorer_demo.md#prepared-inputs-runtime-and-expected-scientific-result).
- Property dialogs and a complete full-precision GUI rule export were not
  supplied. The screenshot supports displayed options, total count and visible
  rules; exact whole-set agreement remains grounded in frozen scripted evidence.
- Exact scientific values remain confidence **0.016421780466724288**, lift
  **37.66139852656707**, support **19/385288**, and joint count **19** for the
  selected atorvastatin/MYOPATHY pair. Rounded GUI text does not replace them.
- Scientific findings remain `scientific_findings_validated: false`. Source-case,
  alias, benchmark and interpretation reviews are not signed off by this checklist.

## Reproduction and integrity

The [dated manual verification manifest](../artifacts/manifests/weka-explorer-verification-20261106/manual_verification.json)
records screenshot SHA-256 values, supplied observations, frozen references and
unmeasured fields. The companion validation record and test XML capture the
current checks. Historical preparation manifests remain unchanged and describe
their earlier automated connection failure.

Run the existing checks from the project root, with `WEKA_JAR` set to
`.tools/weka/weka-stable-3.8.6.jar`:

```powershell
.venv/Scripts/python -m pytest -q
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check src tests tools scripts
.venv/Scripts/python scripts/verify_explorer_preparation.py
```

The preparation auditor intentionally verifies the historical checkpoint; its
`GUI_verified: false` field refers to that old record. The dated manual manifest
and this checklist provide the subsequent completion evidence without rewriting
the locked scientific artifacts. Final packaging is the next separate step.
