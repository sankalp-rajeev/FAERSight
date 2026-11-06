"""Complete statin-rule exports and complexity counts; no clinical selection."""

import csv
from collections import Counter

from faersight.audit import sha256, write_json
from showcase.runner import SCHEMA
from showcase_fallback_a1.compare import (
    compare as a1_compare,
)
from showcase_fallback_a1.compare import (
    independent_count_check,
    read_postings,
    read_rules,
)
from showcase_fallback_a1.compare import (
    structure as a1_structure,
)

# Re-export unchanged validation helpers so A2 cannot alter earlier behavior.
__all__ = [
    "compare",
    "structure",
    "export_statin_rules",
    "independent_count_check",
    "read_postings",
    "read_rules",
]


def compare(apriori, fpgrowth, common_count):
    result = a1_compare(apriori, fpgrowth, common_count)
    result["native_comparison"] = result.pop("raw_native_thresholds_not_identical")
    result["native_minimum_counts_identical"] = True
    result["common_count_filter_required"] = False
    return result


def statin_category(lhs, rhs):
    dl = sum(i.startswith("DRUG_") for i in lhs)
    dr = sum(i.startswith("DRUG_") for i in rhs)
    rl, rr = len(lhs) - dl, len(rhs) - dr
    signature = dl, rl, dr, rr
    if not dl and not dr:
        return "reaction_only"
    named = {
        (1, 0, 0, 1): "single_statin_to_single_reaction",
        (1, 1, 0, 1): "statin_plus_one_reaction_to_single_reaction",
        (2, 0, 0, 1): "two_statins_to_single_reaction",
        (0, 1, 1, 0): "single_reaction_to_single_statin",
        (0, 2, 1, 0): "two_reactions_to_single_statin",
    }
    if dl == 1 and rl == dr == 0 and rr > 1:
        return "single_statin_to_multi_reaction_consequent"
    return named.get(signature, "other_statin_containing")


def structure(rules):
    result = a1_structure(rules)
    keys = [
        "single_statin_to_single_reaction",
        "single_statin_to_multi_reaction_consequent",
        "statin_plus_one_reaction_to_single_reaction",
        "two_statins_to_single_reaction",
        "single_reaction_to_single_statin",
        "two_reactions_to_single_statin",
        "other_statin_containing",
        "reaction_only",
    ]
    counts = Counter({key: 0 for key in keys})
    for lhs, rhs in rules:
        counts[statin_category(lhs, rhs)] += 1
    result.update(
        statin_structure_breakdown=dict(counts),
        antecedent_size_histogram={
            str(k): v for k, v in sorted(Counter(len(a) for a, _ in rules).items())
        },
        consequent_size_histogram={
            str(k): v for k, v in sorted(Counter(len(b) for _, b in rules).items())
        },
        multi_item_antecedent=sum(len(a) > 1 for a, _ in rules),
    )
    if (
        sum(counts.values()) != len(rules)
        or sum(v for k, v in counts.items() if k != "reaction_only") != result["statin_containing"]
    ):
        raise ValueError("Statin categories do not partition the rule pool")
    return result


def export_statin_rules(rules, algorithm, target):
    if algorithm not in {"apriori", "fpgrowth"}:
        raise ValueError("Unknown algorithm source")
    selected = [key for key in sorted(rules) if any(i.startswith("DRUG_") for i in key[0] + key[1])]
    csv_path, json_path = (target / f"statin_rules_{algorithm}.{ext}" for ext in ("csv", "json"))
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["algorithm", *SCHEMA], lineterminator="\n")
        writer.writeheader()
        writer.writerows({"algorithm": algorithm, **rules[key]} for key in selected)
    integer_fields = [
        "antecedent_items",
        "consequent_items",
        "joint_count",
        "antecedent_count",
        "consequent_count",
        "n",
        "weka_rank",
        "rule_cap",
    ]
    float_fields = [
        "support",
        "confidence",
        "lift",
        "leverage",
        "conviction",
        "ranking_value",
        "minimum_metric",
    ]
    rows = []
    by_key = {}
    for key in selected:
        row = {
            "algorithm": algorithm,
            **rules[key],
            "antecedent": list(key[0]),
            "consequent": list(key[1]),
        }
        for name in integer_fields:
            row[name] = int(row[name])
        for name in float_fields:
            row[name] = float(row[name])
        rows.append(row)
        by_key[key] = row
    write_json(json_path, rows)
    sample = sorted(selected, key=lambda key: (len(key[0] + key[1]), key))[:8]
    return {
        "algorithm": algorithm,
        "all_statin_rules_exported": len(rows),
        "files": {p.name: sha256(p) for p in (csv_path, json_path)},
        "selection": "first 8 by total item count, canonical lhs/rhs; metrics not consulted",
        "deterministic_representatives": [by_key[key] for key in sample],
        "structure_breakdown": structure(rules)["statin_structure_breakdown"],
    }
