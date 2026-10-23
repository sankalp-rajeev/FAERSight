"""Host-local plotting selection with exact, portable dependency verification."""

import json
import os
import subprocess
from pathlib import Path

from faersight.audit import sha256
from showcase.inspect import ROOT

PLOTTING_ENV = "FAERSIGHT_PLOTTING_PYTHON"
# These current files have an explicit portability amendment. Historical audits
# verify their original committed bytes; scientific code and evidence stay exact.
PORTABILITY_FILES = frozenset(
    {
        ".github/workflows/ci.yml",
        "showcase_metrics/config.json",
        "showcase_metrics/runner.py",
        "tests/showcase_metrics/test_metric_study.py",
        "scripts/verify_showcase_metrics.py",
    }
)


def plotting_env():
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(ROOT / ".tools/metric-matplotlib-config")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def resolve_plotting_python():
    override = os.environ.get(PLOTTING_ENV)
    if override is not None:
        candidate = Path(override).expanduser()
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if override.strip() and candidate.is_file():
            # Retain the venv entry point: resolving a Linux symlink to its base
            # Python would bypass the virtual environment and its pinned packages.
            return candidate.absolute()
        raise RuntimeError(
            f"{PLOTTING_ENV} must point to an existing Python interpreter: {override!r}"
        )
    base = ROOT / ".tools/plotting-venv"
    candidates = (
        [base / "Scripts/python.exe", base / "bin/python"]
        if os.name == "nt"
        else [base / "bin/python", base / "Scripts/python.exe"]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.absolute()
    raise RuntimeError(
        f"No plotting Python found. Set {PLOTTING_ENV} to a Python interpreter with "
        "matplotlib==3.10.8, numpy==2.4.2, pillow==12.1.1, or provision .tools/plotting-venv."
    )


def plotting_runtime():
    executable = resolve_plotting_python()
    code = (
        "import importlib.metadata as m,json,sys; "
        "print(json.dumps({'python_version':sys.version,'platform':sys.platform,"
        "'versions':{p:m.version(p) for p in ('matplotlib','numpy','pillow')}}))"
    )
    try:
        result = subprocess.run(
            [str(executable), "-c", code],
            capture_output=True,
            timeout=30,
            check=True,
            env=plotting_env(),
        )
        observed = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise RuntimeError(
            f"Cannot inspect plotting Python {executable}; set {PLOTTING_ENV} to a working "
            "interpreter with the pinned plotting packages."
        ) from error
    expected = json.loads((ROOT / "showcase_metrics/config.json").read_text())["plotting_versions"]
    if observed.get("versions") != expected:
        raise ValueError(
            f"Plotting dependency version changed: expected {expected}, "
            f"got {observed.get('versions')}"
        )
    return {"executable": str(executable), "executable_sha256": sha256(executable), **observed}


def plotting_python():
    return plotting_runtime()["executable"]
