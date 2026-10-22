"""Mechanical evidence export for the authorized 0.001 run; no mining invocation."""

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faersight.audit import sha256, write_json  # noqa: E402
from showcase.runner import FLOAT_TOLERANCE, independent_values, verify_core  # noqa: E402


def signature(lhs: list[str], rhs: list[str]) -> tuple[int, int, int, int]:
    return (
        sum(i.startswith("DRUG_") for i in lhs),
        sum(i.startswith("REAC_") for i in lhs),
        sum(i.startswith("DRUG_") for i in rhs),
        sum(i.startswith("REAC_") for i in rhs),
    )


def count_items(connection, items: list[str]) -> int:
    names = [item[:-2] for item in items]
    placeholders = ",".join("?" for _ in names)
    return connection.execute(
        f"""
        SELECT count(*) FROM (SELECT case_id FROM case_items
        WHERE item_type || '_' || item_value IN ({placeholders})
        GROUP BY case_id HAVING count(*)=?)
    """,
        [*names, len(names)],
    ).fetchone()[0]


def analyze(source: Path, output: Path) -> dict:
    run = json.loads((source / "run.json").read_text())
    if run["rule_cap_reached_or_ambiguous"] or run["integer_partition_limit_exceeded"]:
        raise ValueError("Mechanical rule analysis is restricted to a passed below-cap run")
    with (source / "rules.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    vocabulary = set(
        json.loads(
            (ROOT / "artifacts/manifests/2025Q4-statins-mining/arff_manifest.json").read_text()
        )["attributes"]
    )
    categories = Counter(
        {
            k: 0
            for k in (
                "single_statin_to_single_reaction",
                "two_statins_to_single_reaction",
                "statin_plus_one_reaction_to_single_reaction",
                "single_reaction_to_single_reaction",
                "multi_item_consequent",
                "reaction_only_to_reaction_only",
                "multi_reaction_antecedent_to_single_reaction",
            )
        }
    )
    signatures = Counter()
    examples = defaultdict(list)
    seen = set()
    ordering = []
    maximum_lhs = maximum_rhs = maximum_total = 0
    for row in rows:
        lhs, rhs = json.loads(row["antecedent"]), json.loads(row["consequent"])
        key = row["antecedent"], row["consequent"]
        if key in seen or not lhs or not rhs or set(lhs) & set(rhs):
            raise ValueError("Duplicate, empty or overlapping rule")
        if lhs != sorted(set(lhs)) or rhs != sorted(set(rhs)):
            raise ValueError("Noncanonical itemset")
        if any(not i.endswith("=1") or i[:-2] not in vocabulary for i in lhs + rhs):
            raise ValueError("Absence-derived or unregistered attribute")
        seen.add(key)
        ordering.append(key)
        joint, left, right, n = (
            int(row[k]) for k in ("joint_count", "antecedent_count", "consequent_count", "n")
        )
        if not (
            n == 385288 and 385 <= joint <= min(left, right) <= n and n - left - right + joint >= 0
        ):
            raise ValueError("Invalid counts/population/support")
        if int(row["antecedent_items"]) != len(lhs) or int(row["consequent_items"]) != len(rhs):
            raise ValueError("Side lengths disagree with complete itemsets")
        for metric, value in independent_values(joint, left, right, n).items():
            if not math.isclose(
                float(row[metric]), value, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE
            ):
                raise ValueError(f"Count-derived {metric} disagreement")
        if (
            row["ranking_metric"].lower() != "lift"
            or float(row["lift"]) < 1.2
            or float(row["requested_support"]) != 0.001
            or int(row["rule_cap"]) != 100000
            or not math.isclose(
                float(row["ranking_value"]), float(row["lift"]), rel_tol=FLOAT_TOLERANCE
            )
        ):
            raise ValueError("Registered metric/options mismatch")
        sig = signature(lhs, rhs)
        signatures[sig] += 1
        categories["single_statin_to_single_reaction"] += sig == (1, 0, 0, 1)
        categories["two_statins_to_single_reaction"] += sig == (2, 0, 0, 1)
        categories["statin_plus_one_reaction_to_single_reaction"] += sig == (1, 1, 0, 1)
        categories["single_reaction_to_single_reaction"] += sig == (0, 1, 0, 1)
        categories["multi_item_consequent"] += len(rhs) > 1
        categories["reaction_only_to_reaction_only"] += sig[0] == sig[2] == 0
        categories["multi_reaction_antecedent_to_single_reaction"] += (
            sig[0] == sig[2] == 0 and sig[1] > 1 and sig[3] == 1
        )
        maximum_lhs, maximum_rhs = max(maximum_lhs, len(lhs)), max(maximum_rhs, len(rhs))
        maximum_total = max(maximum_total, len(lhs) + len(rhs))
        if len(lhs) + len(rhs) >= 3:
            examples[sig].append(row)
    if len(rows) != run["returned_rules"] or ordering != sorted(ordering):
        raise ValueError("Returned-rule count or canonical row order mismatch")
    # Predefined deterministic selection: structural coverage, shortest rules first,
    # then numeric signature; round-robin canonical rows within each signature.
    groups = sorted(examples, key=lambda sig: (sum(sig), sig))
    selected = []
    for offset in range(8):
        for sig in groups:
            if offset < len(examples[sig]):
                selected.append(
                    {
                        "selection_order": len(selected) + 1,
                        "structure": str(sig),
                        **examples[sig][offset],
                    }
                )
                if len(selected) == 8:
                    break
        if len(selected) == 8:
            break
    if selected:
        import duckdb

        with duckdb.connect(
            str(ROOT / "data/processed/2025Q4-statins/analytical.duckdb"), read_only=True
        ) as connection:
            for row in selected:
                lhs, rhs = json.loads(row["antecedent"]), json.loads(row["consequent"])
                expected = (
                    count_items(connection, lhs + rhs),
                    count_items(connection, lhs),
                    count_items(connection, rhs),
                )
                if expected != tuple(
                    int(row[k]) for k in ("joint_count", "antecedent_count", "consequent_count")
                ):
                    raise ValueError("Representative rule counts disagree with frozen primary mart")
                row["independent_mart_counts_match"] = True
        with (output / "representative_rules.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=list(selected[0]))
            writer.writeheader()
            writer.writerows(selected)
    structures = [
        {"lhs_statins": a, "lhs_reactions": b, "rhs_statins": c, "rhs_reactions": d, "rules": count}
        for (a, b, c, d), count in sorted(signatures.items())
    ]
    result = {
        "returned_rules": len(rows),
        "maximum_antecedent_items": maximum_lhs,
        "maximum_consequent_items": maximum_rhs,
        "maximum_total_rule_items": maximum_total,
        "categories": dict(categories),
        "category_counts_overlap": True,
        "disjoint_structure_signatures": structures,
        "selection_policy": (
            "multi-item rules only; sort signatures by total length then numeric signature; "
            "round-robin canonical antecedent/consequent rows; first eight"
        ),
        "representatives": selected,
        "all_exported_counts_and_metrics_reconcile": True,
        "representative_counts_independently_match_primary_mart": bool(selected),
        "scientific_interpretation_performed": False,
        "scientific_findings_validated": False,
    }
    write_json(output / "mechanical_summary.json", result)
    return result


def export(source: Path, capture: Path, output: Path, tests: Path) -> dict:
    if output.exists():
        raise ValueError("Evidence snapshot exists")
    record = json.loads((capture / "command_record.json").read_text())
    if record["status"] not in {"passed", "stopped"}:
        raise ValueError("The single recorded attempt is not complete")
    if record["authorized_support_only"] != "0.001":
        raise ValueError("Only support 0.001 is authorized for this checkpoint")
    for name, digest in record["raw_output_hashes"].items():
        if sha256(source / name) != digest:
            raise ValueError("Raw output changed after the recorded invocation")
    output.mkdir(parents=True)
    for name in (
        "invocation.json",
        "run.json",
        "resolved_options.json",
        "complete.txt",
        "process.txt",
        "compile.txt",
    ):
        if (source / name).is_file():
            shutil.copyfile(source / name, output / name)
    for path in capture.iterdir():
        if path.is_file():
            shutil.copyfile(path, output / ("capture_" + path.name))
    summary = analyze(source, output) if record["status"] == "passed" else None
    invocation = json.loads((source / "invocation.json").read_text())
    run = json.loads((source / "run.json").read_text()) if (source / "run.json").is_file() else {}
    write_json(
        output / "run_outcome.json",
        {
            "completed_successfully": record["status"] == "passed",
            "status": record["runner_status"],
            "failure_kind": invocation.get("failure_kind"),
            "runner_exit_code": record["exit_code"],
            "java_exit_code_if_recorded": invocation.get("exit_code"),
            "total_command_wall_seconds": record["total_command_wall_seconds"],
            "java_process_seconds_if_recorded": invocation.get("process_seconds"),
            "association_build_seconds": run.get("association_build_seconds"),
            "requested_support": "0.001",
            "locked_minimum_count": 385,
            "weka_reported_support": run.get("support_used"),
            "weka_reported_minimum_count": run.get("minimum_count"),
            "returned_rules": run.get("returned_rules"),
            "requested_rule_cap": 100000,
            "rule_cap_reached_or_ambiguous": run.get("rule_cap_reached_or_ambiguous"),
            "integer_partition_limit_exceeded": run.get("integer_partition_limit_exceeded"),
            "maximum_frequent_itemset_length": run.get("maximum_frequent_itemset_length"),
            "maximum_antecedent_items": summary["maximum_antecedent_items"] if summary else None,
            "maximum_consequent_items": summary["maximum_consequent_items"] if summary else None,
            "maximum_total_rule_items": summary["maximum_total_rule_items"] if summary else None,
            "structural_categories": summary["categories"] if summary else None,
            "mechanical_analysis_performed": summary is not None,
            "analysis_skipped_reason": None if summary else "no_successful_below_cap_export",
            "next_support_0_0005_gate": "requires_separate_explicit_authorization"
            if summary
            else "blocked_by_registered_stop_rule_no_retry_or_descent",
            "scientific_findings_validated": False,
        },
    )
    with zipfile.ZipFile(output / "raw_output.zip", "w") as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                entry = zipfile.ZipInfo(
                    path.relative_to(source).as_posix(), date_time=(1980, 1, 1, 0, 0, 0)
                )
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes())
    with zipfile.ZipFile(output / "raw_output.zip") as archive:
        for name, digest in record["raw_output_hashes"].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError("Archived raw output hash mismatch")
    xml = ET.parse(tests).getroot()
    suites = list(xml) if xml.tag == "testsuites" else [xml]
    test_counts = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")
    }
    write_json(
        output / "test_results.json",
        {**test_counts, "junit_sha256": sha256(tests), "actual_weka_enabled": True},
    )
    result = {
        "status": record["status"],
        "authorized_support_only": "0.001",
        "full_data_mining_started": True,
        "full_data_mining_completed": record["status"] == "passed",
        "raw_output_location": str(source.resolve()),
        "core_preservation": verify_core(),
        "raw_output_hashes": record["raw_output_hashes"],
        "total_command_wall_seconds": record["total_command_wall_seconds"],
        "exit_code": record["exit_code"],
        "mechanical_analysis_performed": summary is not None,
        "lower_supports_run": False,
        "later_showcase_steps_run": False,
        "scientific_findings_validated": False,
        "artifacts": {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    write_json(output / "evidence_index.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=ROOT / "artifacts/generated/weka-showcase/full/0.001"
    )
    parser.add_argument(
        "--capture",
        type=Path,
        default=ROOT / "artifacts/generated/weka-showcase/step2b-0.001-capture",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "artifacts/manifests/weka-showcase-step2b-0.001"
    )
    parser.add_argument("--tests", type=Path, required=True)
    args = parser.parse_args()
    result = export(args.source, args.capture, args.output, args.tests)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in {"artifacts", "raw_output_hashes"}},
            indent=2,
        )
    )
