# FAERSight

Technical implementation of [PRD.md](PRD.md): case-level FDA reporting associations,
WEKA Apriori, and independently calculated PRR/ROR.

The first engineering milestone runs on **synthetic data only**. It parses
dollar-delimited DEMO/DRUG/REAC fixtures, selects the latest case version, applies
reviewed exact drug aliases and suspect-role filtering, exports sparse binary
ARFF, builds a small DuckDB presence mart, and verifies a real WEKA Apriori rule
against independent contingency counts. Outputs include audits, hashes, raw WEKA
logs, statistics, and a comparison CSV.

Python performs preprocessing and count-based checks. **WEKA performs Apriori**.
Reporting associations do not establish causality or clinical incidence.

## Run on Windows (PowerShell)

From the project root, using Python 3.11+ and uv:

```powershell
uv sync --frozen --extra dev --cache-dir .tools/uv-cache
.venv/Scripts/python -m faersight.cli validate-config config/experiment.example.yaml
.venv/Scripts/python -m faersight.cli build-fixture-arff
.venv/Scripts/python -m pytest -q
```

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
makes WEKA failures fail the suite. GitHub CI is configured but has not been run
on a remote repository.

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

The fixture pipeline is intentionally small and in memory. It is **not ready to
process full quarterly archives**. The current mart contains mining items rather
than the complete retained drug/reaction records. FDA download/extraction,
streaming full-quarter integration, source README/encoding verification,
full analytical mart, threshold sweeps, known-signal evaluation, and ranking
agreement remain later milestones. The smoke runner only accepts the known toy
pair; it is not a general real-data experiment runner.

## Freeze the real experiment next

See [decisions](docs/decisions.md) and [course compliance](docs/course_compliance.md).
The draft [experiment template](config/experiment.example.yaml) intentionally leaves
the therapeutic class, quarter(s), reaction floor and threshold grid unresolved.
`validate-config --require-frozen` rejects it until those values and `status: frozen`
are supplied. The fixture's synthetic quarter is not a real-data selection.

Technical artifacts here are engineering aids. Course report, literature-review,
slides and narration must be written by the student under the PRD's course policy.

The repository follows the documented
[WEKA Apriori options](https://weka.sourceforge.io/doc.dev/weka/associations/Apriori.html):
lift ranking (`-T 1`) and zero/first-nominal values treated as missing for mining
(`-Z`). No Python Apriori substitute is used.
