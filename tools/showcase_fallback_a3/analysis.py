"""A3 rule classification; complete exports reuse the frozen A2 implementation."""

from collections import Counter

from showcase_fallback_a2.analysis import (
    compare,
    independent_count_check,
    read_postings,
    read_rules,
    statin_category,
)
from showcase_fallback_a2.analysis import export_statin_rules as a2_export
from showcase_fallback_a2.analysis import structure as a2_structure

__all__ = [
    "compare",
    "independent_count_check",
    "read_postings",
    "read_rules",
    "structure",
    "export_statin_rules",
]


def structure(rules):
    result = a2_structure(rules)
    counts = Counter(
        {
            k: 0
            for k in result["statin_structure_breakdown"]
            if k != "two_reactions_to_single_statin"
        }
    )
    counts["multiple_reactions_to_single_statin"] = 0
    for lhs, rhs in rules:
        category = statin_category(lhs, rhs)
        if (
            len(lhs) >= 2
            and all(i.startswith("REAC_") for i in lhs)
            and len(rhs) == 1
            and rhs[0].startswith("DRUG_")
        ):
            category = "multiple_reactions_to_single_statin"
        counts[category] += 1
    if sum(counts.values()) != len(rules):
        raise ValueError("A3 categories fail to partition the rule pool")
    result["statin_structure_breakdown"] = dict(counts)
    return result


def export_statin_rules(rules, algorithm, target):
    result = a2_export(rules, algorithm, target)
    result["structure_breakdown"] = structure(rules)["statin_structure_breakdown"]
    return result
