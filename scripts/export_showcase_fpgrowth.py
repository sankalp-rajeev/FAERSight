"""Aggregate-only mechanical export; this script never invokes mining."""

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faersight.audit import sha256, write_json  # noqa: E402
from scripts.export_showcase_step2b import count_items, signature  # noqa: E402
from showcase.runner import independent_values, verify_core  # noqa: E402
from showcase_fpgrowth.runner import verify_locked_apriori  # noqa: E402


def analyze(source, target):
    import duckdb

    run = json.loads((source / "run.json").read_text())
    if run["rule_policy_limit_reached"] or not run["api_equals_internal_count"]:
        raise ValueError("No complete below-policy-limit model")
    with (source / "rules.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    vocabulary = set(
        json.loads(
            (ROOT / "artifacts/manifests/2025Q4-statins-mining/arff_manifest.json").read_text()
        )["attributes"]
    )
    sigs = Counter()
    seen, order, multi = set(), [], []
    maxima = [0, 0, 0]
    for row in rows:
        lhs, rhs = json.loads(row["antecedent"]), json.loads(row["consequent"])
        key = row["antecedent"], row["consequent"]
        assert key not in seen and lhs and rhs and not set(lhs) & set(rhs)
        assert lhs == sorted(set(lhs)) and rhs == sorted(set(rhs))
        assert all(i.endswith("=1") and i[:-2] in vocabulary for i in lhs + rhs)
        seen.add(key)
        order.append(key)
        j, left, right, n = (
            int(row[k]) for k in ("joint_count", "antecedent_count", "consequent_count", "n")
        )
        assert n == 385288 and 386 <= j <= min(left, right) <= n and n - left - right + j >= 0
        assert int(row["antecedent_items"]) == len(lhs) and int(row["consequent_items"]) == len(rhs)
        for metric, expected in independent_values(j, left, right, n).items():
            assert math.isclose(float(row[metric]), expected, rel_tol=1e-12, abs_tol=1e-12)
        assert row["ranking_metric"].lower() == "lift" and float(row["lift"]) >= 1.2
        assert float(row["requested_support"]) == 0.001 and int(row["rule_cap"]) == 100000
        assert float(row["ranking_value"]) == float(row["lift"])
        sigs[signature(lhs, rhs)] += 1
        maxima = [max(maxima[i], v) for i, v in enumerate((len(lhs), len(rhs), len(lhs + rhs)))]
        if len(lhs + rhs) > 2:
            multi.append(row)
    assert order == sorted(order) and len(rows) == run["returned_rules"]
    # Locked before full mining: shortest total length, then canonical lhs/rhs;
    # first eight, without scoring or interpretation-based selection.
    reps = sorted(
        multi,
        key=lambda r: (
            int(r["antecedent_items"]) + int(r["consequent_items"]),
            r["antecedent"],
            r["consequent"],
        ),
    )[:8]
    db = ROOT / "data/processed/2025Q4-statins/analytical.duckdb"
    assert sha256(db) == "2255f30a4b903d9b4ab09c258491e9f1ecc67e2edacf40fee8c1d51f7489a2ce"
    with duckdb.connect(str(db), read_only=True) as con:
        for row in reps:
            lhs, rhs = json.loads(row["antecedent"]), json.loads(row["consequent"])
            assert [count_items(con, items) for items in (lhs + rhs, lhs, rhs)] == [
                int(row[k]) for k in ("joint_count", "antecedent_count", "consequent_count")
            ]
    result = {
        "returned_rules": len(rows),
        "maximum_antecedent_size": maxima[0],
        "maximum_consequent_size": maxima[1],
        "maximum_total_rule_size": maxima[2],
        "structural_counts": {
            "single_statin_to_single_reaction": sigs[(1, 0, 0, 1)],
            "two_statins_to_single_reaction": sigs[(2, 0, 0, 1)],
            "statin_plus_one_reaction_to_single_reaction": sigs[(1, 1, 0, 1)],
            "single_reaction_to_single_reaction": sigs[(0, 1, 0, 1)],
            "multi_item_consequent": sum(v for k, v in sigs.items() if k[2] + k[3] > 1),
            "reaction_only_to_reaction_only": sum(v for k, v in sigs.items() if k[0] == k[2] == 0),
        },
        "exhaustive_signature_histogram_lhs_drug_reaction_rhs_drug_reaction": {
            str(k): v for k, v in sorted(sigs.items())
        },
        "representative_selection": "first 8 by total length then canonical lhs then rhs",
        "representatives": reps,
        "representative_counts_independently_verified": True,
        "causal_interpretation": False,
    }
    write_json(target / "mechanical_summary.json", result)
    return result


def export(tests):
    source = ROOT / "artifacts/generated/weka-showcase-fpgrowth/full/0.001"
    capture = ROOT / "artifacts/generated/weka-showcase-fpgrowth/capture-0.001"
    target = ROOT / "artifacts/manifests/weka-showcase-fpgrowth/run-0.001"
    target.mkdir(parents=True, exist_ok=False)
    record = json.loads((capture / "command_record.json").read_text())
    invocation = json.loads((source / "invocation.json").read_text())
    for p in capture.iterdir():
        if p.is_file():
            shutil.copyfile(p, target / ("capture_" + p.name))
    for name in [
        "invocation.json",
        "stdout.txt",
        "stderr.txt",
        "compile.txt",
        "resolved_options.json",
        "run.json",
    ]:
        if (source / name).exists():
            shutil.copyfile(source / name, target / name)
    with zipfile.ZipFile(target / "raw_output.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(source.rglob("*")):
            if p.is_file():
                archive.write(p, p.relative_to(source).as_posix())
    with zipfile.ZipFile(target / "raw_output.zip") as archive:
        assert set(archive.namelist()) == set(record["raw_output_hashes"])
        assert all(
            hashlib.sha256(archive.read(k)).hexdigest() == v
            for k, v in record["raw_output_hashes"].items()
        )
    successful = record["status"] == "passed" and invocation["status"] == "passed"
    summary = analyze(source, target) if successful else None
    suites = ET.parse(tests).getroot()
    suites = list(suites) if suites.tag == "testsuites" else [suites]
    counts = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")
    }
    assert not any(counts[k] for k in ("failures", "errors", "skipped"))
    shutil.copyfile(tests, target / "test_results.xml")
    verify_locked_apriori()
    outcome = {
        "status": record["status"],
        "invocation_status": invocation["status"],
        "cli_exit_code": record["cli_exit_code"],
        "java_exit_code": invocation["process_exit_code"],
        "failure_kind": invocation.get("failure_kind"),
        "total_command_wall_seconds": record["total_command_wall_seconds"],
        "jvm_wall_seconds": invocation.get("jvm_wall_seconds"),
        "build_seconds": json.loads((source / "run.json").read_text())["association_build_seconds"]
        if successful
        else None,
        "resolved_support_count": 386,
        "apriori_count": 385,
        "N_is_cap": False,
        "returned_rule_count": summary["returned_rules"] if summary else None,
        "mechanical_summary": summary,
        "fallback_a_eligible_separate_authorization_required": True,
        "fallback_b_eligible_separate_authorization_required": not successful,
        "lower_supports_fallbacks_metrics_explorer_executed": False,
        "internal_failure_cause_established": False,
        "rule_overlap_with_apriori": None,
        "tests": counts,
        "core": verify_core(),
        "scientific_findings_validated": False,
    }
    write_json(target / "outcome.json", outcome)
    write_json(
        target / "evidence_index.json",
        {
            "artifacts": {p.name: sha256(p) for p in sorted(target.iterdir()) if p.is_file()},
            "raw_output_hashes": record["raw_output_hashes"],
            "core": outcome["core"],
            "status": outcome["status"],
            "scientific_findings_validated": False,
        },
    )
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tests", type=Path)
    export(parser.parse_args().tests)
