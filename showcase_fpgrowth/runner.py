"""Only the separately authorized FPGrowth 0.001 task; no ladder or fallback execution."""

import argparse
import csv
import itertools
import json
import math
import os
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from faersight.audit import sha256, write_json
from showcase.inspect import ROOT, pinned_runtime
from showcase.runner import (
    FIXTURE,
    SCHEMA,
    code_hashes,
    fixture_transactions,
    independent_values,
    single_jvm,
    verify_core,
)

BASE = ROOT / "showcase_fpgrowth"
SOURCE = BASE / "java/ShowcaseFPGrowth.java"
CONFIG = BASE / "config.json"
LOCK = ROOT / "artifacts/manifests/weka-showcase-fpgrowth/locked/execution_manifest.json"


def minimum_count(support: str, n: int) -> int:
    s = float(support)
    if not math.isfinite(s) or not 0 < s <= 1 or n < 1:
        raise ValueError("Invalid fractional support/population")
    return math.ceil(s * n)


def options(support="0.001", cap=100000, *, all_rules=True, positive=2, maximum=-1):
    minimum_count(support, 20)
    if type(cap) is not int or cap < 1:
        raise ValueError("Invalid requested count")
    return [
        "-P",
        str(positive),
        "-I",
        str(maximum),
        "-N",
        str(cap),
        "-T",
        "1",
        "-C",
        "1.2",
        "-U",
        "1.0",
        "-M",
        support,
        "-D",
        "1.0",
        *(["-S"] if all_rules else []),
    ]


def source_hashes():
    hashes = {
        p.relative_to(ROOT).as_posix(): sha256(p)
        for p in sorted(BASE.rglob("*"))
        if p.is_file() and p.suffix in {".py", ".java", ".json", ".md"}
    }
    for name in ["record_showcase_fpgrowth.py", "export_showcase_fpgrowth.py"]:
        p = ROOT / "scripts" / name
        hashes[p.relative_to(ROOT).as_posix()] = sha256(p)
    return hashes


def git(*args, binary=False):
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return result if binary else result.decode().strip()


def verify_locked_apriori():
    locked = json.loads(
        (
            ROOT / "artifacts/manifests/weka-showcase-step2a/locked/execution_manifest.json"
        ).read_text()
    )
    if locked["source_hashes"] != code_hashes():
        raise ValueError("Frozen Apriori showcase source/config changed")


def invoke(output, *, arff=FIXTURE, n=20, attributes=4, opts=None, fixture_only=True, export=True):
    output, arff = Path(output), Path(arff)
    if fixture_only and (n > 1000 or attributes > 16 or arff.stat().st_size > 65536):
        raise ValueError("Fixture invocation cannot accept full data")
    config, java, cp = pinned_runtime()
    opts = options("0.1") if opts is None else opts
    output.mkdir(parents=True, exist_ok=False)
    classes = output / "classes"
    classes.mkdir()
    record = {
        "status": "running",
        "started_utc": datetime.now(UTC).isoformat(),
        "mode": "fixture" if fixture_only else "full_data",
        "input_sha256": sha256(arff),
        "source_sha256": sha256(SOURCE),
        "options": opts,
        "runtime": config["runtime"],
        "process_exit_code": None,
        "scientific_findings_validated": False,
    }
    started = time.perf_counter()
    try:
        with single_jvm():
            compile_cmd = [
                str(java.with_name("javac.exe")),
                "-encoding",
                "UTF-8",
                "-cp",
                cp,
                "-d",
                str(classes.resolve()),
                str(SOURCE),
            ]
            record["compile_command"] = compile_cmd
            with (output / "compile.txt").open("wb") as log:
                subprocess.run(
                    compile_cmd, stdout=log, stderr=subprocess.STDOUT, timeout=120, check=True
                )
            command = [
                str(java),
                "-Xmx4g",
                "-XX:ActiveProcessorCount=2",
                "-cp",
                str(classes.resolve()) + os.pathsep + cp,
                "faersight.showcasefp.ShowcaseFPGrowth",
                str(arff.resolve()),
                str(output.resolve()),
                str(n),
                str(attributes),
                str(export).lower(),
                *opts,
            ]
            record["command"] = command
            write_json(output / "invocation.json", record)
            process_started = time.perf_counter()
            with (
                (output / "stdout.txt").open("wb") as stdout,
                (output / "stderr.txt").open("wb") as stderr,
            ):
                with subprocess.Popen(command, stdout=stdout, stderr=stderr) as process:
                    try:
                        record["process_exit_code"] = process.wait(timeout=1800)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        record["process_exit_code"] = process.wait()
                        record["killed_by_runner_after_timeout"] = True
                        raise
                    finally:
                        record["jvm_wall_seconds"] = time.perf_counter() - process_started
            if record["process_exit_code"] != 0:
                raise subprocess.CalledProcessError(record["process_exit_code"], command)
        result = json.loads((output / "run.json").read_text())
        if export and not (output / "complete.txt").is_file():
            raise ValueError("Missing complete export")
        if not fixture_only:
            if not (
                result["tree_build_passes"] == 1
                and result["resolved_lower_count"] == 386
                and result["api_equals_internal_count"]
                and not result["has_nonpresence_items"]
                and result["settings"]["available_processors"] == 2
                and result["settings"]["max_heap_bytes"] == 4294967296
            ):
                raise ValueError("Full-data semantic/completeness check failed")
        record["status"] = "passed"
        if result["rule_policy_limit_reached"]:
            record["status"] = "stop_rule_policy_limit"
    except Exception as exc:
        record["status"] = "failed"
        record["failure_kind"] = (
            "timeout"
            if isinstance(exc, subprocess.TimeoutExpired)
            else (
                "process_failure"
                if isinstance(exc, subprocess.CalledProcessError)
                else "semantic_error"
            )
        )
        record["error"] = str(exc)
        raise
    finally:
        record["total_wall_seconds_including_compile"] = time.perf_counter() - started
        record["finished_utc"] = datetime.now(UTC).isoformat()
        record["hashes"] = {
            p.relative_to(output).as_posix(): sha256(p)
            for p in sorted(output.rglob("*"))
            if p.is_file() and p.name != "invocation.json"
        }
        write_json(output / "invocation.json", record)
    return record


def check_fixture(folder, support="0.1"):
    names, txns = fixture_transactions()
    with (folder / "rules.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == SCHEMA
        rows = list(reader)
    expected = set()
    for assignment in itertools.product((0, 1, 2), repeat=len(names)):
        lhs = tuple(
            sorted(name + "=1" for name, v in zip(names, assignment, strict=True) if v == 1)
        )
        rhs = tuple(
            sorted(name + "=1" for name, v in zip(names, assignment, strict=True) if v == 2)
        )
        if not lhs or not rhs:
            continue
        j, left, right = (sum(set(items) <= txn for txn in txns) for items in (lhs + rhs, lhs, rhs))
        if j >= minimum_count(support, len(txns)) and left and right:
            if independent_values(j, left, right, len(txns))["lift"] >= 1.2:
                expected.add((lhs, rhs))
    seen = set()
    order = []
    for row in rows:
        lhs, rhs = json.loads(row["antecedent"]), json.loads(row["consequent"])
        if lhs != sorted(set(lhs)) or rhs != sorted(set(rhs)) or set(lhs) & set(rhs):
            raise ValueError("Noncanonical/overlapping items")
        if any(i[:-2] not in names or not i.endswith("=1") for i in lhs + rhs):
            raise ValueError("Non-presence rule")
        key = tuple(lhs), tuple(rhs)
        if key in seen:
            raise ValueError("Duplicate rule")
        seen.add(key)
        order.append((row["antecedent"], row["consequent"]))
        j, left, right = (sum(set(items) <= txn for txn in txns) for items in (lhs + rhs, lhs, rhs))
        if [
            int(row[k])
            for k in [
                "joint_count",
                "antecedent_count",
                "consequent_count",
                "n",
                "antecedent_items",
                "consequent_items",
            ]
        ] != [j, left, right, len(txns), len(lhs), len(rhs)]:
            raise ValueError("Independent counts disagree")
        for k, value in independent_values(j, left, right, len(txns)).items():
            if not math.isclose(float(row[k]), value, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"Independent {k} disagrees")
        if row["ranking_metric"].lower() != "lift" or float(row["ranking_value"]) != float(
            row["lift"]
        ):
            raise ValueError("Wrong ranking")
    if seen != expected or order != sorted(order):
        raise ValueError("Exhaustive rule family/canonical order mismatch")
    required = [
        (("DRUG_A=1",), ("REAC_X=1",)),
        (("DRUG_A=1", "DRUG_B=1"), ("REAC_X=1",)),
        (("DRUG_A=1", "REAC_X=1"), ("REAC_Y=1",)),
        (("REAC_X=1",), ("REAC_Y=1",)),
        (("DRUG_A=1",), ("REAC_X=1", "REAC_Y=1")),
    ]
    if not set(required) <= seen:
        raise ValueError("Planned fixture form unavailable")
    return {
        "returned_rules": len(rows),
        "exhaustive_family_matches": True,
        "all_counts_and_four_metrics_match": True,
        "tolerance": 1e-12,
        "required_structures": required,
        "empty_transactions": sum(not t for t in txns),
        "multi_item_consequents": sum(len(rhs) > 1 for _, rhs in seen),
    }


def fixture_checkpoint(output):
    output.mkdir(parents=True, exist_ok=False)
    probes = {}
    for name, opts, export in [
        ("first", options("0.1"), True),
        ("second", options("0.1"), True),
        ("S_N1", options("0.1", 1), True),
        ("iter_N1", options("0.1", 1, all_rules=False), True),
        ("iter_N100000", options("0.1", all_rules=False), True),
        ("rounding", options("0.12"), True),
        ("sparse_P1", options("0.1", positive=1), False),
        ("I2", options("0.1", maximum=2), True),
    ]:
        invoke(output / name, opts=opts, export=export)
        probes[name] = json.loads((output / name / "run.json").read_text())
    check = check_fixture(output / "first")
    check_fixture(output / "rounding", "0.12")
    assert probes["sparse_P1"]["has_nonpresence_items"]
    assert probes["sparse_P1"]["returned_rules"] == 50
    assert probes["first"]["tree_build_passes"] == 1
    assert probes["first"]["resolved_lower_count"] == 2
    assert probes["rounding"]["resolved_lower_count"] == 3
    assert probes["S_N1"]["returned_rules"] == probes["S_N1"]["internal_qualifying_rules"] == 50
    assert probes["iter_N1"]["tree_build_passes"] == 2
    assert probes["iter_N1"]["returned_rules"] == 1
    assert probes["iter_N1"]["internal_qualifying_rules"] == 50
    assert probes["iter_N100000"]["tree_build_passes"] == 2
    assert probes["I2"]["maximum_frequent_itemset_length"] == 2
    assert sha256(output / "first/rules.csv") == sha256(output / "second/rules.csv")
    assert sha256(output / "first/fpgrowth_raw.txt") == sha256(output / "second/fpgrowth_raw.txt")
    result = {
        "status": "passed",
        "new_full_data_run_started": False,
        "fixture_sha256": sha256(FIXTURE),
        "fixture": check,
        "probes": probes,
        "deterministic_export_sha256": sha256(output / "first/rules.csv"),
        "sources": source_hashes(),
        "apriori_source_unchanged": code_hashes(),
        "artifact_hashes": {
            p.relative_to(output).as_posix(): sha256(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    }
    write_json(output / "fixture_result.json", result)
    return result


def lock(fixture, tests):
    verify_locked_apriori()
    core = verify_core()
    if git("status", "--porcelain", "--", "showcase_fpgrowth", "tests/showcase_fpgrowth"):
        raise ValueError("Commit implementation/tests before lock")
    result = json.loads((fixture / "fixture_result.json").read_text())
    assert result["status"] == "passed" and result["sources"] == source_hashes()
    assert all(sha256(fixture / k) == v for k, v in result["artifact_hashes"].items())
    xml = ET.parse(tests).getroot()
    suites = list(xml) if xml.tag == "testsuites" else [xml]
    counts = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")
    }
    assert counts["tests"] >= 113 and not any(counts[k] for k in ("failures", "errors", "skipped"))
    config, java, _ = pinned_runtime()
    assert sha256(ROOT / config["input"]["path"]) == config["input"]["sha256"]
    target = LOCK.parent
    target.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(target / "fixture_evidence.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(fixture.rglob("*")):
            if p.is_file():
                archive.write(p, p.relative_to(fixture).as_posix())
    manifest = {
        "status": "locked_before_fpgrowth_full_data",
        "code_commit": git("rev-parse", "HEAD"),
        "amendment_commit": "23a3a34",
        "source_hashes": source_hashes(),
        "input": config["input"],
        "runtime": config["runtime"],
        "config": json.loads(CONFIG.read_text()),
        "resolved_options": options(),
        "canonical_export_schema": SCHEMA,
        "itemsets": "sorted JSON attribute=1 arrays; rows sorted by lhs then rhs",
        "fixture": result,
        "fixture_archive_sha256": sha256(target / "fixture_evidence.zip"),
        "tests": counts,
        "test_xml_sha256": sha256(tests),
        "core": core,
        "support_count_comparability_limitation": "FPGrowth ceil=386; Apriori round=385",
        "completion": "-S returns all internal rules; -N ignored; normal return plus export",
        "policy": "stop at internal count >=100000 even though -S does not truncate; no retry",
        "processor": "JVM ActiveProcessorCount=2; no associator thread option",
        "java_version": subprocess.run(
            [str(java), "-version"], capture_output=True, timeout=30
        ).stderr.decode(),
        "javac_sha256": sha256(java.with_name("javac.exe")),
        "representative_selection": "first 8 multi-item rules: total length, canonical lhs/rhs",
        "semantics_hashes": {
            p.relative_to(ROOT).as_posix(): sha256(p)
            for p in sorted((LOCK.parent.parent / "semantics").iterdir())
            if p.is_file()
        },
        "fpgrowth_full_data_mining_started": False,
        "scientific_findings_validated": False,
    }
    write_json(LOCK, manifest)
    return manifest


def full_run(manifest_path, *, authorize=False):
    if not authorize:
        raise ValueError("Explicit full-data authorization required")
    if manifest_path.resolve() != LOCK.resolve():
        raise ValueError("Only locked FPGrowth manifest accepted")
    manifest = json.loads(LOCK.read_text())
    if git("show", "HEAD:" + LOCK.relative_to(ROOT).as_posix(), binary=True) != LOCK.read_bytes():
        raise ValueError("Lock must be committed before invocation")
    if manifest["source_hashes"] != source_hashes() or manifest["resolved_options"] != options():
        raise ValueError("Locked implementation/options changed")
    if manifest["config"] != json.loads(CONFIG.read_text()):
        raise ValueError("Config changed")
    verify_locked_apriori()
    verify_core()
    config, _, _ = pinned_runtime()
    if config["input"] != manifest["input"]:
        raise ValueError("Input definition changed")
    arff = ROOT / manifest["input"]["path"]
    if sha256(arff) != manifest["input"]["sha256"]:
        raise ValueError("Input hash mismatch")
    return invoke(
        ROOT / manifest["config"]["full_output"],
        arff=arff,
        n=385288,
        attributes=366,
        opts=options(),
        fixture_only=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    f = sub.add_parser("fixture")
    f.add_argument("output", type=Path)
    locking = sub.add_parser("lock")
    locking.add_argument("fixture", type=Path)
    locking.add_argument("tests", type=Path)
    r = sub.add_parser("run")
    r.add_argument("--execution-manifest", type=Path, required=True)
    r.add_argument("--authorize-full-data", action="store_true")
    args = parser.parse_args()
    if args.mode == "fixture":
        result = fixture_checkpoint(args.output)
    elif args.mode == "lock":
        result = lock(args.fixture, args.tests)
    else:
        result = full_run(args.execution_manifest, authorize=args.authorize_full_data)
    print(json.dumps({k: v for k, v in result.items() if k in {"status", "tests"}}, indent=2))
