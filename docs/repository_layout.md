# Repository layout and cleanup record

The primary research pipeline lives in `src/faersight/`. Optional WEKA comparison
and Explorer tooling is grouped under `tools/`; completed checkpoint history is
under `docs/history/`. The research landing page and primary reproduction commands
remain in the [README](../README.md).

## Inventory and dependencies

The [complete inventory](repository_inventory.json) classifies all **437 files**
tracked at baseline `5d21ec1f428eef48293e44855581b72168caee14`. Each entry records
KEEP, CONSOLIDATE or REMOVE, its reason, original SHA-256, current location,
Python import dependents, textual references and immutable-manifest references.
Textual references include historical mentions; they do not imply runtime use.
The inventory also covers direct, locked transitive, build and external
dependencies. **No dependency, scientific configuration or version was changed.**

- **KEEP:** primary pipeline, its tests, FDA/class/benchmark configuration,
  mappings, frozen results, genuine screenshots and essential evidence.
- **CONSOLIDATE:** 39 optional tooling files moved from seven root packages into
  `tools/`, six historical documents moved into `docs/history/`, and necessary
  packaging, audit, CI, test-path and documentation updates.
- **REMOVE:** five one-time scripts retired from the active tree. Their exact
  source remains recoverable; none is a primary pipeline entry point.

The top-level directories now have these responsibilities:

```text
src/faersight/       Primary acquisition, preprocessing, DuckDB, mining and evaluation
config/ mappings/   Frozen scientific definitions and exact drug aliases
benchmarks/         Declared positive-reference signals
tests/              Pipeline, WEKA semantics and provenance regression coverage
tools/              Optional showcase packages, Explorer preparation and source archive
scripts/            Setup, smoke checks, evidence export and read-only verification
artifacts/manifests/ Immutable scientific results, provenance and failure evidence
docs/               Current research, reproduction and verification guides
docs/history/       Completed checkpoint plans and decisions
images/             Genuine manually captured WEKA evidence
```

Raw FDA files, processed databases, generated case packets, environments and
scratch outputs remain local and ignored. All **292 previously tracked artifact
files** remain at their original paths with identical bytes.

## Retired scripts

- `scripts/record_showcase_step2b.py` and `scripts/record_showcase_fpgrowth.py`:
  checkpoint-specific test/lint capture, already preserved in frozen evidence.
- `scripts/export_showcase_step2b.py` and `scripts/export_showcase_fpgrowth.py`:
  one-time checkpoint snapshot exporters, with completed snapshots already frozen.
- `scripts/reproduce_milestone4.py`: the historical primary-base plus uncommitted
  milestone-overlay harness. Its original reproduction/failure/recovery evidence
  remains intact. Current primary and sensitivity reproduction use the CLI
  commands documented in the README.

## Why the fallback stages and evidence remain

A3 imports A2, A2 imports A1, and the metric study reuses A1's independent count
and rule comparison utilities. All three stages have tested, distinct registered
contracts. A1 resolves minimum counts to **1,541 for Apriori / 1,542 for FPGrowth**;
A2 resolves to **1,156**, A3 to **771**. Replacing these with a generic runner
would require a scientific/provenance amendment and a larger refactor. They are
grouped under `tools/` with their original module names rather than deleted.

The [final comparison](weka_showcase_fallback_a3.md) and
[metric study](weka_showcase_metrics.md) retain the findings: **70 / 194 / 586**
rules per algorithm at supports **0.004 / 0.003 / 0.002**, respectively, with
matching rule sets and no statin-containing rules. A1's native-count difference
and common-count comparison remain explicit. The original 0.001 Apriori timeout,
FPGrowth completion, logs, empty exports, compiled evidence and hash sidecars
remain because their manifests and conclusions depend on them. They are unsafe
to prune independently. These are secondary algorithm findings, separate from
the primary drug-safety reporting-association analysis.

## Immutable source references and historical replay

Old manifests retain their original source paths and hashes. Before removing or
moving their dependencies, the exact original Git blobs were stored in
[`original_sources.zip`](../tools/project_layout/original_sources.zip), indexed
by [`catalog.json`](../tools/project_layout/catalog.json). The catalog records
both original bytes and reviewed current replacements. The historical audit
helper verifies the archive hash, each original source hash and each replacement
hash; it rejects tampering and a retired file restored into the active tree.
Scientific inputs and outputs always come from their actual paths.

This archive supports **historical evidence verification**, not execution under
an old source identity. New execution locks still hash live code. Old locked
showcase execution commands require their original source checkout; changed
source must not silently pass an old execution lock. To inspect or recover the
pre-cleanup layout without changing this checkout:

```sh
git worktree add --detach .tools/pre-cleanup 5d21ec1f428eef48293e44855581b72168caee14
python -m zipfile -e tools/project_layout/original_sources.zip .tools/historical-sources
```

The first command recovers the complete prior tracked tree; the second extracts
only affected original sources for inspection. Exact checkpoint execution uses
the code commit recorded in that checkpoint's immutable manifest, its pinned
runtime and separately provisioned inputs. A checkout alone does not recover
ignored FDA data or generated outputs. The overlay harness's historical procedure
is described in [milestone 4](milestone4.md#reproduction-and-freeze-status).
Do not extract archived sources into the active repository root or overwrite
frozen result directories. No new mining experiment was performed for cleanup.

## Verification in the consolidated layout

Run `uv sync --frozen --extra dev` after changing layouts. Imports and existing
`python -m showcase...` module entry points remain available through the editable
installation; no caller must add `tools.` to a module name. The separate plotting
environment receives the tooling search path explicitly. Follow the
[plotting setup](plotting_runtime.md) before running all tests.

```sh
uv run --frozen ruff check .
uv run --frozen ruff format --check src tests tools scripts
uv run --frozen python -m pytest -q
uv run --frozen python scripts/verify_repository.py
```

The repository verifier checks the complete inventory, archived source pins,
reviewed current replacements, unchanged scientific files and README links.
It runs in CI without requiring historical Git objects. The existing read-only
Explorer/metric auditors additionally use the historical Git commits, local
generated evidence, pinned plotting runtime and optional SciPy cross-check.
Their commands remain in the [verification workflow](reproduction_and_demo_readiness.md).

New cleanup files are limited to this guide, the machine-readable inventory,
the source catalog/archive and [historical source helper](../tools/project_layout/__init__.py),
the [repository verifier](../scripts/verify_repository.py), and
[three archive-integrity tests](../tests/unit/test_project_layout.py).

### Cleanup validation

On November 6, 2026, all **195 local tests passed with zero skips**, including
actual WEKA fixtures and deterministic chart/data checks. Ruff lint and formatting
passed. The README's **48 numerical assertions**, three frozen image hashes and
all local Markdown links were checked. A wheel build succeeded, both example and
frozen configurations validated, and the documented synthetic end-to-end CLI
completed in a new scratch output directory.

Read-only Explorer/metric audits verified **108 frozen core files**, **393 protected
prior files**, **1,096 primary / 1,106 sensitivity generated artifacts**, the
unchanged mining-invocation inventory, rank calculations and historical chart
bytes. The Explorer auditor's original pending-GUI status is historical;
[separate manual evidence](weka_explorer_demo.md) retains the completed GUI
observations. No frozen evidence index was rewritten to report cleanup checks.

Student reviewer fields and `scientific_findings_validated=false` remain unchanged.
