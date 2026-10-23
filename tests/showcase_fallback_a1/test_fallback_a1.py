import csv
import json

import pytest

from showcase.runner import FIXTURE, SCHEMA, independent_values
from showcase_fallback_a1 import runner
from showcase_fallback_a1.compare import (
    compare,
    independent_count_check,
    overlap,
    read_postings,
    read_rules,
)
from tests.showcase.test_runner import require_pinned_runtime


@pytest.fixture(scope="module")
def actual_fixture(tmp_path_factory):
    require_pinned_runtime()
    output = tmp_path_factory.mktemp("a1_parent") / "fixture"
    return output, runner.fixture_checkpoint(output)


def test_locked_counts_and_options():
    cfg = runner.config()
    assert cfg["minimum_counts"] == {"apriori": 1541, "fpgrowth": 1542}
    assert cfg["common_support_count_for_posthoc_comparison"] == 1542
    assert runner.options("apriori")[runner.options("apriori").index("-M") + 1] == "0.004"
    assert "-Z" in runner.options("apriori")
    assert runner.options("fpgrowth")[-1] == "-S"
    assert cfg["next_support_authorized"] is False


def test_explicit_full_authorization_required():
    with pytest.raises(ValueError, match="Explicit"):
        runner.execute()


@pytest.mark.parametrize("first_passed", [False, True])
def test_apriori_first_gate_no_retry_or_next_level(tmp_path, monkeypatch, first_passed):
    manifest_path = tmp_path / "manifest.json"
    cfg = {"full_output": "output"}
    manifest = {"config": cfg, "source_hashes": {}, "protected_history": {"hashes": {}}}
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "LOCK", manifest_path)
    monkeypatch.setattr(runner, "sources", lambda: {})
    monkeypatch.setattr(runner, "config", lambda: cfg)
    monkeypatch.setattr(
        runner.fp,
        "git",
        lambda *a, **k: manifest_path.read_bytes() if a[0] == "show" else "fixture_commit",
    )
    calls = []

    def invoke(algorithm, output, *, fixture):
        assert not fixture
        calls.append(algorithm)
        return {"status": "passed" if algorithm != "apriori" or first_passed else "failed"}

    monkeypatch.setattr(runner, "invoke", invoke)
    result = runner.execute(authorize=True)
    assert calls == (["apriori", "fpgrowth"] if first_passed else ["apriori"])
    assert result["next_0_003_eligible_not_authorized"] == first_passed
    assert result["next_level_executed"] is False
    with pytest.raises(FileExistsError):
        runner.execute(authorize=True)


def rule(joint):
    return {
        "joint_count": str(joint),
        "antecedent_count": "3000",
        "consequent_count": "5000",
        "n": "385288",
        **independent_values(joint, 3000, 5000, 385288),
    }


def test_common_support_filter_separates_rounding_from_agreement():
    key = (("REAC_X=1",), ("REAC_Y=1",))
    edge = (("REAC_Z=1",), ("REAC_Y=1",))
    result = compare({key: rule(1600), edge: rule(1541)}, {key: rule(1600)}, 1542)
    assert result["raw_native_thresholds_not_identical"]["apriori_only"] == 1
    assert result["raw_native_thresholds_not_identical"]["jaccard"] == 0.5
    assert result["common_support_comparison"]["jaccard"] == 1
    assert result["common_support_comparison"]["shared_metrics_reconcile"]
    assert result["native_only_rules"][0]["below_common_count"]


def test_shared_metric_difference_and_count_disagreement_are_detected():
    key = (("REAC_X=1",), ("REAC_Y=1",))
    changed = rule(1600)
    changed["lift"] *= 1.001
    assert not overlap({key: rule(1600)}, {key: changed})["shared_metrics_reconcile"]
    changed["joint_count"] = "1601"
    with pytest.raises(ValueError, match="counts disagree"):
        overlap({key: rule(1600)}, {key: changed})


@pytest.mark.weka
def test_actual_both_unmodified_bridges_and_independent_counts(actual_fixture):
    output, result = actual_fixture
    assert result["status"] == "passed"
    assert result["comparison"]["common_support_comparison"]["intersection"] == 50
    names = runner.apriori.fixture_transactions()[0]
    posts, n, empty = read_postings(FIXTURE, names)
    assert n == 20 and empty == 8
    for algorithm in runner.ALGORITHMS:
        native, rules = runner.check_result(
            algorithm, output / algorithm, n=n, minimum=2, support="0.1", names=names
        )
        assert native["returned_rules"] == 50
        assert independent_count_check(rules, posts)["rules_verified"] == 50


@pytest.mark.weka
@pytest.mark.parametrize(
    "field,value", [("confidence", "nan"), ("joint_count", "999"), ("antecedent", '["DRUG_A=0"]')]
)
def test_canonical_gate_rejects_invalid_comparison_input(actual_fixture, tmp_path, field, value):
    with (actual_fixture[0] / "apriori/rules.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows[0][field] = value
    with (tmp_path / "rules.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError):
        read_rules(
            tmp_path,
            n=20,
            minimum_count=2,
            support="0.1",
            vocabulary={n + "=1" for n in runner.apriori.fixture_transactions()[0]},
        )
