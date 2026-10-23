# Portable plotting runtime

The metric-study chart test requires exactly Matplotlib 3.10.8, NumPy 2.4.2 and
Pillow 12.1.1. Current config pins these versions without a machine-local Python
path. Metric calculations, chart rendering code and all historical evidence are
unchanged by this portability fix.

Runtime selection uses this order:

1. `FAERSIGHT_PLOTTING_PYTHON`, an explicit interpreter file path. Relative paths
   are interpreted from the repository root; spaces are supported. An invalid
   explicit value fails instead of silently choosing a different environment.
2. An intentionally provisioned `.tools/plotting-venv`: `Scripts/python.exe` on
   Windows or `bin/python` on Linux. The venv entry point is retained even if it
   is a symlink to a base interpreter.
3. A clear error explaining how to set the variable or provision the environment.
   No arbitrary Python from PATH is selected.

Every plotting entry point verifies all three package versions before use.
Missing packages, an unusable interpreter or mismatched versions fail. Runtime
metadata records the resolved path, Python version, platform, exact package
versions and an executable SHA-256 as provenance for that host; an executable hash
or filesystem path from another host is not a portable equivalence criterion.

## GitHub Actions and local environments

CI retains the existing Python 3.11 setup and provisions a separate environment:

```sh
python -m venv .tools/plotting-venv
.tools/plotting-venv/bin/python -m pip install matplotlib==3.10.8 numpy==2.4.2 pillow==12.1.1
export FAERSIGHT_PLOTTING_PYTHON="$PWD/.tools/plotting-venv/bin/python"
```

The workflow exports the path through `GITHUB_ENV`, verifies it, then runs the
existing suite. It adds no SciPy dependency and does not change the primary
environment or `uv.lock`. Normal transitive dependencies of the three plotting
packages are installed automatically.

Windows contributors can provision the same local environment with Python 3.11:

```powershell
py -3.11 -m venv .tools/plotting-venv
.tools/plotting-venv/Scripts/python -m pip install matplotlib==3.10.8 numpy==2.4.2 pillow==12.1.1
```

Or explicitly select an existing compatible environment, including the historical
local runtime when present:

```powershell
$env:FAERSIGHT_PLOTTING_PYTHON="C:/Umich/Projects/Kairos/.venv/Scripts/python.exe"
```

That path is an optional example, not a contributor prerequisite. The same exact
version checks apply. Inspect the active runtime from the repository root:

```sh
uv run --frozen python -c "from showcase_metrics.runtime import plotting_runtime; print(plotting_runtime())"
```

## Historical lock and deterministic checks

The old metric manifest retains its original Windows interpreter path/hash and
original source/config hashes as execution provenance. It is not rewritten.
Read-only metric audits explicitly use `verify_lock(historical=True)`, checking
the original committed source bytes, unchanged scientific/plot code, unchanged
scientific configuration and every protected artifact. Only the explicitly named
portability config/runner/test/audit/workflow files are treated as amended current code.
The Explorer preparation audit makes the same historical/current distinction.

The normal execution lock remains strict: amended source cannot be executed as a
new locked analysis under the old source hashes. This fix authorizes no new
analysis/mining run and creates no replacement scientific manifest.

The deterministic chart/data-byte test remains mandatory and unskipped, with the
same byte-equality assertions and three-chart count. It checks repeatability
within the provisioned runtime. Historical chart reproduction audits use the
recorded compatible host environment (and their existing optional SciPy check);
CI does not add SciPy or assert cross-platform PNG/SVG byte identity.


## Portability-fix validation

The local suite passes all 192 tests with the pinned WEKA fixture runtime enabled,
zero skips, including the original deterministic chart/data-byte test and 12 new
runtime/provenance cases. The original chart-byte assertions are unchanged.
Both the project-local Python 3.11 plotting environment and the explicit historical
Windows override were exercised. Ruff lint/format and workflow YAML validation pass.

Before/after checks against 214a892 retain all 414 unchanged tracked files; the
seven amended existing files are only the CI workflow, current plotting config/
runner/test, two read-only auditors and README. All tracked artifact/evidence
files, 108 frozen scientific-core files, 1096 primary and 1106 sensitivity generated
artifacts retain their hashes. The full-data mining invocation inventory is
unchanged. Metric/Explorer historical audits pass without rewriting their records.
No association experiment or scientific result was regenerated.
