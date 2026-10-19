import math

import pytest

from faersight.disproportionality import Counts, metrics
from faersight.evaluation import average_ranks, ranking_comparison, spearman, verify_weka


def test_tied_ranks_and_undefined_correlations():
    assert average_ranks([9, 3, 3, 1]) == [4, 2.5, 2.5, 1]
    assert spearman([1, 2, 2, 4], [4, 3, 3, 1]) == pytest.approx(-1)
    assert spearman([1, 1], [1, 2]) is None
    assert spearman([], []) is None
    with pytest.raises(ValueError, match="finite"):
        spearman([math.inf], [1])


def test_top_k_uses_shared_finite_pairs_and_reports_boundary_ties():
    rows = [
        {"drug": "a", "reaction": str(i), "weka_lift": lift, "prr": prr}
        for i, (lift, prr) in enumerate([(4, math.inf), (3, 2), (3, 4), (1, 1)])
    ]
    result = ranking_comparison(rows, "prr", [1, 10])
    assert result["shared_finite_pairs"] == 3
    assert result["excluded_nonfinite_pairs"] == 1
    assert result["top_k"][0]["overlap_count"] == 0
    assert result["top_k"][0]["lift_boundary_tie"]
    assert result["top_k"][1]["effective_k"] == 3
    assert result["top_k"][1]["overlap_fraction"] == 1


def test_missing_projection_fails_even_when_no_rules_returned():
    with pytest.raises(ValueError, match="Incomplete"):
        verify_weka([], [], [{"drug": "a", "reaction": "X"}], supports=[0.1], min_lift=1.2, n=10)


@pytest.mark.parametrize(
    "corruption",
    [
        None,
        "count",
        "metric",
        "population",
        "missing_pair",
        "duplicate_pair",
        "cap",
        "schedule",
        "direction",
    ],
)
def test_rule_gate_checks_counts_metrics_population_and_coverage(corruption):
    signals = [{"drug": "a", "reaction": "X", **metrics(Counts(3, 1, 1, 5))}]
    rule = {
        "drug": "a",
        "reaction": "X",
        "projection": "r0000",
        "support_requested": "0.1",
        "n": "10",
        "joint_count": "3",
        "drug_count": "4",
        "reaction_count": "4",
        "weka_confidence": "0.75",
        "weka_lift": "1.875",
    }
    run = {
        "projection": "r0000",
        "support_requested": "0.1",
        "n": "10",
        "attributes": "2",
        "cap_reached": "false",
        "cycles": "1",
        "min_support_count": "1",
        "options": "-U 1 -M 0.1 -D 1 -T 1 -C 1.2 -Z",
    }
    rules = [rule]
    if corruption == "count":
        rule["joint_count"] = "2"
    elif corruption == "metric":
        rule["weka_lift"] = "1.88"
    elif corruption == "population":
        rule["n"] = "5"
    elif corruption == "missing_pair":
        rules = []
    elif corruption == "duplicate_pair":
        rules *= 2
    elif corruption == "cap":
        run["cap_reached"] = "true"
    elif corruption == "schedule":
        run["cycles"] = "2"
    elif corruption == "direction":
        rule["drug"], rule["reaction"] = "X", "a"
    if corruption is None:
        result = verify_weka(rules, [run], signals, supports=[0.1], min_lift=1.2, n=10)
        assert len(result[0.1]["pairs"]) == 1
    else:
        with pytest.raises(ValueError):
            verify_weka(rules, [run], signals, supports=[0.1], min_lift=1.2, n=10)
