# FAERSight

Technical implementation of [PRD.md](PRD.md): case-level FDA reporting associations,
WEKA Apriori, and independently calculated PRR/ROR.

Milestone 2 freezes **statins / 2025 Q4** and adds checksum-pinned official FDA
acquisition, streaming DEMO/DRUG/REAC ingestion, deleted-case handling,
latest-case-version selection and a complete DuckDB analytical mart. All eligible
reporting cases are retained for denominators, including reports without statin
exposure. See the [source and scope decision](docs/milestone2.md).

The synthetic end-to-end workflow also exports sparse binary ARFF and verifies
an actual WEKA Apriori rule against independently calculated PRR/ROR.
Real-data ingestion does not establish validated drug-safety findings. Real
mining, benchmark recovery and sensitivity/evaluation remain later quality gates.

Python performs preprocessing and count-based checks. **WEKA performs Apriori**.
Reporting associations do not establish causality or clinical incidence.

Executed Milestone 2 counts, checks, remaining quality gates and reproduction
hashes are recorded in [the engineering record](docs/milestone2.md#executed-integration-evidence)
and [tracked aggregate evidence](artifacts/manifests/2025Q4-statins/).

## Run on Windows (PowerShell)

From the project root, using Python 3.11+ and uv:

```powershell
uv sync --frozen --extra dev --cache-dir .tools/uv-cache
.venv/Scripts/python -m faersight.cli validate-config config/experiment.example.yaml
.venv/Scripts/python -m faersight.cli build-fixture-arff
.venv/Scripts/python -m pytest -q
```

## Acquire and integrate the frozen FDA quarter

```powershell
.venv/Scripts/python -m faersight.cli validate-config config/experiment.yaml --require-frozen
.venv/Scripts/python -m faersight.cli acquire --config config/experiment.yaml
.venv/Scripts/python -m faersight.cli ingest --config config/experiment.yaml
.venv/Scripts/python -m faersight.cli validate-mart data/processed/2025Q4-statins/analytical.duckdb
.venv/Scripts/python -m faersight.cli spotcheck data/processed/2025Q4-statins/analytical.duckdb
```

These Python CLI commands also work on Linux through `uv run --frozen faersight`.
`acquire` streams the official 67,144,585-byte ZIP, checks its frozen SHA-256,
retains download provenance and extracts only required tables, documentation and
the FDA deleted-case list. Existing downloads are checksum-verified on every reuse.
`ingest` does not download implicitly. The frozen source was verified as ASCII;
malformed rows, identity contradictions or encoding errors fail with diagnostics.

Each source relation is validated and converted one row at a time to an audited
UTF-8 staging CSV, then loaded by DuckDB's native streaming CSV reader. The
configured DuckDB budget is 4 GB / four threads, with spill files inside the run
directory. No complete source relation is loaded into a Python list or DataFrame.

Output defaults to `data/processed/2025Q4-statins/`. Validated snapshots are never
overwritten. For another reproduction run, choose a new directory with
`--output data/processed/2025Q4-statins-rerun`. Failed runs retain
`integration_failure.json` and a `.building.duckdb` diagnostic database; use a new
output directory after resolving the failure. Raw archives, staging files, and
databases stay out of Git.

The full mart contains:

- `raw_demo`, `raw_drug`, `raw_reac`: every ingested column, source row and quarter.
- `source_files`, `deleted_cases`, `latest_cases`, `case_eligibility`: provenance and selection.
- `cases`: one eligible retained report per case, independent of statin exposure.
- `case_drugs`: complete retained drug records with ingredient, role and mapping metadata.
- `case_reactions`: all nonblank normalized reaction presences per retained case.
- `case_drug_presence`: distinct reviewed statin presence under the frozen PS role definition.
- `candidate_reactions`, `case_items`: the prespecified vocabulary and separate mining items.
- `signal_counts`: integer `a,b,c,d,N` for every selected drug/reaction pair.
- `quarter_population`, `quarter_drug_role`, `quarter_reaction`: analytical summary views.

The run directory also contains `preprocess_audit.json`, `quality_gates.json`,
`integration_manifest.json`, aggregate summary CSVs, complete unmapped-name
counts, target-relevant unmapped candidates and mapping-conflict diagnostics.
`validate-mart` reruns population, join, role, source-row reconciliation and
contingency marginal checks. Unresolved target-like spellings are flagged for
review and never fuzzy-mapped. A passed integration gate still records
`scientific_findings_validated: false`.

`spotcheck` independently rescans the original relations for five primary-exposed,
five other-role statin and five other-background reports, comparing latest IDs,
full drug rows, reaction memberships, role-filtered exposures and mining items.
Its detailed case diagnostics stay local. Student manual review remains pending.
An optional `Frozen FDA ingestion (manual)` GitHub workflow repeats acquisition,
integration and spot checks without running full downloads on every push.

To include WEKA, run the checksum-verifying downloader and reproduce the fixture:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_weka.ps1
$env:WEKA_JAR = (Resolve-Path '.tools/weka/weka-stable-3.8.6.jar').Path
.venv/Scripts/python -m faersight.cli reproduce-fixture --jar $env:WEKA_JAR
.venv/Scripts/python -m pytest -q
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check src tests
```

Java resolution checks `JAVA_HOME`, `PATH`, then Android Studio's bundled Windows
runtime. A different executable can be passed with `--java 'path/to/java.exe'`.
The local validation used the existing Android Studio OpenJDK 21 runtime;
the smoke runner enforces WEKA **3.8.6**. A minimal Maven classpath includes
Bounce **0.18**. WEKA may print a warning about unavailable MTJ matrix jars;
Apriori does not use those matrix routines and the smoke assertions still run.

## Run on Linux

```bash
uv sync --frozen --extra dev
bash scripts/setup_weka.sh
export WEKA_JAR="$PWD/.tools/weka/weka-stable-3.8.6.jar"
uv run --frozen faersight reproduce-fixture --jar "$WEKA_JAR"
uv run --frozen python -m pytest -q
uv run --frozen ruff check .
```

Java 21 must be available through `JAVA_HOME` or `PATH`. CI uses Python 3.11 and
Temurin 21. Tests needing actual WEKA skip when `WEKA_JAR` is unset; setting it
makes WEKA failures fail the suite. GitHub Actions runs the tests and actual WEKA
smoke on pushes; full FDA downloads are excluded from ordinary CI.

## Inspect the evidence

Generated files are in `artifacts/generated/fixture/`:

- `preprocess_audit.json`: deduplication, orphan rows, exclusions, roles, unmapped names.
- `case_index.csv`: ARFF row to retained case/report identifiers.
- `transactions.arff`: ten transactions, including five empty background baskets.
- `analytical.duckdb`: `cases`, `case_items`, and quarter/item count view `item_summary`.
- `signal_counts.csv`: counts and independently verified support, confidence, lift, PRR/ROR.
- `weka/`: ARFF parser check, version logs, raw Apriori output, accepted rules and manifest.
- `comparison.csv`, `manifest.json`, `repro_manifest.json`: comparison and provenance.

The synthetic pair has `a=3, b=1, c=1, d=5, N=10`; support `0.3`, confidence
`0.75`, lift `1.875`, PRR `4.5`, and ROR `15`. WEKA rounds displayed lift to
`1.88`; the smoke check allows only its displayed rounding precision.

The fixture pipeline intentionally stays small and in memory. Use `ingest` for
full-quarter processing. The smoke runner only accepts the known toy pair; it
is not a general real-data mining experiment runner. Use the frozen experiment
runner for actual real-data threshold sweeps and ranking checks:

```powershell
.venv/Scripts/python -m faersight.cli mine data/processed/2025Q4-statins/analytical.duckdb --jar $env:WEKA_JAR --output artifacts/generated/2025Q4-statins-mining
```

The command validates the mart, exports all eligible reports including empty
baskets, compiles the bundled Java bridge with the existing JDK, and executes
actual WEKA Apriori per reaction at each frozen support value. It checks exact
API counts/metrics and exhaustive pair coverage, then writes PRR/ROR, matched
ranking comparisons, threshold stability and positive-benchmark recovery.
Raw logs, runtime hashes, input hashes and a completion manifest are retained.
Existing snapshots cannot be overwritten; choose a new output path for reruns.
See the [execution contract](docs/milestone3.md), including the toy-discovered
WEKA upper-support correction. Outputs remain provisional until the recorded
manual review and scientific gates are complete.

## Role sensitivity and scientific checks

Milestone 4 adds an isolated **2025 Q4 PS versus PS+SS sensitivity** without
changing the frozen primary experiment. It reviews the exact unmapped SS
rosuvastatin-zinc combination in a separate mapping overlay, retains the primary
reaction vocabulary and full reporting population, and reruns actual WEKA:

```powershell
.venv/Scripts/python -m faersight.cli sensitivity data/processed/2025Q4-statins/analytical.duckdb --primary-run artifacts/generated/2025Q4-statins-mining --output artifacts/generated/2025Q4-statins-sensitivity --jar $env:WEKA_JAR
```

New outputs contain benchmark ranks/percentiles for lift, PRR and ROR, raw-cell
ROR 95% intervals, an explicitly conventional PRR screening flag, matched role
comparisons and a small unsigned student-review packet. See
[Milestone 4](docs/milestone4.md) for exact denominators, sparse-cell policies,
executed differences and fresh-clone reproduction evidence. Detailed sample
cases remain local under the new output's `manual_review/` directory.

The core stays within 2025 Q4. Student inspection and interpretation remain
required before the final scientific freeze or optional WEKA showcase extension.

The [roadmap](docs/roadmap.md) separately plans a post-core **WEKA Showcase /
Tool-Study Extension**: full-ARFF Apriori feasibility, multi-item rules, metric
comparisons, FPGrowth and an Explorer demonstration. Step 2A semantics, fixture
and configuration prerequisites are locked and validated; full-data showcase
mining still awaits explicit user continuation.

## Experiment configuration

See [decisions](docs/decisions.md) and [course compliance](docs/course_compliance.md).
The frozen [experiment](config/experiment.yaml),
[class definition](config/therapeutic_class.yaml) and
[reviewed aliases](mappings/drug_mapping.csv) define the real-data run. The draft
[example template](config/experiment.example.yaml) remains available for future
experiments and is rejected by `--require-frozen` until completed.

Technical artifacts here are engineering aids. Course report, literature-review,
slides and narration must be written by the student under the PRD's course policy.

The repository follows the documented
[WEKA Apriori options](https://weka.sourceforge.io/doc.dev/weka/associations/Apriori.html):
lift ranking (`-T 1`) and zero/first-nominal values treated as missing for mining
(`-Z`). No Python Apriori substitute is used.
