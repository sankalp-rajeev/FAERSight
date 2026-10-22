"""Rebuild frozen primary and sensitivity in an isolated clone from a Git bundle.

The optional prepared clone must be clean at the recorded primary commit. The
new milestone is transferred as a checksum-recorded working-tree overlay, not
misrepresented as a committed revision. Cached archive/jars are explicitly reused;
no processed data, ARFF, results, or environment are copied into the clone.
"""

import argparse
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from faersight.audit import sha256, write_json

OVERLAY = [
    "src/faersight/cli.py",
    "src/faersight/sensitivity.py",
    "src/faersight/manual_review.py",
    "src/faersight/benchmark_ranking.py",
    "src/faersight/screening.py",
    "config/sensitivity.yaml",
    "mappings/sensitivity_ss_aliases.csv",
    "mappings/sensitivity_ss_review.yaml",
    "tests/integration/test_sensitivity.py",
    "tests/unit/test_benchmark_ranking.py",
    "tests/unit/test_screening.py",
]
PRIMARY_FILES = [
    "input/transactions.arff",
    "input/case_index.csv",
    "weka/weka_rules.csv",
    "weka/complete.txt",
    *[
        f"evaluation/{name}"
        for name in (
            "all_candidate_counts.csv",
            "accepted_rules_scored.csv",
            "benchmark_recovery.csv",
            "quality_gates.json",
            "ranking_comparison.json",
            "support_stability.json",
        )
    ],
]
SENSITIVITY_FILES = [
    "ps_ss/input/transactions.arff",
    "ps_ss/input/case_index.csv",
    "ps_ss/weka/weka_rules.csv",
    "ps_ss/weka/complete.txt",
    "all_counts_screened.csv",
    "benchmark_ranks.csv",
    "benchmark_recovery.csv",
    "role_comparison.json",
    "method_rank_comparison.json",
    "mart/ps_ss_without_overlay_counts.csv",
    "mart/deferred_reactions.csv",
    "manual_review/cases.json",
    "manual_review/rules.csv",
    "manual_review/case_checklist.csv",
    "manual_review/benchmark_checklist.csv",
    "manual_review/README.md",
    "manual_review/package_manifest.json",
]


def compare(left: Path, right: Path, names: list[str]) -> dict:
    rows = {
        name: {"reference_sha256": sha256(left / name), "reproduced_sha256": sha256(right / name)}
        for name in names
    }
    for row in rows.values():
        row["matches"] = row["reference_sha256"] == row["reproduced_sha256"]
    if not all(row["matches"] for row in rows.values()):
        raise ValueError(
            "Deterministic artifact mismatch: "
            + ", ".join(name for name, row in rows.items() if not row["matches"])
        )
    return rows


def compare_weka(left: Path, right: Path) -> dict:
    from faersight.mining import read_csv

    logs = sorted(p.relative_to(left).as_posix() for p in (left / "raw").rglob("*.log"))
    other = sorted(p.relative_to(right).as_posix() for p in (right / "raw").rglob("*.log"))
    if logs != other or len(logs) != 1077:
        raise ValueError("Fresh clone changed the WEKA projection schedule")
    compared = compare(left, right, logs)
    stable_runs = []
    for folder in (left, right):
        stable_runs.append(
            [
                {k: v for k, v in row.items() if k != "seconds"}
                for row in read_csv(folder / "weka_runs.csv")
            ]
        )
    if stable_runs[0] != stable_runs[1]:
        raise ValueError("WEKA run metadata differs beyond elapsed time")
    return {
        "raw_logs_compared": len(compared),
        "all_raw_logs_byte_identical": True,
        "run_records_match_except_seconds": True,
    }


def reproduce(
    root: Path,
    clone: Path,
    record_folder: Path,
    jar: Path,
    prepared: bool,
    resume: bool = False,
    integrated_mart: Path | None = None,
) -> dict:
    root, clone, record_folder, jar = [p.resolve() for p in (root, clone, record_folder, jar)]
    record_folder.mkdir(parents=True, exist_ok=True)
    record_path = record_folder / "fresh_clone_reproduction.json"
    if record_path.exists() and not resume:
        raise ValueError("Reproduction record already exists")
    env = dict(os.environ, WEKA_JAR=str(jar), PYTHONUNBUFFERED="1")
    record = {
        "status": "running",
        "started_utc": datetime.now(UTC).isoformat(),
        "clone": str(clone),
        "fresh_clone_method": "local_git_bundle",
        "cached_inputs_reused": [
            "checksum_pinned_FDA_archive",
            "WEKA_and_Bounce_jars",
            "uv_package_cache",
        ],
        "processed_data_or_results_copied": False,
        "scientific_findings_validated": False,
        "commands": [],
    }
    if resume:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record["status"] != "failed" or record["clone"] != str(clone):
            raise ValueError("Only a failed record for this clone can be resumed")
        record.setdefault("resolved_attempt_failures", []).append(
            {"error": record.pop("error"), "finished_utc": record.pop("finished_utc")}
        )
        record["status"] = "running"

    def command(args, name, cwd=clone):
        if resume and any(r["name"] == name and r["exit_code"] == 0 for r in record["commands"]):
            return
        with (record_folder / f"{name}.log").open("wb") as stream:
            result = subprocess.run(
                [str(a) for a in args],
                cwd=cwd,
                env=env,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=3600,
            )
        record["commands"].append(
            {"name": name, "args": [str(a) for a in args], "exit_code": result.returncode}
        )
        write_json(record_path, record)
        if result.returncode:
            raise ValueError(f"Reproduction command failed: {name}")

    try:
        if not prepared:
            if clone.exists():
                raise ValueError("Use a new clone path")
            bundle = record_folder / "primary.bundle"
            command(
                [
                    "git",
                    "-c",
                    f"safe.directory={root.as_posix()}",
                    "bundle",
                    "create",
                    bundle,
                    "HEAD",
                ],
                "bundle",
                cwd=root,
            )
            command(["git", "clone", bundle, clone], "clone", cwd=root)
        git = ["git", "-c", f"safe.directory={clone.as_posix()}"]
        if not prepared:
            command(
                [*git, "checkout", "--detach", "262dfc0bea7c39e0430747927931b98fbbeca96f"],
                "checkout_frozen_primary",
            )
        head = subprocess.run(
            [*git, "rev-parse", "HEAD"], cwd=clone, capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = subprocess.run(
            [*git, "status", "--porcelain"], cwd=clone, capture_output=True, text=True, check=True
        ).stdout.strip()
        if dirty or head != "262dfc0bea7c39e0430747927931b98fbbeca96f":
            raise ValueError("Expected a clean clone of the frozen primary checkpoint")
        record["primary_git_commit"] = head
        record["primary_initial_worktree_clean"] = True
        python = clone / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
        command(
            [
                "uv",
                "sync",
                "--frozen",
                "--extra",
                "dev",
                "--offline",
                "--cache-dir",
                root / ".tools/uv-cache",
            ],
            "environment",
        )
        # pytest's configured basetemp needs this ignored parent on a fresh clone.
        (clone / ".tools").mkdir(exist_ok=True)
        raw = clone / "data/raw/2025Q4"
        raw.mkdir(parents=True, exist_ok=True)
        for name in ("faers_ascii_2025Q4.zip", "faers_ascii_2025Q4.manifest.json"):
            shutil.copyfile(root / "data/raw/2025Q4" / name, raw / name)
        record["archive_sha256"] = sha256(raw / "faers_ascii_2025Q4.zip")
        record["runtime_jar_hashes"] = {p.name: sha256(p) for p in jar.parent.glob("*.jar")}
        cli = [python, "-m", "faersight.cli"]
        command([*cli, "acquire"], "acquire_verify_and_extract")
        command(
            [python, "-m", "pytest", "-q", "--junitxml=artifacts/generated/primary_tests.xml"],
            "primary_tests",
        )
        if integrated_mart is None:
            command([*cli, "ingest"], "primary_ingest")
            database = clone / "data/processed/2025Q4-statins/analytical.duckdb"
        else:
            from faersight.integration import validate_mart

            database = integrated_mart.resolve()
            if not database.is_relative_to(clone) or validate_mart(database)["status"] != "passed":
                raise ValueError("Recovery mart must be a validated rebuild inside this clone")
            integration = json.loads((database.parent / "integration_manifest.json").read_text())
            if integration.get("git_commit") != head or integration.get("git_worktree_dirty"):
                raise ValueError("Recovery mart was not built from the clean primary clone")
            record["ingestion_recovery"] = {
                "reason": "initial_ingest_returned_zero_without_completion_artifacts",
                "method": "direct_clone_python_cli_ingest_with_new_output_directory",
                "database": str(database),
                "integration_manifest_sha256": sha256(
                    database.parent / "integration_manifest.json"
                ),
                "quality": validate_mart(database),
                "scientific_findings_validated": False,
            }
        if not database.is_file() or not (database.parent / "integration_manifest.json").is_file():
            raise ValueError("Ingest exited without required completion artifacts")
        primary_run = clone / "artifacts/generated/2025Q4-statins-mining"
        command([*cli, "mine", database, "--output", primary_run, "--jar", jar], "primary_mining")
        baseline = root / "artifacts/generated/2025Q4-statins-mining"
        record["primary_deterministic_artifacts"] = compare(baseline, primary_run, PRIMARY_FILES)
        record["primary_weka"] = compare_weka(baseline / "weka", primary_run / "weka")
        # A separately disclosed source snapshot adds the new milestone to the clean base.
        record["milestone_overlay_is_committed"] = False
        record["milestone_overlay_hashes"] = {}
        for name in OVERLAY:
            destination = clone / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, destination)
            if sha256(destination) != sha256(root / name):
                raise ValueError("Milestone source transfer changed bytes")
            record["milestone_overlay_hashes"][name] = sha256(destination)
        command(
            [python, "-m", "pytest", "-q", "--junitxml=artifacts/generated/sensitivity_tests.xml"],
            "milestone_tests",
        )
        sensitivity_run = clone / "artifacts/generated/2025Q4-statins-sensitivity"
        command(
            [
                *cli,
                "sensitivity",
                database,
                "--primary-run",
                primary_run,
                "--output",
                sensitivity_run,
                "--jar",
                jar,
            ],
            "sensitivity",
        )
        baseline_ss = root / "artifacts/generated/2025Q4-statins-sensitivity"
        record["sensitivity_deterministic_artifacts"] = compare(
            baseline_ss, sensitivity_run, SENSITIVITY_FILES
        )
        record["sensitivity_weka"] = compare_weka(
            baseline_ss / "ps_ss/weka", sensitivity_run / "ps_ss/weka"
        )
        record["status"] = "passed"
        record["limitations"] = [
            "same_host_and_existing_Java_runtime",
            "cached_pinned_archive_and_dependency_jars",
            "new_milestone_reproduced_from_hashed_uncommitted_overlay",
        ]
    except Exception as exc:
        record["status"] = "failed"
        record["error"] = str(exc)
        raise
    finally:
        record["finished_utc"] = datetime.now(UTC).isoformat()
        record["log_hashes"] = {p.name: sha256(p) for p in record_folder.glob("*.log")}
        write_json(record_path, record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--clone", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--prepared-clone", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--integrated-mart", type=Path)
    args = parser.parse_args()
    result = reproduce(
        args.root,
        args.clone,
        args.records,
        args.jar,
        args.prepared_clone,
        args.resume,
        args.integrated_mart,
    )
    print(json.dumps({k: v for k, v in result.items() if k in {"status", "limitations"}}, indent=2))
