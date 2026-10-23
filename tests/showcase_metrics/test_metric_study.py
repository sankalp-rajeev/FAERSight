import itertools
import json
import math
import subprocess

import pytest

from faersight.audit import sha256
from showcase_metrics import analysis as a
from showcase_metrics.probe import run_probe
from showcase_metrics.runner import config, load_pool, plotting_env
from tests.showcase.test_runner import require_pinned_runtime


def row(name, **values):
    return {
        "antecedent": ["REAC_" + name + "=1"],
        "consequent": ["REAC_Z=1"],
        "confidence": 0.5,
        "lift": 2.0,
        "leverage": 0.01,
        "conviction": 1.5,
        **values,
    }


def test_reconciliation_and_stop_on_finite_discrepancy():
    r = {
        "joint_count": 5,
        "antecedent_count": 9,
        "consequent_count": 7,
        "n": 20,
        **a.recompute(5, 9, 7, 20),
    }
    assert not any(a.reconcile(r).values())
    r["lift"] += 0.001
    with pytest.raises(ValueError, match="discrepancy"):
        a.reconcile(r)


@pytest.mark.parametrize("raw", ["Infinity", "inf", "+Infinity"])
def test_infinity_is_retained_ranked_above_finite_and_tied(raw, tmp_path):
    value = a.parse_metric(raw, "conviction")
    rows = [row("C", conviction=value), row("A", conviction=value), row("B", conviction=9)]
    assert [a.key(r)[0][0] for r in a.ordered(rows, "conviction")] == [
        "REAC_A=1",
        "REAC_C=1",
        "REAC_B=1",
    ]
    assert sorted(a.average_ranks(rows, "conviction").values()) == [1.5, 1.5, 3.0]
    path = tmp_path / "infinity.json"
    a.write_json(path, {"conviction": value})
    assert json.loads(path.read_text()) == {"conviction": "Infinity"}
    stats = next(r for r in a.distributions(rows, [50]) if r["metric"] == "conviction")
    assert stats["infinite_count"] == 2 and stats["mean"] is None


@pytest.mark.parametrize(
    "raw,metric", [("NaN", "conviction"), ("-Infinity", "conviction"), ("Infinity", "lift")]
)
def test_invalid_metric_representations_stop(raw, metric):
    with pytest.raises(ValueError, match="Invalid"):
        a.parse_metric(raw, metric)


def test_average_ties_are_not_lexical_statistical_ranks():
    rows = [row("B", lift=4), row("A", lift=4), row("C", lift=3)]
    ranks = a.average_ranks(rows, "lift")
    assert [ranks[a.key(r)] for r in rows] == [1.5, 1.5, 3]
    assert a.key(a.ordered(rows, "lift")[0]) == a.key(rows[1])


def test_no_rounding_creates_false_metric_ties():
    rows = [row("A", lift=1.23451), row("B", lift=1.23459)]
    assert a.average_ranks(rows, "lift")[a.key(rows[1])] == 1
    assert len(set(a.average_ranks(rows, "lift").values())) == 2


def test_top_k_lexical_boundary_split_and_overlap():
    rows = [row("C", confidence=0.9), row("B", confidence=0.9), row("A", confidence=1)]
    overlap, boundary, four = a.top_k(rows, [2])
    confidence = next(r for r in boundary if r["metric"] == "confidence")
    assert confidence["boundary_group_size"] == 2
    assert confidence["boundary_inside"] == confidence["boundary_outside"] == 1
    assert confidence["membership_split_by_lexical_order"]
    assert len(overlap) == 6 and four[0]["intersection"] == 2
    for r in overlap:
        assert r["union"] == 4 - r["intersection"]


def test_spearman_known_perfect_reverse_and_tied_case():
    rows = [
        row("A", confidence=3, lift=1, leverage=9),
        row("B", confidence=2, lift=2, leverage=6),
        row("C", confidence=1, lift=3, leverage=6),
    ]
    assert a.spearman(rows, "confidence", "lift") == -1
    assert a.spearman(rows, "confidence", "leverage") == pytest.approx(math.sqrt(0.75))
    assert a.spearman(rows, "confidence", "confidence") == 1
    assert a.spearman(rows, "confidence", "conviction") is None


def test_rank_gap_threshold_selectors_and_lexical_tie_break():
    cfg = config()
    rows = [
        row(f"{i:03}", confidence=200 - i, lift=i, leverage=200 - i, conviction=i)
        for i in range(201)
    ]
    result = a.rank_gaps(rows, cfg)
    for group in result.values():
        assert len(group["examples"]) == 3
        assert all(r["rank_gap"] >= 100 for r in group["examples"])
        assert group["examples"] == sorted(
            group["examples"], key=lambda r: (-r["rank_gap"], a.key(r))
        )
    assert not any(r["examples"] for r in a.rank_gaps(rows[:2], cfg).values())


def test_statin_statin_pairs_bound_every_larger_statin_itemset():
    posts = {
        "DRUG_A=1": set(range(9)),
        "DRUG_B=1": set(range(9)),
        "REAC_X=1": {0, 1, 2},
        "REAC_Y=1": {0, 1},
    }
    pairs, bound = a.statin_itemset_bound(posts)
    assert len(pairs) == 5
    assert bound["families"]["statin_reaction"]["maximum_joint_count"] == 3
    assert bound["all_statin_containing_itemsets_size_ge_2_maximum_joint_count"] == 9
    brute = max(
        len(set.intersection(*(posts[k] for k in items)))
        for size in range(2, len(posts) + 1)
        for items in itertools.combinations(posts, size)
        if any(k.startswith("DRUG_") for k in items)
    )
    assert brute == 9


def test_frozen_pool_identity_precision_and_single_to_single_population():
    rows, provenance = load_pool()
    assert len(rows) == 586 and len(a.single_to_single(rows)) == 472
    assert provenance["apriori"]["rules"] == provenance["fpgrowth"]["rules"] == 586
    assert all(float(r["raw_API_values"][m]) == r[m] for r in rows for m in a.VALUES)
    subset = [
        row("A", confidence=3),
        row("B", confidence=1),
        row("C", confidence=2, antecedent=["REAC_Q=1", "REAC_W=1"]),
    ]
    singles = a.single_to_single(subset)
    assert a.average_ranks(singles, "confidence")[a.key(subset[1])] == 2
    assert a.average_ranks(subset, "confidence")[a.key(subset[1])] == 3


@pytest.mark.weka
def test_actual_confidence_one_conviction_api_without_association_build(tmp_path):
    require_pinned_runtime()
    result = run_probe(tmp_path / "probe")
    assert result["association_builds"] == 0
    cases = [r for r in result["cases"] if r["confidence_one"]]
    assert len(cases) == 3
    assert [r["parsed"]["conviction"] for r in cases] == [3.25, 0.95, 0]
    assert all(math.isfinite(r["parsed"]["conviction"]) for r in cases)


def test_distribution_exact_ties_and_empirical_percentiles():
    rows = [row(str(i), confidence=v) for i, v in enumerate([1, 1, 2, 4])]
    stats = a.distributions(rows, [25, 50, 95])[0]
    assert stats["rules_in_ties"] == 2 and stats["fraction_in_ties"] == 0.5
    assert stats["largest_tie_group"] == 2 and stats["distinct_values"] == 3
    assert stats["percentiles"] == {"25": 1, "50": 1, "95": 4}
    assert stats["median"] == 1.5 and stats["mean"] == 2


def test_extreme_plot_pair_selection_uses_canonical_metric_name_tie_break():
    values = [
        {"metric_a": "lift", "metric_b": "leverage", "spearman": 0.9},
        {"metric_a": "confidence", "metric_b": "conviction", "spearman": 0.9},
        {"metric_a": "conviction", "metric_b": "lift", "spearman": -0.1},
    ]
    selected = a.plot_pairs(values)
    assert selected[0]["metric_a"] == "confidence"
    assert selected[1]["metric_b"] == "lift"


def test_deterministic_chart_and_data_bytes(tmp_path):
    rows = [
        row(str(i), confidence=i, lift=10 - i, leverage=i, conviction=10 - i) for i in range(1, 10)
    ]
    for r in rows:
        r["average_ranks"] = {m: a.average_ranks(rows, m)[a.key(r)] for m in a.METRICS}
    corr = a.correlations(rows, "fixture")
    data = {
        "metrics": list(a.METRICS),
        "correlations": corr,
        "scatter_pairs": a.plot_pairs(corr),
        "rules": rows,
    }
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    a.write_json(first, data)
    a.write_json(second, data)
    assert first.read_bytes() == second.read_bytes()
    outputs = []
    for name in ["one", "two"]:
        output = tmp_path / name
        subprocess.run(
            [config()["plotting_python"], "-m", "showcase_metrics.plots", str(first), str(output)],
            env=plotting_env(),
            capture_output=True,
            check=True,
            timeout=120,
        )
        outputs.append({p.name: sha256(p) for p in output.iterdir()})
    assert outputs[0] == outputs[1]
    assert len([k for k in outputs[0] if k.endswith(".png")]) == 3
