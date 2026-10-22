"""Export aggregate milestone evidence while keeping report-level samples local."""

import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from faersight.audit import sha256, write_json
from faersight.disproportionality import Counts
from faersight.mining import read_csv
from faersight.screening import screening_metrics
from faersight.weka import write_csv


def export(source: Path, output: Path, tests: Path, reproduction: Path) -> dict:
    manifest = json.loads((source / "sensitivity_manifest.json").read_text(encoding="utf-8"))
    if (
        manifest["status"] != "computational_gates_passed"
        or not manifest["primary_experiment_unchanged"]
    ):
        raise ValueError("Only completed sensitivity checks can be exported")
    for name, digest in manifest["artifacts"].items():
        path = (source / name).resolve()
        if not path.is_relative_to(source.resolve()) or sha256(path) != digest:
            raise ValueError(f"Sensitivity artifact changed: {name}")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Evidence directory exists; choose a new snapshot")
    output.mkdir(parents=True, exist_ok=True)
    names = {
        "sensitivity_manifest.json": "sensitivity_manifest.json",
        "all_counts_screened.csv": "all_counts_screened.csv",
        "benchmark_ranks.csv": "benchmark_ranks.csv",
        "benchmark_recovery.csv": "benchmark_recovery.csv",
        "method_rank_comparison.json": "method_rank_comparison.json",
        "role_comparison.json": "role_comparison.json",
        "mart_quality_gates.json": "mart/quality_gates.json",
        "deferred_reactions.csv": "mart/deferred_reactions.csv",
        "ps_ss_without_overlay_counts.csv": "mart/ps_ss_without_overlay_counts.csv",
        "arff_manifest.json": "ps_ss/input/manifest.json",
        "weka_manifest.json": "ps_ss/weka/manifest.json",
        "weka_rules.csv": "ps_ss/weka/weka_rules.csv",
        "weka_runs.csv": "ps_ss/weka/weka_runs.csv",
        "manual_review_manifest.json": "manual_review/package_manifest.json",
        "manual_review_instructions.md": "manual_review/README.md",
        "manual_rule_review.csv": "manual_review/rules.csv",
        "benchmark_review_checklist.csv": "manual_review/benchmark_checklist.csv",
    }
    for name in (
        "compile.log",
        "java_version.log",
        "javac_version.log",
        "progress.log",
        "complete.txt",
    ):
        names[name] = "ps_ss/weka/" + name
    for destination, origin in names.items():
        shutil.copyfile(source / origin, output / destination)
    scored = read_csv(source / "all_counts_screened.csv")
    lookups = {
        role: {(r["drug"], r["reaction"]): r for r in scored if r["role"] == role}
        for role in ("PS", "PS+SS")
    }
    uncorrected = {
        (r["drug"], r["reaction"]): r
        for r in read_csv(source / "mart/ps_ss_without_overlay_counts.csv")
    }
    differences, mapping_effect = [], []
    for key in sorted(lookups["PS"]):
        ps, ss = lookups["PS"][key], lookups["PS+SS"][key]
        differences.append(
            {
                "drug": key[0],
                "reaction": key[1],
                **{
                    f"{role}_{column}": row[column]
                    for role, row in [("ps", ps), ("ps_ss", ss)]
                    for column in (
                        "a",
                        "b",
                        "c",
                        "d",
                        "n",
                        "lift_python_check",
                        "prr",
                        "ror",
                        "ror_ci95_lower",
                        "ror_ci95_upper",
                        "prr_screen_convention",
                    )
                },
            }
        )
        before = uncorrected[key]
        if any(before[cell] != ss[cell] for cell in "abcd"):
            metrics = screening_metrics(Counts(*(int(before[cell]) for cell in "abcd")))
            mapping_effect.append(
                {
                    "drug": key[0],
                    "reaction": key[1],
                    **{
                        f"{role}_{column}": row[column]
                        for role, row in [("without_overlay", metrics), ("with_overlay", ss)]
                        for column in ("a", "b", "c", "d", "prr", "ror", "prr_screen_convention")
                    },
                }
            )
    write_csv(output / "role_pair_differences.csv", differences)
    write_csv(output / "mapping_effect.csv", mapping_effect)
    xml = ET.parse(tests).getroot()
    suites = list(xml) if xml.tag == "testsuites" else [xml]
    counts = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")
    }
    if any(counts[k] for k in ("failures", "errors", "skipped")):
        raise ValueError("Milestone tests did not all pass with WEKA enabled")
    write_json(
        output / "test_results.json",
        {
            **counts,
            "passed": counts["tests"],
            "actual_weka_tests_enabled": True,
            "junit_sha256": sha256(tests),
            "scientific_findings_validated": False,
        },
    )
    repro = json.loads((reproduction / "fresh_clone_reproduction.json").read_text())
    if repro["status"] != "passed":
        raise ValueError("Fresh-clone reproduction has not passed")
    shutil.copyfile(
        reproduction / "fresh_clone_reproduction.json", output / "fresh_clone_reproduction.json"
    )
    for log in reproduction.glob("*.log"):
        shutil.copyfile(log, output / ("reproduction_" + log.name))
    initial = reproduction.parent / "milestone4-reproduction/fresh_clone_reproduction.json"
    if initial.is_file():
        shutil.copyfile(initial, output / "reproduction_initial_setup_attempt.json")
    logs = sorted((source / "ps_ss/weka/raw").rglob("*.log"))
    with zipfile.ZipFile(output / "weka_raw_logs.zip", "w") as archive:
        for path in logs:
            entry = zipfile.ZipInfo(
                path.relative_to(source / "ps_ss/weka").as_posix(), date_time=(1980, 1, 1, 0, 0, 0)
            )
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    with zipfile.ZipFile(output / "weka_raw_logs.zip") as archive:
        for name in archive.namelist():
            if (
                hashlib.sha256(archive.read(name)).hexdigest()
                != manifest["artifacts"]["ps_ss/weka/" + name]
            ):
                raise ValueError("Archived raw WEKA log mismatch")
    index = {
        "status": "provisional_computational_evidence",
        "quarters": ["2025Q4"],
        "primary_experiment_unchanged": True,
        "scientific_findings_validated": False,
        "raw_weka_logs": len(logs),
        "mapping_affected_pairs": len(mapping_effect),
        "report_level_records_included": False,
        "fresh_clone_reproduction": "passed",
        "student_review_completed": False,
        "artifacts": {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    write_json(output / "evidence_index.json", index)
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--tests", type=Path, required=True)
    parser.add_argument("--reproduction", type=Path, required=True)
    args = parser.parse_args()
    result = export(args.source, args.output, args.tests, args.reproduction)
    print(json.dumps({k: v for k, v in result.items() if k != "artifacts"}, indent=2))
