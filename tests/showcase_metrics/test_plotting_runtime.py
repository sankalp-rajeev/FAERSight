import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from showcase_metrics import runner, runtime
from showcase_metrics.runner import plotting_versions

PINNED = {"matplotlib": "3.10.8", "numpy": "2.4.2", "pillow": "12.1.1"}


@pytest.fixture
def isolated_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    monkeypatch.delenv(runtime.PLOTTING_ENV, raising=False)
    folder = tmp_path / "showcase_metrics"
    folder.mkdir()
    (folder / "config.json").write_text(json.dumps({"plotting_versions": PINNED}))
    return tmp_path


def interpreter(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"test interpreter")
    return path


def test_environment_override_precedes_project_venv(isolated_runtime, monkeypatch):
    explicit = interpreter(isolated_runtime / "custom runtime/python")
    interpreter(isolated_runtime / ".tools/plotting-venv/bin/python")
    monkeypatch.setenv(runtime.PLOTTING_ENV, str(explicit))
    assert runtime.resolve_plotting_python() == explicit


def test_repo_relative_posix_path_override_is_not_windows_specific(isolated_runtime, monkeypatch):
    expected = interpreter(isolated_runtime / "portable/bin/python")
    monkeypatch.setenv(runtime.PLOTTING_ENV, "portable/bin/python")
    assert runtime.resolve_plotting_python() == expected
    assert Path(runtime.resolve_plotting_python()).is_absolute()


@pytest.mark.parametrize("layout", ["bin/python", "Scripts/python.exe"])
def test_project_local_environment_is_discovered(isolated_runtime, layout):
    expected = interpreter(isolated_runtime / ".tools/plotting-venv" / layout)
    assert runtime.resolve_plotting_python() == expected


def test_missing_runtime_has_actionable_error_without_global_fallback(isolated_runtime):
    with pytest.raises(RuntimeError, match="Set FAERSIGHT_PLOTTING_PYTHON"):
        runtime.resolve_plotting_python()


@pytest.mark.parametrize("override", ["", "missing/bin/python"])
def test_invalid_explicit_override_does_not_silently_fall_back(
    isolated_runtime, monkeypatch, override
):
    interpreter(isolated_runtime / ".tools/plotting-venv/bin/python")
    monkeypatch.setenv(runtime.PLOTTING_ENV, override)
    with pytest.raises(RuntimeError, match="FAERSIGHT_PLOTTING_PYTHON must point"):
        runtime.resolve_plotting_python()


def test_linux_venv_symlink_is_not_resolved_to_base_python(isolated_runtime, monkeypatch):
    # Pure-path simulation also runs on Windows without symlink privileges.
    expected = interpreter(isolated_runtime / ".tools/plotting-venv/bin/python")
    monkeypatch.setattr(
        Path, "resolve", lambda *args, **kwargs: pytest.fail("Venv symlink resolved")
    )
    assert runtime.resolve_plotting_python() == expected


@pytest.mark.parametrize("mismatch", [False, True])
def test_exact_version_pins_and_runtime_provenance(isolated_runtime, monkeypatch, mismatch):
    expected = interpreter(isolated_runtime / ".tools/plotting-venv/bin/python")
    versions = {**PINNED, "numpy": "0.0.0"} if mismatch else PINNED
    observed = {"versions": versions, "python_version": "test 3.11", "platform": "linux"}
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(stdout=json.dumps(observed).encode())

    monkeypatch.setattr(runtime.subprocess, "run", run)
    if mismatch:
        with pytest.raises(ValueError, match="Plotting dependency version changed"):
            plotting_versions()
    else:
        assert plotting_versions() == PINNED
        result = runtime.plotting_runtime()
        assert result["executable"] == str(expected)
        assert result["python_version"] == "test 3.11"
        assert result["platform"] == "linux" and len(result["executable_sha256"]) == 64
    assert calls[0][0] == str(expected)


@pytest.mark.parametrize("changed_science", [False, True])
def test_historical_audit_preserves_old_provenance_without_authorizing_new_execution(
    tmp_path, monkeypatch, changed_science
):
    import hashlib

    scientific = tmp_path / "showcase_metrics/analysis.py"
    scientific.parent.mkdir()
    scientific.write_bytes(b"unchanged scientific source")
    archived = {
        "showcase_metrics/analysis.py": scientific.read_bytes(),
        "showcase_metrics/runner.py": b"original host-specific runner",
        ".github/workflows/ci.yml": b"historical CI without plotting provisioning",
    }
    manifest = {
        "code_commit": "old-commit",
        "source_hashes": {
            name: hashlib.sha256(data).hexdigest()
            for name, data in archived.items()
            if name.endswith(".py")
        },
        "config": {"support": ".002", "plotting_python": "C:/historical/python.exe"},
        "protected_prior_hashes": {
            ".github/workflows/ci.yml": hashlib.sha256(
                archived[".github/workflows/ci.yml"]
            ).hexdigest()
        },
        "full_data_mining_invocations_before": {},
    }
    lock = tmp_path / "manifest.json"
    lock.write_text(json.dumps(manifest))
    monkeypatch.setattr(runner, "LOCK", lock)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(
        runner,
        "config",
        lambda: {
            "support": ".003" if changed_science else ".002",
            "plotting_python_env": runtime.PLOTTING_ENV,
        },
    )
    monkeypatch.setattr(
        runner,
        "git",
        lambda *args, **kwargs: (
            lock.read_bytes() if args[1].startswith("HEAD:") else archived[args[1].split(":", 1)[1]]
        ),
    )
    monkeypatch.setattr(runner, "source_hashes", lambda: {})
    monkeypatch.setattr(runner, "mining_inventory", lambda: {})
    monkeypatch.setattr(runner, "plotting_versions", lambda: PINNED)
    if changed_science:
        with pytest.raises(ValueError, match="scientific configuration changed"):
            runner.verify_lock(historical=True)
    else:
        assert runner.verify_lock(historical=True) == manifest
    with pytest.raises(ValueError, match="Locked code/configuration changed"):
        runner.verify_lock()
