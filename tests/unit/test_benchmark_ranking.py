import math

from faersight.benchmark_ranking import benchmark_ranks


def test_ties_percentiles_and_threshold_misses_are_retained():
    signals = [
        {"drug": "a", "reaction": "X", "lift_python_check": 3, "prr": 4, "ror": 5},
        {"drug": "b", "reaction": "X", "lift_python_check": 3, "prr": 2, "ror": 2},
        {"drug": "c", "reaction": "X", "lift_python_check": 1, "prr": 1, "ror": 1},
        {"drug": "d", "reaction": "X", "lift_python_check": 9, "prr": math.inf, "ror": 9},
    ]
    benchmark = {"pairs": [{"drug": drug, "reaction": "X"} for drug in "abcde"]}
    ranks = benchmark_ranks(signals, benchmark, {0.1: {"pairs": {("a", "X"): {}}}}, "PS")
    all_rows = [r for r in ranks if r["pool"] == "all_candidates"]
    a_lift = next(r for r in all_rows if r["drug"] == "a" and r["metric"] == "lift")
    assert a_lift["rank"] == 1.5 and a_lift["percentile"] == 75
    assert a_lift["pool_size"] == 3 and a_lift["nonfinite_pairs_excluded"] == 1
    assert {r["status"] for r in all_rows if r["drug"] == "d"} == {
        "nonfinite_score_excluded_from_shared_pool"
    }
    assert {r["status"] for r in all_rows if r["drug"] == "e"} == {"not_in_candidate_vocabulary"}
    subset = [r for r in ranks if r["pool"] == "weka_accepted"]
    assert all(r["rank"] == 1 and r["percentile"] == 100 for r in subset if r["drug"] == "a")
    assert all(
        r["rank"] is None and r["status"] == "not_weka_accepted" for r in subset if r["drug"] == "b"
    )
    assert len(ranks) == 5 * 3 * 2


def test_empty_pool_has_no_invented_rank():
    row = {"drug": "a", "reaction": "X", "lift_python_check": 2, "prr": 2, "ror": 2}
    result = benchmark_ranks(
        [row], {"pairs": [{"drug": "a", "reaction": "X"}]}, {0.1: {"pairs": {}}}, "PS"
    )
    assert all(
        r["rank"] is None and r["pool_size"] == 0 for r in result if r["pool"] == "weka_accepted"
    )
