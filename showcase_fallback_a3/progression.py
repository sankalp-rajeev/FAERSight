"""Aggregate read-only progression over the three registered levels; no mining."""

import csv
import json

from faersight.audit import sha256, write_json
from showcase.inspect import ROOT

LEVELS = [
    ("0.004", "weka-showcase-fallback-a1-0.004"),
    ("0.003", "weka-showcase-fallback-a2-0.003"),
    ("0.002", "weka-showcase-fallback-a3-0.002"),
]
SCHEMA = [
    "support",
    "algorithm",
    "minimum_count",
    "frequent_itemsets",
    "rule_count",
    "build_seconds",
    "jvm_wall_seconds",
    "maximum_total_rule_size",
    "eligible_statins",
    "statin_singleton_eligibility",
    "statin_containing_rule_count",
    "reaction_only_rule_count",
    "native_jaccard",
    "common_count_jaccard",
    "source_outcome_path",
    "source_outcome_sha256",
    "source_manifest_sha256",
]


def completed_rows(support, outcome, manifest, provenance):
    comparison = outcome.get("comparison") or {}
    native = comparison.get(
        "native_comparison", comparison.get("raw_native_thresholds_not_identical")
    )
    common = comparison.get("common_support_comparison")
    rows = []
    for algorithm in ("apriori", "fpgrowth"):
        invocation = outcome.get(algorithm)
        if not invocation or invocation["status"] != "passed":
            continue
        result = outcome["results"][algorithm]
        metadata = result["native"]
        minimum = manifest["config"]["minimum_counts"][algorithm]
        observed = (
            metadata["minimum_count"]
            if algorithm == "apriori"
            else metadata["resolved_lower_count"]
        )
        if (
            observed != minimum
            or invocation["resolved_minimum_count"] != minimum
            or metadata["rows"] != 385288
            or metadata["attributes"] != 366
        ):
            raise ValueError("Progression source count/population mismatch")
        eligibility = {
            drug: {"count": count, "eligible": count >= minimum}
            for drug, count in manifest["statin_presence_counts"].items()
        }
        rows.append(
            {
                "support": support,
                "algorithm": algorithm,
                "minimum_count": minimum,
                "frequent_itemsets": metadata["frequent_itemsets"],
                "rule_count": metadata["returned_rules"],
                "build_seconds": invocation["association_build_seconds"],
                "jvm_wall_seconds": invocation["jvm_wall_seconds"],
                "maximum_total_rule_size": result["structure"]["maximum_total_size"],
                "eligible_statins": sorted(k for k, v in eligibility.items() if v["eligible"]),
                "statin_singleton_eligibility": eligibility,
                "statin_containing_rule_count": result["structure"]["statin_containing"],
                "reaction_only_rule_count": result["structure"]["reaction_only"],
                "native_jaccard": native["jaccard"] if native else None,
                "common_count_jaccard": common["jaccard"] if common else None,
                **provenance,
            }
        )
    return rows


def timing_notes(rows):
    result = {}
    for algorithm in ("apriori", "fpgrowth"):
        sequence = [r for r in rows if r["algorithm"] == algorithm]
        build = [r["build_seconds"] for r in sequence]
        wall = [r["jvm_wall_seconds"] for r in sequence]
        result[algorithm] = {
            "support_order": [r["support"] for r in sequence],
            "build_seconds": build,
            "jvm_wall_seconds": wall,
            "build_time_nondecreasing_as_support_decreases": all(
                b >= a for a, b in zip(build[:-1], build[1:], strict=True)
            ),
            "jvm_wall_nondecreasing_as_support_decreases": all(
                b >= a for a, b in zip(wall[:-1], wall[1:], strict=True)
            ),
            "limitation": (
                "one observed invocation per level; no extrapolation or universal performance claim"
            ),
        }
    return result


def export_progression(a3_outcome, a3_manifest_path, target):
    rows, statuses, sources = [], {}, {}
    for support, area in LEVELS:
        folder = ROOT / "artifacts/manifests" / area
        manifest_path = folder / "locked/execution_manifest.json"
        if support == "0.002":
            manifest_path = a3_manifest_path
            outcome = a3_outcome
            # Snapshot the mechanically completed outcome before adding progression
            # metadata, avoiding a circular hash in its own provenance.
            path = target / "a3_outcome_before_progression.json"
            write_json(path, a3_outcome)
        else:
            path = folder / "run/outcome.json"
            outcome = json.loads(path.read_text())
        manifest = json.loads(manifest_path.read_text())
        provenance = {
            "source_outcome_path": path.relative_to(ROOT).as_posix(),
            "source_outcome_sha256": sha256(path),
            "source_manifest_sha256": sha256(manifest_path),
        }
        sources[support] = provenance
        statuses[support] = {
            a: outcome.get(a, {}).get("status", "not_attempted") for a in ("apriori", "fpgrowth")
        }
        rows.extend(completed_rows(support, outcome, manifest, provenance))
    report = {
        "registered_supports": [s for s, _ in LEVELS],
        "statuses": statuses,
        "completed_rows": rows,
        "sources": sources,
        "timing_notes": timing_notes(rows),
        "scope": "same pinned PS input, WEKA 3.8.6, fixed options and 4 GiB/1800 s envelope",
        "A1_native_rounding_caveat": "1541 versus 1542; common-count comparison at 1542 retained",
        "further_support_levels": [],
        "scientific_findings_validated": False,
    }
    write_json(target / "support_progression.json", report)
    with (target / "support_progression.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SCHEMA, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, sort_keys=True, separators=(",", ":"))
                    if isinstance(v, (dict, list))
                    else v
                    for k, v in row.items()
                }
            )
    return {
        "completed_algorithm_level_rows": len(rows),
        "files": {
            p.name: sha256(p)
            for p in (target / "support_progression.json", target / "support_progression.csv")
        },
        "timing_notes": report["timing_notes"],
    }
