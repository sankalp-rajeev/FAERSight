import json
from copy import deepcopy

import pytest

from showcase_fallback_a3 import runner
from showcase_fallback_a3.analysis import export_statin_rules, structure
from showcase_fallback_a3.progression import completed_rows, timing_notes
from tests.showcase.test_runner import require_pinned_runtime


@pytest.fixture(scope="module")
def actual_fixture(tmp_path_factory):
    require_pinned_runtime()
    output = tmp_path_factory.mktemp("a3_parent") / "fixture"
    return output, runner.fixture_checkpoint(output)


def test_final_support_counts_and_scope():
    cfg = runner.config()
    assert cfg["minimum_counts"] == {"apriori": 771, "fpgrowth": 771}
    assert cfg["support"] == "0.002" and cfg["fallback_a_final_support"]
    assert cfg["progression_supports"] == ["0.004", "0.003", "0.002"]
    assert not cfg["additional_support_levels_authorized"]
    assert runner.options("fpgrowth")[-1] == "-S" and "-Z" in runner.options("apriori")


def test_authorization_is_required():
    with pytest.raises(ValueError, match="Explicit"):
        runner.execute()


@pytest.mark.parametrize("apriori_passed", [False, True])
def test_terminal_gate_never_adds_another_support(tmp_path, monkeypatch, apriori_passed):
    lock = tmp_path / "manifest.json"
    cfg = {"full_output": "output"}
    lock.write_text(
        json.dumps({"config": cfg, "source_hashes": {}, "protected_history": {"hashes": {}}})
    )
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "LOCK", lock)
    monkeypatch.setattr(runner, "sources", lambda: {})
    monkeypatch.setattr(runner, "config", lambda: cfg)
    monkeypatch.setattr(
        runner.fp, "git", lambda *a, **kw: lock.read_bytes() if a[0] == "show" else "HEAD"
    )
    calls = []

    def invoke(algorithm, output, *, fixture):
        assert not fixture
        calls.append(algorithm)
        return {"status": "passed" if algorithm != "apriori" or apriori_passed else "failed"}

    monkeypatch.setattr(runner, "invoke", invoke)
    result = runner.execute(authorize=True)
    assert calls == (["apriori", "fpgrowth"] if apriori_passed else ["apriori"])
    assert result["fallback_a_status"] == (
        "complete_registered_ladder"
        if apriori_passed
        else "terminated_at_first_failed_A3_algorithm"
    )
    assert not result["additional_support_levels_authorized"] and not result["next_level_executed"]
    with pytest.raises(FileExistsError):
        runner.execute(authorize=True)


@pytest.mark.weka
def test_actual_fixture_complete_metrics_and_deterministic_statin_exports(actual_fixture, tmp_path):
    output, fixture = actual_fixture
    assert fixture["comparison"]["native_comparison"]["intersection"] == 50
    assert fixture["comparison"]["native_comparison"]["shared_metrics_reconcile"]
    _, rules = runner.check_result(
        "apriori",
        output / "apriori",
        n=20,
        minimum=2,
        support="0.1",
        names=runner.apriori.fixture_transactions()[0],
    )
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    a = export_statin_rules(rules, "apriori", first)
    b = export_statin_rules(dict(reversed(list(rules.items()))), "apriori", second)
    assert a == b and a["all_statin_rules_exported"] == 48
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in a["files"])


def test_multiple_reaction_to_statin_category_includes_three_reactions():
    rules = {
        (("REAC_A=1", "REAC_B=1"), ("DRUG_A=1",)): {},
        (("REAC_A=1", "REAC_B=1", "REAC_C=1"), ("DRUG_A=1",)): {},
        (("DRUG_A=1",), ("DRUG_B=1",)): {},
    }
    result = structure(rules)
    assert result["statin_structure_breakdown"]["multiple_reactions_to_single_statin"] == 2
    assert result["statin_structure_breakdown"]["other_statin_containing"] == 1
    assert sum(result["statin_structure_breakdown"].values()) == 3


def prior(support):
    name = (
        "weka-showcase-fallback-a1-0.004"
        if support == "0.004"
        else "weka-showcase-fallback-a2-0.003"
    )
    base = runner.ROOT / "artifacts/manifests" / name
    return json.loads((base / "run/outcome.json").read_text()), json.loads(
        (base / "locked/execution_manifest.json").read_text()
    )


def test_progression_preserves_actual_rounding_eligibility_and_nonmonotonic_times():
    rows = []
    for support in ("0.004", "0.003"):
        outcome, manifest = prior(support)
        rows.extend(completed_rows(support, outcome, manifest, {}))
    assert [r["minimum_count"] for r in rows] == [1541, 1542, 1156, 1156]
    assert rows[0]["eligible_statins"] == []
    assert rows[2]["eligible_statins"] == ["DRUG_atorvastatin"]
    assert [r["rule_count"] for r in rows] == [70, 70, 194, 194]
    assert not timing_notes(rows)["apriori"]["build_time_nondecreasing_as_support_decreases"]


def test_progression_keeps_missing_outputs_missing_and_rejects_count_mismatch():
    outcome, manifest = prior("0.003")
    failed = deepcopy(outcome)
    failed["fpgrowth"]["status"] = "failed"
    failed["comparison"] = None
    rows = completed_rows("0.003", failed, manifest, {})
    assert len(rows) == 1 and rows[0]["native_jaccard"] is None
    invalid = deepcopy(outcome)
    invalid["results"]["apriori"]["native"]["minimum_count"] = 999
    with pytest.raises(ValueError, match="count/population"):
        completed_rows("0.003", invalid, manifest, {})
