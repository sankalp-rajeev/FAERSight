"""Isolated Apriori runner. Step 2A invokes inspection and tiny fixtures only."""

import argparse
import csv
import itertools
import json
import math
import os
import shutil
import subprocess
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from faersight.audit import sha256, write_json
from showcase.inspect import ROOT, pinned_runtime

SOURCE = ROOT / "showcase/java/ShowcaseApriori.java"
FIXTURE = ROOT / "showcase/fixtures/semantic.arff"
CONFIG = ROOT / "showcase/config.yaml"
SCHEMA = [
    "antecedent",
    "consequent",
    "antecedent_items",
    "consequent_items",
    "joint_count",
    "antecedent_count",
    "consequent_count",
    "n",
    "support",
    "confidence",
    "lift",
    "leverage",
    "conviction",
    "ranking_metric",
    "ranking_value",
    "weka_rank",
    "requested_support",
    "minimum_metric",
    "rule_cap",
    "resolved_options",
]
FLOAT_TOLERANCE = 1e-12


def minimum_count(support: str | float, n: int) -> int:
    value = float(support)
    if n < 1 or not math.isfinite(value) or not 0 < value <= 1:
        raise ValueError("Invalid support/population")
    return int(max(value, 1 / n) * n + 0.5)


def options(support: str, cap: int = 100000) -> list[str]:
    minimum_count(support, 20)
    if type(cap) is not int or cap < 1:
        raise ValueError("Invalid cap")
    return [
        "-N",
        str(cap),
        "-T",
        "1",
        "-C",
        "1.2",
        "-D",
        "1.0",
        "-U",
        "1.0",
        "-M",
        support,
        "-S",
        "-1.0",
        "-Z",
        "-c",
        "-1",
    ]


def config_checked() -> tuple[dict, Path, str]:
    config, java, classpath = pinned_runtime()
    checks = [
        config["plan_commit"] == "69d27d7",
        config["full_data_authorized"] is False,
        config["input"]
        == {
            "path": "artifacts/generated/2025Q4-statins-mining/input/transactions.arff",
            "sha256": "de0f94f545ebae18033195524984fc842d3359154b864cb52bef2372a877dcf1",
            "rows": 385288,
            "attributes": 366,
            "nominal_values": ["0", "1"],
            "quarters": ["2025Q4"],
            "roles": ["PS"],
        },
        config["apriori"]["support_ladder"]
        == [
            {"fraction": s, "minimum_count": count}
            for s, count in [("0.001", 385), ("0.0005", 193), ("0.0002", 77), ("0.0001", 39)]
        ],
        config["apriori"]["metric"] == "lift",
        config["apriori"]["metric_id"] == 1,
        config["apriori"]["minimum_metric"] == "1.2",
        config["apriori"]["rule_cap"] == 100000,
        config["apriori"]["upper_support"] == config["apriori"]["delta"] == "1.0",
        config["apriori"]["significance_level"] == "-1.0",
        config["apriori"]["treat_zero_as_missing"] is True,
        config["apriori"]["class_rules"] is False,
        config["apriori"]["remove_all_missing_columns"] is False,
        config["apriori"]["print_itemsets"] is False,
        config["apriori"]["verbose"] is False,
        config["apriori"]["class_index_option"] == "-1",
        config["apriori"]["expected_cycles"] == 1,
        config["apriori"]["maximum_itemset_length"] is None,
        config["apriori"]["brute_force_integer_partition_limit"] == 30,
        config["runtime"]["heap"] == "4g",
        config["runtime"]["jvm_active_processor_count"] == 2,
        config["runtime"]["apriori_processor_option"] is None,
        config["runtime"]["timeout_seconds"] == 1800,
        config["runtime"]["concurrent_jvms"] == 1,
        all(config["failure_policy"].values()),
    ]
    if not all(checks):
        raise ValueError("Showcase configuration conflicts with registered plan")
    return config, java, classpath


@contextmanager
def single_jvm():
    """A shared lock covers compilation and invocation; stale locks fail closed."""
    path = ROOT / "artifacts/generated/weka-showcase/.jvm.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, f"pid={os.getpid()}\n".encode())
        os.close(fd)
        fd = None
        yield
    finally:
        if fd is not None:
            os.close(fd)
        path.unlink()


def invoke(
    output: Path,
    *,
    arff: Path | None = None,
    n: int = 0,
    attributes: int = 0,
    support: str = "0.1",
    cap: int = 100000,
    fixture_only: bool = True,
    semantic_probes: bool = False,
) -> dict:
    if (
        arff is not None
        and fixture_only
        and (n > 1000 or attributes > 16 or arff.stat().st_size > 65536)
    ):
        raise ValueError("Fixture invocation cannot read the full-data input")
    config, java, classpath = config_checked()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Showcase output exists; use a new directory")
    output.mkdir(parents=True, exist_ok=True)
    classes = output / "classes"
    classes.mkdir()
    status = {
        "status": "running",
        "mode": "inspection"
        if arff is None
        else "semantic_fixture"
        if fixture_only
        else "full_data",
        "started_utc": datetime.now(UTC).isoformat(),
        "java_source_sha256": sha256(SOURCE),
        "config_sha256": sha256(CONFIG),
        "scientific_findings_validated": False,
    }
    if arff:
        status["input_sha256"] = sha256(arff)
    started = time.monotonic()
    try:
        with single_jvm():
            javac = java.with_name("javac.exe")
            compile_command = [
                str(javac),
                "-encoding",
                "UTF-8",
                "-cp",
                classpath,
                "-d",
                str(classes.resolve()),
                str(SOURCE),
            ]
            with (output / "compile.txt").open("wb") as stream:
                subprocess.run(
                    compile_command,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    timeout=120,
                    check=True,
                )
            command = [
                str(java),
                "-Xmx4g",
                "-XX:ActiveProcessorCount=2",
                "-cp",
                str(classes.resolve()) + os.pathsep + classpath,
                "faersight.showcase.ShowcaseApriori",
            ]
            command += (
                ["probes", str(FIXTURE), str(output.resolve())]
                if semantic_probes
                else ["inspect", str(output.resolve())]
                if arff is None
                else [
                    "mine",
                    str(arff.resolve()),
                    str(output.resolve()),
                    str(n),
                    str(attributes),
                    *options(support, cap),
                ]
            )
            status["compile_command"], status["command"] = compile_command, command
            write_json(output / "invocation.json", status)
            invocation_started = time.monotonic()
            with (output / "process.txt").open("wb") as stream:
                subprocess.run(
                    command,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    timeout=config["runtime"]["timeout_seconds"],
                    check=True,
                )
            status["process_seconds"] = time.monotonic() - invocation_started
        expected = (
            "semantic_probes.json"
            if semantic_probes
            else "runtime_and_options.json"
            if arff is None
            else "complete.txt"
        )
        if not (output / expected).is_file():
            raise ValueError("JVM exited without expected completion artifact")
        if semantic_probes:
            status["status"] = "passed"
        elif arff:
            result = json.loads((output / "run.json").read_text())
            if result["cycles"] != 1 or result["minimum_count"] != minimum_count(support, n):
                raise ValueError("Fixed-support schedule/count mismatch")
            status["rule_cap_reached_or_ambiguous"] = result["rule_cap_reached_or_ambiguous"]
            status["status"] = (
                "stop_cap_ambiguity"
                if result["rule_cap_reached_or_ambiguous"]
                else "stop_integer_partition_limit"
                if result["integer_partition_limit_exceeded"]
                else "passed"
            )
        else:
            audit = json.loads((output / "runtime_and_options.json").read_text())
            if audit["weka_version"] != "3.8.6" or audit["available_processors"] != 2:
                raise ValueError("Pinned WEKA/JVM processor observation changed")
            if audit["max_heap_bytes"] != 4 * 1024**3:
                raise ValueError("JVM did not honor 4 GiB heap")
            status["status"] = "passed"
    except Exception as exc:
        status["status"] = "failed"
        status["error"] = str(exc)
        status["failure_kind"] = (
            "timeout"
            if isinstance(exc, subprocess.TimeoutExpired)
            else "process_failure"
            if isinstance(exc, subprocess.CalledProcessError)
            else "semantic_or_validation_failure"
        )
        if isinstance(exc, subprocess.CalledProcessError):
            status["exit_code"] = exc.returncode
        raise
    finally:
        status["total_seconds_including_compile"] = time.monotonic() - started
        status["finished_utc"] = datetime.now(UTC).isoformat()
        status["artifacts"] = {
            p.relative_to(output).as_posix(): sha256(p)
            for p in sorted(output.rglob("*"))
            if p.is_file() and p.name != "invocation.json"
        }
        write_json(output / "invocation.json", status)
    return status


def fixture_transactions() -> tuple[list[str], list[set[str]]]:
    text = FIXTURE.read_text(encoding="utf-8")
    header, data = text.split("@data", 1)
    names = [line.split()[1] for line in header.splitlines() if line.startswith("@attribute")]
    transactions = []
    for line in data.splitlines():
        if not line.strip():
            continue
        cells = line.strip()[1:-1]
        transactions.append(
            {names[int(cell.split()[0])] + "=1" for cell in cells.split(",") if cell.strip()}
        )
    return names, transactions


def independent_values(joint: int, lhs: int, rhs: int, n: int) -> dict:
    return {
        "support": joint / n,
        "confidence": joint / lhs,
        "lift": (joint / lhs) / (rhs / n),
        "leverage": joint / n - (lhs / n) * (rhs / n),
        # This is the pinned WEKA convention, not unsmoothed textbook conviction.
        "conviction": (lhs * (n - rhs) / n) / (lhs - joint + 1),
    }


def check_fixture(folder: Path, *, support: str = "0.1", cap_expected: bool = False) -> dict:
    names, transactions = fixture_transactions()
    with (folder / "rules.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != SCHEMA:
            raise ValueError("Export schema changed")
        rows = list(reader)
    observed = {}
    canonical_rows = []
    for row in rows:
        lhs, rhs = json.loads(row["antecedent"]), json.loads(row["consequent"])
        if lhs != sorted(set(lhs)) or rhs != sorted(set(rhs)) or not lhs or not rhs:
            raise ValueError("Noncanonical or empty rule side")
        if set(lhs) & set(rhs) or any(not item.endswith("=1") for item in lhs + rhs):
            raise ValueError("Absence-derived or overlapping rule")
        if any(item[:-2] not in names for item in lhs + rhs):
            raise ValueError("Unknown fixture attribute")
        key = tuple(lhs), tuple(rhs)
        if key in observed:
            raise ValueError("Duplicate rule")
        joint = sum(set(lhs + rhs) <= txn for txn in transactions)
        left = sum(set(lhs) <= txn for txn in transactions)
        right = sum(set(rhs) <= txn for txn in transactions)
        if [
            int(row[k])
            for k in (
                "joint_count",
                "antecedent_count",
                "consequent_count",
                "n",
                "antecedent_items",
                "consequent_items",
            )
        ] != [joint, left, right, len(transactions), len(lhs), len(rhs)]:
            raise ValueError("Independent support/itemset counts disagree")
        for name, expected in independent_values(joint, left, right, len(transactions)).items():
            if not math.isclose(
                float(row[name]), expected, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE
            ):
                raise ValueError(f"Independent {name} disagrees")
        if row["ranking_metric"].lower() != "lift" or not math.isclose(
            float(row["ranking_value"]), float(row["lift"]), rel_tol=FLOAT_TOLERANCE
        ):
            raise ValueError("Ranking metric/value disagreement")
        if float(row["lift"]) < 1.2 or joint < minimum_count(support, len(transactions)):
            raise ValueError("Exported rule violates threshold")
        observed[key] = row
        canonical_rows.append((row["antecedent"], row["consequent"]))
    if canonical_rows != sorted(canonical_rows):
        raise ValueError("Export row order is not canonical")
    # Exhaustively check every ordered disjoint nonempty partition independently.
    all_items = [name + "=1" for name in names]
    expected_keys = set()
    for assignment in itertools.product((0, 1, 2), repeat=len(all_items)):
        lhs = tuple(sorted(x for x, side in zip(all_items, assignment, strict=True) if side == 1))
        rhs = tuple(sorted(x for x, side in zip(all_items, assignment, strict=True) if side == 2))
        if not lhs or not rhs:
            continue
        joint = sum(set(lhs + rhs) <= txn for txn in transactions)
        left = sum(set(lhs) <= txn for txn in transactions)
        right = sum(set(rhs) <= txn for txn in transactions)
        if joint >= minimum_count(support, len(transactions)) and left and right:
            if independent_values(joint, left, right, len(transactions))["lift"] >= 1.2:
                expected_keys.add((lhs, rhs))
    if not cap_expected and set(observed) != expected_keys:
        raise ValueError(
            f"Missing/unexpected unrestricted rules: {len(observed)}/{len(expected_keys)}"
        )
    required = [
        (("DRUG_A=1",), ("REAC_X=1",)),
        (("DRUG_A=1", "DRUG_B=1"), ("REAC_X=1",)),
        (("DRUG_A=1", "REAC_X=1"), ("REAC_Y=1",)),
        (("REAC_X=1",), ("REAC_Y=1",)),
        (("DRUG_A=1",), ("REAC_X=1", "REAC_Y=1")),
    ]
    if not cap_expected and not set(required) <= set(observed):
        raise ValueError("Planned rule structure unavailable; document limitation")
    return {
        "rows": len(transactions),
        "empty_transactions": sum(not t for t in transactions),
        "returned_rules": len(observed),
        "independent_qualifying_rules": len(expected_keys),
        "required_structures_recovered": [
            list(map(list, key)) for key in required if key in observed
        ],
        "multi_item_consequents": sum(len(rhs) > 1 for _, rhs in observed),
        "presence_only": True,
        "all_counts_and_four_metrics_match": True,
        "exhaustive_rule_family_matches": set(observed) == expected_keys,
        "tolerance": FLOAT_TOLERANCE,
    }


def fixture_checkpoint(output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Fixture checkpoint exists")
    audit = invoke(output / "options_audit")
    invoke(output / "semantic_probes", semantic_probes=True)
    probes = {
        r["probe"]: r
        for r in json.loads((output / "semantic_probes/semantic_probes.json").read_text())
    }
    if not (
        probes["fixed"]["cycles"] == 1
        and probes["default_delta"]["cycles"] > 1
        and probes["upper_equals_lower"]["returned_rules"] == 0
        and probes["without_Z"]["has_zero_items"]
        and not probes["fixed"]["has_zero_items"]
    ):
        raise ValueError("Semantic behavior probes differ from inspected bytecode")
    results = []
    for name in ("first", "second"):
        status = invoke(output / name, arff=FIXTURE, n=20, attributes=4)
        if status["status"] != "passed":
            raise ValueError("Fixture failed or reached cap")
        results.append(check_fixture(output / name))
    if sha256(output / "first/rules.csv") != sha256(output / "second/rules.csv"):
        raise ValueError("Canonical export differs across independent JVM runs")
    if (output / "first/apriori_raw.txt").read_bytes() != (
        output / "second/apriori_raw.txt"
    ).read_bytes():
        raise ValueError("Raw fixture output differs")
    cap = invoke(output / "cap_probe", arff=FIXTURE, n=20, attributes=4, cap=1)
    cap_check = check_fixture(output / "cap_probe", cap_expected=True)
    if cap["status"] != "stop_cap_ambiguity" or cap_check["returned_rules"] != 1:
        raise ValueError("Cap detection probe failed")
    # Fraction .12 * 20 = 2.4 must round to 2, rather than ceil to 3.
    rounding = invoke(output / "rounding_probe", arff=FIXTURE, n=20, attributes=4, support="0.12")
    if rounding["status"] != "passed":
        raise ValueError("Rounding probe failed")
    check_fixture(output / "rounding_probe", support="0.12")
    result = {
        "status": "passed",
        "full_data_mining_started": False,
        "fixture_sha256": sha256(FIXTURE),
        "fixture": results[0],
        "two_independent_jvms_identical": True,
        "canonical_export_sha256": sha256(output / "first/rules.csv"),
        "cap_probe_returned": 1,
        "cap_probe_status": cap["status"],
        "rounding_probe_count": 2,
        "runtime_options_audit": audit["status"],
        "semantic_probes": probes,
        "scientific_findings_validated": False,
        "artifacts": {
            p.relative_to(output).as_posix(): sha256(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    }
    write_json(output / "fixture_result.json", result)
    return result


def code_hashes() -> dict[str, str]:
    return {
        p.relative_to(ROOT).as_posix(): sha256(p)
        for p in sorted((ROOT / "showcase").rglob("*"))
        if p.is_file() and p.suffix in {".py", ".java", ".yaml", ".arff"}
    }


def verify_core() -> dict:
    """Compare every tracked frozen core file byte-for-byte with the plan commit."""
    import hashlib

    git = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
    folders = [
        "config",
        "benchmarks",
        "mappings",
        "src/faersight",
        "artifacts/manifests/2025Q4-statins",
        "artifacts/manifests/2025Q4-statins-mining",
        "artifacts/manifests/2025Q4-statins-sensitivity",
    ]
    names = subprocess.run(
        [*git, "ls-tree", "-r", "--name-only", "69d27d7", "--", *folders],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    for name in names:
        original = subprocess.run(
            [*git, "show", "69d27d7:" + name], cwd=ROOT, capture_output=True, check=True
        ).stdout
        if hashlib.sha256(original).hexdigest() != sha256(ROOT / name):
            raise ValueError(f"Frozen core file changed: {name}")
    return {
        "plan_commit": "69d27d7",
        "tracked_frozen_files_verified": len(names),
        "all_match_committed_bytes": True,
    }


def lock_checkpoint(fixture: Path, semantics: Path, output: Path, tests: Path) -> dict:
    """Lock metadata/hashes only. Never pass the full ARFF to a JVM here."""
    import xml.etree.ElementTree as ET

    config, java, _ = config_checked()
    protected = verify_core()
    if (ROOT / "artifacts/generated/weka-showcase/full").exists():
        raise ValueError("Unexpected full-data showcase output directory")
    fixture_result = json.loads((fixture / "fixture_result.json").read_text())
    if fixture_result["status"] != "passed" or fixture_result["full_data_mining_started"]:
        raise ValueError("Fixture checkpoint is not passed/isolated")
    for name, digest in fixture_result["artifacts"].items():
        path = (fixture / name).resolve()
        if not path.is_relative_to(fixture.resolve()) or sha256(path) != digest:
            raise ValueError("Fixture artifact changed")
    if fixture_result["fixture_sha256"] != sha256(FIXTURE):
        raise ValueError("Fixture source changed")
    for folder in fixture.iterdir():
        invocation = folder / "invocation.json"
        if invocation.is_file():
            record = json.loads(invocation.read_text())
            if record["java_source_sha256"] != sha256(SOURCE) or record["config_sha256"] != sha256(
                CONFIG
            ):
                raise ValueError("Fixture was not executed with current source/config")
    inspection = json.loads((semantics / "inspection_manifest.json").read_text())
    for name, digest in inspection["artifacts"].items():
        if sha256(semantics / name) != digest:
            raise ValueError("Pinned inspection evidence changed")
    audit = json.loads((fixture / "options_audit/runtime_and_options.json").read_text())
    for entry, actual in zip(
        config["apriori"]["support_ladder"], audit["resolved_ladder"], strict=True
    ):
        if actual["minimum_count_at_385288"] != entry["minimum_count"]:
            raise ValueError("Integer cutoff audit differs from locked settings")
    full_input = ROOT / config["input"]["path"]
    if sha256(full_input) != config["input"]["sha256"]:
        raise ValueError("Full input hash differs from frozen primary ARFF")
    git = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
    commit = subprocess.run(
        [*git, "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = subprocess.run(
        [*git, "status", "--porcelain", "--", "showcase", "tests/showcase"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if dirty:
        raise ValueError("Commit showcase code/config/tests before locking its execution manifest")
    xml = ET.parse(tests).getroot()
    suites = list(xml) if xml.tag == "testsuites" else [xml]
    counts = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "errors", "failures", "skipped")
    }
    if any(counts[k] for k in ("errors", "failures", "skipped")):
        raise ValueError("All core/showcase tests must pass with actual WEKA enabled")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Locked evidence exists")
    output.mkdir(parents=True, exist_ok=True)
    for path in sorted(fixture.rglob("*")):
        if path.is_file() and path.suffix != ".class":
            destination = output / "fixture" / path.relative_to(fixture)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
    # Hashes refer to the original generated fixture snapshot, including class bytes.
    # The exported subset is separately indexed and contains no full-data results.
    result = {
        "schema_version": 1,
        "status": "step2a_prerequisites_locked_and_validated",
        "code_commit": commit,
        "source_hashes": code_hashes(),
        "config_sha256": sha256(CONFIG),
        "plan_commit": "69d27d7",
        "locked_utc": datetime.now(UTC).isoformat(),
        "input": {
            **config["input"],
            "absolute_path": str(full_input.resolve()),
            "verification": "sha256_only_not_loaded_by_WEKA",
        },
        "runtime": {
            **config["runtime"],
            "java_version": audit["java_version"],
            "javac_sha256": sha256(java.with_name("javac.exe")),
            "observed_available_processors": audit["available_processors"],
            "observed_heap_bytes": audit["max_heap_bytes"],
        },
        "verified_defaults": audit["defaults"],
        "metric_identifiers": audit["metric_identifiers"],
        "apriori": config["apriori"],
        "resolved_options": audit["resolved_ladder"],
        "failure_policy": config["failure_policy"],
        "canonical_export": {**config["export"], "columns": SCHEMA},
        "fixture": {
            "source_hash": sha256(FIXTURE),
            "result": fixture_result,
            "generated_snapshot": str(fixture.resolve()),
        },
        "inspection_manifest_sha256": sha256(semantics / "inspection_manifest.json"),
        "tests": {
            **counts,
            "passed": counts["tests"],
            "actual_weka_enabled": True,
            "junit_sha256": sha256(tests),
        },
        "core_preservation": protected,
        "full_data_mining_started": False,
        "full_data_execution_authorized": False,
        "scientific_findings_validated": False,
        "first_full_command": ".venv/Scripts/python -m showcase.runner run "
        "--execution-manifest "
        "artifacts/manifests/weka-showcase-step2a/locked/execution_manifest.json "
        "--support 0.001 --output artifacts/generated/weka-showcase/full/0.001 "
        "--authorize-full-data",
    }
    write_json(output / "execution_manifest.json", result)
    write_json(
        output / "evidence_index.json",
        {
            "full_data_mining_started": False,
            "scientific_findings_validated": False,
            "artifacts": {
                p.relative_to(output).as_posix(): sha256(p)
                for p in sorted(output.rglob("*"))
                if p.is_file()
            },
        },
    )
    return result


def full_run(manifest_path: Path, output: Path, support: str, *, authorized: bool = False) -> dict:
    """One future full-data invocation only, requiring explicit human continuation."""
    if not authorized:
        raise ValueError("Full-data execution requires explicit --authorize-full-data")
    config, _, _ = config_checked()
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest["status"] != "step2a_prerequisites_locked_and_validated"
        or manifest["config_sha256"] != sha256(CONFIG)
        or manifest["source_hashes"] != code_hashes()
    ):
        raise ValueError("Execution manifest does not lock the current source/config")
    ladder = [r["fraction"] for r in config["apriori"]["support_ladder"]]
    if support not in ladder:
        raise ValueError("Support is outside the registered ladder")
    expected_output = ROOT / "artifacts/generated/weka-showcase/full" / support
    if output.resolve() != expected_output.resolve():
        raise ValueError("Use the registered showcase output path; do not bypass stop history")
    # Every lower support must have a completed, nontruncated predecessor snapshot.
    # A partial/failed predecessor, or any prior stop, fails this gate.
    for earlier in ladder[: ladder.index(support)]:
        previous = output.parent / earlier / "invocation.json"
        if not previous.is_file() or json.loads(previous.read_text())["status"] != "passed":
            raise ValueError("Ladder predecessor absent, failed, or stopped; do not descend")
    verify_core()
    path = ROOT / config["input"]["path"]
    if sha256(path) != config["input"]["sha256"]:
        raise ValueError("Full input hash changed")
    return invoke(
        output, arff=path, n=385288, attributes=366, support=support, cap=100000, fixture_only=False
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fixture = sub.add_parser("fixture")
    fixture.add_argument("--output", type=Path, required=True)
    lock = sub.add_parser("lock")
    lock.add_argument("--fixture", type=Path, required=True)
    lock.add_argument("--semantics", type=Path, required=True)
    lock.add_argument("--output", type=Path, required=True)
    lock.add_argument("--tests", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--execution-manifest", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--support", required=True)
    run.add_argument("--authorize-full-data", action="store_true")
    args = parser.parse_args()
    if args.command == "fixture":
        result = fixture_checkpoint(args.output)
    elif args.command == "lock":
        result = lock_checkpoint(args.fixture, args.semantics, args.output, args.tests)
    else:
        result = full_run(
            args.execution_manifest, args.output, args.support, authorized=args.authorize_full_data
        )
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k in {"status", "fixture", "code_commit", "full_data_mining_started"}
            },
            indent=2,
        )
    )
    if args.command == "run" and result["status"] != "passed":
        parser.exit(2, "Registered stop condition reached; preserve output and do not descend.\n")


if __name__ == "__main__":
    main()
