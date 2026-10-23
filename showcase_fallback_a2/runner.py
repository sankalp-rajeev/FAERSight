"""Lock/run/export only Fallback A2 0.003, with Apriori-first fail-closed gating."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from faersight.audit import sha256, write_json
from showcase import runner as apriori
from showcase.inspect import ROOT, pinned_runtime
from showcase_fallback_a2.analysis import (
    compare,
    export_statin_rules,
    independent_count_check,
    read_postings,
    read_rules,
    structure,
)
from showcase_fpgrowth import runner as fp

BASE = ROOT / "showcase_fallback_a2"
CONFIG = BASE / "config.json"
EVIDENCE = ROOT / "artifacts/manifests/weka-showcase-fallback-a2-0.003"
LOCK = EVIDENCE / "locked/execution_manifest.json"
ALGORITHMS = ("apriori", "fpgrowth")


def config():
    result = json.loads(CONFIG.read_text())
    if result["support"] != "0.003" or result["minimum_counts"] != {
        "apriori": 1156,
        "fpgrowth": 1156,
    }:
        raise ValueError("Only the registered A2 support is authorized")
    if apriori.minimum_count("0.003", 385288) != 1156 or fp.minimum_count("0.003", 385288) != 1156:
        raise ValueError("Verified minimum-count semantics changed")
    return result


def options(algorithm, support="0.003"):
    if algorithm not in ALGORITHMS:
        raise ValueError("Unknown algorithm")
    return apriori.options(support) if algorithm == "apriori" else fp.options(support)


def sources():
    paths = [p for p in BASE.rglob("*") if p.is_file() and p.suffix in {".py", ".json"}]
    paths += sorted((ROOT / "tests/showcase_fallback_a2").glob("*.py"))
    return {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(paths)}


def vocabulary():
    return json.loads(
        (ROOT / "artifacts/manifests/2025Q4-statins-mining/arff_manifest.json").read_text()
    )["attributes"]


def preserve_history():
    baseline = "b5daa01"
    folders = [
        "config",
        "benchmarks",
        "mappings",
        "src",
        "tests",
        "showcase",
        "showcase_fpgrowth",
        "showcase_fallback_a1",
        "artifacts/manifests",
        "scripts/record_showcase_step2b.py",
        "scripts/export_showcase_step2b.py",
        "scripts/record_showcase_fpgrowth.py",
        "scripts/export_showcase_fpgrowth.py",
        "docs/weka_showcase_step2b.md",
        "docs/weka_showcase_fpgrowth.md",
        "docs/weka_showcase_fallback_a1.md",
    ]
    names = fp.git("ls-tree", "-r", "--name-only", baseline, "--", *folders).splitlines()
    hashes = {}
    for name in names:
        digest = hashlib.sha256(fp.git("show", baseline + ":" + name, binary=True)).hexdigest()
        if sha256(ROOT / name) != digest:
            raise ValueError("Prior committed file changed: " + name)
        hashes[name] = digest
    return {"baseline_commit": baseline, "verified_files": len(hashes), "hashes": hashes}


def check_result(algorithm, folder, *, n, minimum, support, names):
    if not (folder / "complete.txt").is_file():
        raise ValueError("Incomplete export")
    run = json.loads((folder / "run.json").read_text())
    if run["weka_version"] != "3.8.6" or run["rows"] != n or run["attributes"] != len(names):
        raise ValueError("Native dimensions/version mismatch")
    settings = run["settings"]
    if settings["metric_id"] != 1 or settings["minimum_metric"] != 1.2:
        raise ValueError("Native metric changed")
    if algorithm == "apriori":
        if (
            run["cycles"] != 1
            or run["minimum_count"] != minimum
            or run["rule_cap_reached_or_ambiguous"]
            or run["integer_partition_limit_exceeded"]
            or not settings["treat_zero_as_missing"]
            or settings["class_rules"]
        ):
            raise ValueError("Apriori schedule/cap/length/presence gate failed")
    else:
        if (
            run["tree_build_passes"] != 1
            or run["resolved_lower_count"] != minimum
            or not run["api_equals_internal_count"]
            or run["rule_policy_limit_reached"]
            or run["has_nonpresence_items"]
            or not settings["find_all"]
            or settings["positive_index"] != 2
            or settings["maximum_items"] != -1
            or settings["available_processors"] != 2
            or settings["max_heap_bytes"] != 4294967296
        ):
            raise ValueError("FPGrowth schedule/completeness/presence gate failed")
    rules = read_rules(
        folder,
        n=n,
        minimum_count=minimum,
        support=support,
        vocabulary={name + "=1" for name in names},
    )
    if len(rules) != run["returned_rules"]:
        raise ValueError("Native/CSV rule count mismatch")
    return run, rules


def invoke(algorithm, output, *, fixture=True):
    settings, java, cp = pinned_runtime()
    cfg = config()
    arff = apriori.FIXTURE if fixture else ROOT / settings["input"]["path"]
    support, n, names = (
        ("0.1", 20, apriori.fixture_transactions()[0])
        if fixture
        else ("0.003", 385288, vocabulary())
    )
    minimum = (apriori.minimum_count if algorithm == "apriori" else fp.minimum_count)(support, n)
    source = apriori.SOURCE if algorithm == "apriori" else fp.SOURCE
    if algorithm not in ALGORITHMS:
        raise ValueError("Unknown algorithm")
    if not fixture and sha256(arff) != settings["input"]["sha256"]:
        raise ValueError("Frozen input changed")
    output.mkdir(parents=True, exist_ok=False)
    classes = output / "classes"
    classes.mkdir()
    record = {
        "status": "running",
        "algorithm": algorithm,
        "fixture": fixture,
        "started_utc": datetime.now(UTC).isoformat(),
        "support": support,
        "resolved_minimum_count": minimum,
        "input_sha256": sha256(arff),
        "source_sha256": sha256(source),
        "options": options(algorithm, support),
        "process_exit_code": None,
        "scientific_findings_validated": False,
    }
    started = time.perf_counter()
    try:
        with apriori.single_jvm():
            command = [
                str(java.with_name("javac.exe")),
                "-encoding",
                "UTF-8",
                "-cp",
                cp,
                "-d",
                str(classes.resolve()),
                str(source),
            ]
            record["compile_command"] = command
            with (output / "compile.txt").open("wb") as stream:
                subprocess.run(
                    command,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    timeout=cfg["compile_timeout_seconds"],
                    check=True,
                )
            command = [
                str(java),
                "-Xmx4g",
                "-XX:ActiveProcessorCount=2",
                "-cp",
                str(classes.resolve()) + os.pathsep + cp,
            ]
            if algorithm == "apriori":
                command += [
                    "faersight.showcase.ShowcaseApriori",
                    "mine",
                    str(arff),
                    str(output.resolve()),
                    str(n),
                    str(len(names)),
                ]
            else:
                command += [
                    "faersight.showcasefp.ShowcaseFPGrowth",
                    str(arff),
                    str(output.resolve()),
                    str(n),
                    str(len(names)),
                    "true",
                ]
            command += record["options"]
            record["command"] = command
            write_json(output / "invocation.json", record)
            jvm_started = time.perf_counter()
            with (
                (output / "stdout.txt").open("wb") as stdout,
                (output / "stderr.txt").open("wb") as stderr,
            ):
                with subprocess.Popen(command, stdout=stdout, stderr=stderr) as process:
                    try:
                        record["process_exit_code"] = process.wait(
                            timeout=cfg["timeout_seconds_per_jvm"]
                        )
                    except subprocess.TimeoutExpired:
                        process.kill()
                        record["process_exit_code"] = process.wait()
                        record["killed_at_timeout"] = True
                        raise
                    finally:
                        record["jvm_wall_seconds"] = time.perf_counter() - jvm_started
            if record["process_exit_code"] != 0:
                raise subprocess.CalledProcessError(record["process_exit_code"], command)
        record["process_and_compile_wall_seconds"] = time.perf_counter() - started
        run, rules = check_result(
            algorithm, output, n=n, minimum=minimum, support=support, names=names
        )
        record["status"] = "passed"
        record["association_build_seconds"] = run["association_build_seconds"]
        record["returned_rules"] = len(rules)
        record["frequent_itemsets"] = run["frequent_itemsets"]
        record["structure"] = structure(rules)
    except Exception as exc:
        record["status"] = "failed"
        record["failure_kind"] = (
            "timeout"
            if isinstance(exc, subprocess.TimeoutExpired)
            else (
                "process_failure"
                if isinstance(exc, subprocess.CalledProcessError)
                else "semantic_or_cap_error"
            )
        )
        record["error"] = str(exc)
    finally:
        record["total_driver_wall_seconds"] = time.perf_counter() - started
        record["finished_utc"] = datetime.now(UTC).isoformat()
        record["hashes"] = {
            p.relative_to(output).as_posix(): sha256(p)
            for p in sorted(output.rglob("*"))
            if p.is_file() and p.name != "invocation.json"
        }
        write_json(output / "invocation.json", record)
    return record


def fixture_checkpoint(output):
    output.mkdir(parents=True, exist_ok=False)
    records = {a: invoke(a, output / a) for a in ALGORITHMS}
    if any(r["status"] != "passed" for r in records.values()):
        raise ValueError("Fixture failed")
    names = apriori.fixture_transactions()[0]
    rules = {
        a: check_result(a, output / a, n=20, minimum=2, support="0.1", names=names)[1]
        for a in ALGORITHMS
    }
    result = compare(rules["apriori"], rules["fpgrowth"], 2)
    if (
        result["common_support_comparison"]["intersection"] != 50
        or not result["common_support_comparison"]["shared_metrics_reconcile"]
    ):
        raise ValueError("Fixture comparison failed")
    for a in ALGORITHMS:
        (apriori.check_fixture if a == "apriori" else fp.check_fixture)(output / a)
    statin_exports = {a: export_statin_rules(rules[a], a, output) for a in ALGORITHMS}
    report = {
        "statin_fixture_exports": statin_exports,
        "status": "passed",
        "comparison": result,
        "invocations": records,
        "source_hashes": sources(),
        "full_data_run_started": False,
        "hashes": {
            p.relative_to(output).as_posix(): sha256(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    }
    write_json(output / "fixture_result.json", report)
    return report


def lock(fixture):
    cfg = config()
    if fp.git("status", "--porcelain", "--", "showcase_fallback_a2", "tests/showcase_fallback_a2"):
        raise ValueError("Commit implementation before locking")
    history = preserve_history()
    original, java, _ = pinned_runtime()
    arff = ROOT / original["input"]["path"]
    if sha256(arff) != original["input"]["sha256"]:
        raise ValueError("Input hash mismatch")
    posts, rows, empty = read_postings(arff, vocabulary())
    if rows != 385288 or empty != 117325:
        raise ValueError("Population changed")
    drugs = {name[:-2]: len(post) for name, post in posts.items() if name.startswith("DRUG_")}
    eligibility = {
        a: {
            drug: {"count": count, "eligible": count >= cfg["minimum_counts"][a]}
            for drug, count in drugs.items()
        }
        for a in ALGORITHMS
    }
    if any(
        [drug for drug, detail in eligibility[a].items() if detail["eligible"]]
        != ["DRUG_atorvastatin"]
        for a in ALGORITHMS
    ):
        raise ValueError("Unexpected A2 statin singleton eligibility")
    check = json.loads((fixture / "fixture_result.json").read_text())
    if check["source_hashes"] != sources() or check["status"] != "passed":
        raise ValueError("Fixture source/status changed")
    if any(sha256(fixture / name) != digest for name, digest in check["hashes"].items()):
        raise ValueError("Fixture artifact changed")
    LOCK.parent.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(
        LOCK.parent / "fixture_evidence.zip", "w", zipfile.ZIP_DEFLATED
    ) as archive:
        for p in sorted(fixture.rglob("*")):
            if p.is_file():
                archive.write(p, p.relative_to(fixture).as_posix())
    versions = {}
    with apriori.single_jvm():
        for name, executable in [("java", java), ("javac", java.with_name("javac.exe"))]:
            run = subprocess.run(
                [str(executable), "-version"], capture_output=True, timeout=30, check=True
            )
            text = run.stdout + run.stderr
            (LOCK.parent / (name + "_version.txt")).write_bytes(text)
            versions[name] = text.decode()
    result = {
        "status": "locked_before_either_full_data_invocation",
        "config": cfg,
        "code_commit": fp.git("rev-parse", "HEAD"),
        "source_hashes": sources(),
        "input": original["input"],
        "runtime": original["runtime"],
        "versions": versions,
        "options": {a: options(a) for a in ALGORITHMS},
        "protected_history": history,
        "statin_presence_counts": drugs,
        "statin_singleton_eligibility": eligibility,
        "fixture_archive_sha256": sha256(LOCK.parent / "fixture_evidence.zip"),
        "fixture_result_sha256": sha256(fixture / "fixture_result.json"),
        "canonical_export_schema": apriori.SCHEMA,
        "registered_command": (
            ".venv/Scripts/python -m showcase_fallback_a2.runner run --authorize-full-data"
        ),
        "monotonic_support_observation": (
            "With other settings fixed, higher support cannot introduce statin rules "
            "absent from the complete 0.001 FPGrowth pool"
        ),
        "native_support_counts_identical": True,
        "representative_selection": (
            "first 8 by total length then canonical lhs/rhs; all statin rules exported"
        ),
        "full_data_mining_started": False,
        "scientific_findings_validated": False,
    }
    write_json(LOCK, result)
    return result


def execute(*, authorize=False):
    if not authorize:
        raise ValueError("Explicit A2 full-data authorization required")
    manifest = json.loads(LOCK.read_text())
    if (
        fp.git("show", "HEAD:" + LOCK.relative_to(ROOT).as_posix(), binary=True)
        != LOCK.read_bytes()
    ):
        raise ValueError("Manifest must be committed before execution")
    if manifest["source_hashes"] != sources() or manifest["config"] != config():
        raise ValueError("A2 implementation/configuration changed")
    for name, digest in manifest["protected_history"]["hashes"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("Protected prior evidence/source changed: " + name)
    output = ROOT / manifest["config"]["full_output"]
    output.mkdir(parents=True, exist_ok=False)
    record = {
        "status": "running",
        "argv": sys.argv,
        "cwd": str(ROOT),
        "launch_commit": fp.git("rev-parse", "HEAD"),
        "manifest_sha256": sha256(LOCK),
        "started_utc": datetime.now(UTC).isoformat(),
        "support": "0.003",
        "next_level_executed": False,
        "scientific_findings_validated": False,
    }
    write_json(output / "checkpoint.json", record)
    record["apriori"] = invoke("apriori", output / "apriori", fixture=False)
    if record["apriori"]["status"] != "passed":
        record.update(status="stopped", fpgrowth_not_run_reason="Apriori failed or incomplete")
    else:
        record["fpgrowth"] = invoke("fpgrowth", output / "fpgrowth", fixture=False)
        record["status"] = "passed" if record["fpgrowth"]["status"] == "passed" else "stopped"
    record["finished_utc"] = datetime.now(UTC).isoformat()
    record["next_0_002_eligible_not_authorized"] = record["status"] == "passed"
    write_json(output / "checkpoint.json", record)
    return record


def export(tests):
    cfg = config()
    output = ROOT / cfg["full_output"]
    record = json.loads((output / "checkpoint.json").read_text())
    target = EVIDENCE / "run"
    target.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(tests, target / "test_results.xml")
    suites = ET.parse(tests).getroot()
    suites = list(suites) if suites.tag == "testsuites" else [suites]
    counts = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")
    }
    if any(counts[k] for k in ("failures", "errors", "skipped")):
        raise ValueError("Post-run tests must all pass with WEKA enabled")
    results, rules = {}, {}
    for algorithm in ALGORITHMS:
        if algorithm in record and record[algorithm]["status"] == "passed":
            native, pool = check_result(
                algorithm,
                output / algorithm,
                n=385288,
                minimum=cfg["minimum_counts"][algorithm],
                support="0.003",
                names=vocabulary(),
            )
            results[algorithm] = {"native": native, "structure": structure(pool)}
            rules[algorithm] = pool
    if rules:
        original, _, _ = pinned_runtime()
        posts, n, empty = read_postings(ROOT / original["input"]["path"], vocabulary())
        if n != 385288 or empty != 117325:
            raise ValueError("Independent population mismatch")
        for a, pool in rules.items():
            results[a]["independent_ARFF_counts"] = independent_count_check(pool, posts)
            results[a]["statin_export"] = export_statin_rules(pool, a, target)
    comparison = compare(rules["apriori"], rules["fpgrowth"], 1156) if len(rules) == 2 else None
    if comparison:
        common = comparison["common_support_comparison"]
        if (
            common["shared_metrics_reconcile"] is False
            or common["apriori_only"]
            or common["fpgrowth_only"]
        ):
            record["next_0_002_eligible_not_authorized"] = False
            record["comparison_requires_review_before_descent"] = True
    record.update(comparison=comparison, results=results, tests=counts)
    write_json(target / "outcome.json", record)
    raw_hashes = {
        p.relative_to(output).as_posix(): sha256(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    with zipfile.ZipFile(target / "raw_output.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in raw_hashes:
            archive.write(output / name, name)
    with zipfile.ZipFile(target / "raw_output.zip") as archive:
        if any(hashlib.sha256(archive.read(k)).hexdigest() != v for k, v in raw_hashes.items()):
            raise ValueError("Archive mismatch")
    write_json(
        target / "evidence_index.json",
        {
            "artifacts": {p.name: sha256(p) for p in target.iterdir() if p.is_file()},
            "raw_output_hashes": raw_hashes,
            "scientific_findings_validated": False,
        },
    )
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    fixture_parser = sub.add_parser("fixture")
    fixture_parser.add_argument("output", type=Path)
    lock_parser = sub.add_parser("lock")
    lock_parser.add_argument("fixture", type=Path)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--authorize-full-data", action="store_true")
    export_parser = sub.add_parser("export")
    export_parser.add_argument("tests", type=Path)
    args = parser.parse_args()
    if args.mode == "fixture":
        result = fixture_checkpoint(args.output)
    elif args.mode == "lock":
        result = lock(args.fixture)
    elif args.mode == "run":
        result = execute(authorize=args.authorize_full_data)
    else:
        result = export(args.tests)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k in {"status", "tests", "comparison"}}, indent=2
        )
    )
    if result["status"] not in {"passed", "locked_before_either_full_data_invocation"}:
        sys.exit(1)
