"""Canonical, finite-metric comparisons; no ranking experiments or clinical claims."""

import csv
import json
import math
from collections import Counter
from pathlib import Path

from showcase.runner import SCHEMA, independent_values

METRICS = ["support", "confidence", "lift", "leverage", "conviction"]
TOLERANCE = 1e-12


def read_rules(folder: Path, *, n: int, minimum_count: int, support: str, vocabulary: set):
    with (folder / "rules.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != SCHEMA:
            raise ValueError("Unexpected canonical export schema")
        rows = list(reader)
    result, order = {}, []
    for row in rows:
        lhs, rhs = json.loads(row["antecedent"]), json.loads(row["consequent"])
        if not lhs or not rhs or lhs != sorted(set(lhs)) or rhs != sorted(set(rhs)):
            raise ValueError("Noncanonical/empty itemset")
        if set(lhs) & set(rhs) or any(
            i not in vocabulary or not i.endswith("=1") for i in lhs + rhs
        ):
            raise ValueError("Unknown, absence-derived or overlapping items")
        key = tuple(lhs), tuple(rhs)
        if key in result:
            raise ValueError("Duplicate rule")
        joint, left, right, total = (
            int(row[k]) for k in ("joint_count", "antecedent_count", "consequent_count", "n")
        )
        if not (
            total == n
            and minimum_count <= joint <= min(left, right) <= n
            and n - left - right + joint >= 0
        ):
            raise ValueError("Invalid support/population counts")
        if int(row["antecedent_items"]) != len(lhs) or int(row["consequent_items"]) != len(rhs):
            raise ValueError("Item count mismatch")
        for metric, expected in independent_values(joint, left, right, n).items():
            value = float(row[metric])
            if not math.isfinite(value) or not math.isclose(
                value, expected, rel_tol=TOLERANCE, abs_tol=TOLERANCE
            ):
                raise ValueError("Nonfinite or count-inconsistent " + metric)
        if (
            row["ranking_metric"].lower() != "lift"
            or float(row["lift"]) < 1.2
            or float(row["requested_support"]) != float(support)
            or int(row["rule_cap"]) != 100000
            or float(row["ranking_value"]) != float(row["lift"])
        ):
            raise ValueError("Metric/threshold/configuration mismatch")
        result[key] = row
        order.append((row["antecedent"], row["consequent"]))
    if order != sorted(order):
        raise ValueError("Noncanonical export row order")
    return result


def structure(rules):
    hist = Counter((len(lhs), len(rhs)) for lhs, rhs in rules)
    reaction_rules = [
        (lhs, rhs) for lhs, rhs in rules if all(i.startswith("REAC_") for i in lhs + rhs)
    ]
    return {
        "rules": len(rules),
        "reaction_only": len(reaction_rules),
        "statin_containing": sum(
            any(i.startswith("DRUG_") for i in lhs + rhs) for lhs, rhs in rules
        ),
        "single_reaction_to_single_reaction": sum(len(a) == len(b) == 1 for a, b in reaction_rules),
        "multi_reaction_antecedent_to_single_reaction": sum(
            len(a) > 1 and len(b) == 1 for a, b in reaction_rules
        ),
        "single_reaction_to_multi_reaction_consequent": sum(
            len(a) == 1 and len(b) > 1 for a, b in reaction_rules
        ),
        "larger_reaction_only_total_ge_4": sum(len(a + b) >= 4 for a, b in reaction_rules),
        "multi_item_consequent": sum(len(b) > 1 for _, b in rules),
        "side_length_histogram": {f"{a}->{b}": v for (a, b), v in sorted(hist.items())},
        "maximum_antecedent_size": max((len(a) for a, _ in rules), default=0),
        "maximum_consequent_size": max((len(b) for _, b in rules), default=0),
        "maximum_total_size": max((len(a + b) for a, b in rules), default=0),
    }


def overlap(apriori, fpgrowth):
    a, f = set(apriori), set(fpgrowth)
    shared = a & f
    mismatches, maxima = [], {m: 0.0 for m in METRICS}
    for key in sorted(shared):
        ar, fr = apriori[key], fpgrowth[key]
        if any(
            int(ar[k]) != int(fr[k])
            for k in ("joint_count", "antecedent_count", "consequent_count", "n")
        ):
            raise ValueError("Shared-rule counts disagree")
        for metric in METRICS:
            av, fv = float(ar[metric]), float(fr[metric])
            if not math.isfinite(av) or not math.isfinite(fv):
                raise ValueError("Nonfinite shared metric")
            maxima[metric] = max(maxima[metric], abs(av - fv))
            if not math.isclose(av, fv, rel_tol=TOLERANCE, abs_tol=TOLERANCE):
                mismatches.append({"rule": key, "metric": metric, "apriori": av, "fpgrowth": fv})
    return {
        "apriori_rules": len(a),
        "fpgrowth_rules": len(f),
        "intersection": len(shared),
        "apriori_only": len(a - f),
        "fpgrowth_only": len(f - a),
        "jaccard": len(shared) / len(a | f) if a | f else None,
        "empty_union_jaccard_convention": "null_not_defined",
        "shared_metric_test_applicable": bool(shared),
        "shared_metrics_reconcile": not mismatches if shared else None,
        "maximum_absolute_metric_differences": maxima if shared else None,
        "metric_mismatches": mismatches,
        "tolerance": TOLERANCE,
    }


def compare(apriori, fpgrowth, common_count):
    raw = overlap(apriori, fpgrowth)
    ac = {k: v for k, v in apriori.items() if int(v["joint_count"]) >= common_count}
    fc = {k: v for k, v in fpgrowth.items() if int(v["joint_count"]) >= common_count}
    only = []
    for algorithm, own, other in [("apriori", apriori, fpgrowth), ("fpgrowth", fpgrowth, apriori)]:
        for key in sorted(set(own) - set(other)):
            only.append(
                {
                    "algorithm": algorithm,
                    "antecedent": key[0],
                    "consequent": key[1],
                    "joint_count": int(own[key]["joint_count"]),
                    "below_common_count": int(own[key]["joint_count"]) < common_count,
                }
            )
    return {
        "raw_native_thresholds_not_identical": raw,
        "common_support_count": common_count,
        "common_support_comparison": overlap(ac, fc),
        "native_only_rules": only,
        "common_support_filter_is_not_a_new_mining_run": True,
        "speed_ratio": None,
        "causal_interpretation": False,
    }


def read_postings(arff: Path, names):
    posts, n, empty = {name + "=1": set() for name in names}, 0, 0
    with arff.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip().lower() == "@data":
                break
        for line in stream:
            line = line.strip()
            if not line:
                continue
            if not line.startswith("{") or not line.endswith("}"):
                raise ValueError("Expected sparse rows")
            indexes = set()
            for cell in line[1:-1].split(","):
                if cell.strip():
                    index, value = cell.split()
                    if value != "1" or int(index) in indexes:
                        raise ValueError("Non-presence or duplicate sparse cell")
                    indexes.add(int(index))
                    posts[names[int(index)] + "=1"].add(n)
            empty += not indexes
            n += 1
    return posts, n, empty


def independent_count_check(rules, posts):
    cache = {}
    for (lhs, rhs), row in rules.items():
        for items, field in [
            (lhs, "antecedent_count"),
            (rhs, "consequent_count"),
            (lhs + rhs, "joint_count"),
        ]:
            key = tuple(sorted(items))
            if key not in cache:
                cache[key] = len(set.intersection(*(posts[i] for i in key)))
            if cache[key] != int(row[field]):
                raise ValueError("Independent ARFF count mismatch")
    return {"rules_verified": len(rules), "distinct_itemset_counts_verified": len(cache)}
