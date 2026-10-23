import csv
import json

import pytest

from showcase.runner import SCHEMA
from showcase_fallback_a2 import runner
from showcase_fallback_a2.analysis import export_statin_rules, statin_category, structure
from tests.showcase.test_runner import require_pinned_runtime


@pytest.fixture(scope="module")
def actual_fixture(tmp_path_factory):
    require_pinned_runtime()
    output = tmp_path_factory.mktemp("a2_parent") / "fixture"
    return output, runner.fixture_checkpoint(output)


def test_a2_counts_and_scope_are_locked():
    cfg = runner.config()
    assert cfg["minimum_counts"] == {"apriori": 1156, "fpgrowth": 1156}
    assert cfg["full_output"].endswith("a2/0.003")
    assert runner.options("apriori")[runner.options("apriori").index("-M") + 1] == "0.003"
    assert "-Z" in runner.options("apriori") and runner.options("fpgrowth")[-1] == "-S"
    assert cfg["next_support_authorized"] is False


def test_explicit_authorization_required():
    with pytest.raises(ValueError, match="Explicit"):
        runner.execute()


@pytest.mark.parametrize("apriori_passed", [False, True])
def test_a2_gate_order_and_no_retry(tmp_path, monkeypatch, apriori_passed):
    cfg = {"full_output": "output"}
    lock = tmp_path / "manifest.json"
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
    assert result["next_0_002_eligible_not_authorized"] == apriori_passed
    assert not result["next_level_executed"]
    with pytest.raises(FileExistsError):
        runner.execute(authorize=True)


@pytest.mark.weka
def test_actual_fixture_recovers_statin_forms_and_reconciles_metrics(actual_fixture):
    output, result = actual_fixture
    assert result["comparison"]["native_comparison"]["intersection"] == 50
    assert result["comparison"]["native_comparison"]["shared_metrics_reconcile"]
    for algorithm in runner.ALGORITHMS:
        export = result["statin_fixture_exports"][algorithm]
        assert export["all_statin_rules_exported"] == 48
        assert all(v > 0 for v in export["structure_breakdown"].values())
        with (output / f"statin_rules_{algorithm}.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            reader = csv.DictReader(stream)
            assert reader.fieldnames == ["algorithm", *SCHEMA]
            assert all(row["algorithm"] == algorithm for row in reader)


@pytest.mark.weka
def test_statin_exports_and_sample_are_independent_of_input_order(actual_fixture, tmp_path):
    output, _ = actual_fixture
    names = runner.apriori.fixture_transactions()[0]
    _, pool = runner.check_result(
        "apriori", output / "apriori", n=20, minimum=2, support="0.1", names=names
    )
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    a = export_statin_rules(pool, "apriori", first)
    b = export_statin_rules(dict(reversed(list(pool.items()))), "apriori", second)
    assert a == b
    assert len(a["deterministic_representatives"]) == 8
    for name in a["files"]:
        assert (first / name).read_bytes() == (second / name).read_bytes()
    exported = json.loads((first / "statin_rules_apriori.json").read_text())
    assert len(exported) == 48
    assert all(
        isinstance(row["antecedent"], list) and isinstance(row["joint_count"], int)
        for row in exported
    )


def test_no_statin_rules_produces_explicit_empty_exports(tmp_path):
    result = export_statin_rules({}, "fpgrowth", tmp_path)
    assert result["all_statin_rules_exported"] == 0 and not result["deterministic_representatives"]
    assert json.loads((tmp_path / "statin_rules_fpgrowth.json").read_text()) == []
    with (tmp_path / "statin_rules_fpgrowth.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == ["algorithm", *SCHEMA]
        assert list(reader) == []


def test_complexity_counts_and_other_statins_do_not_discard_rules():
    keys = {
        (("DRUG_A=1",), ("DRUG_B=1",)): {},
        (("REAC_X=1", "REAC_Y=1"), ("DRUG_A=1",)): {},
        (("REAC_X=1",), ("REAC_Y=1",)): {},
    }
    result = structure(keys)
    assert result["statin_containing"] == 2 and result["reaction_only"] == 1
    assert result["statin_structure_breakdown"]["other_statin_containing"] == 1
    assert result["antecedent_size_histogram"] == {"1": 2, "2": 1}
    assert result["consequent_size_histogram"] == {"1": 3}
    assert result["multi_item_antecedent"] == 1 and result["multi_item_consequent"] == 0
    assert statin_category(("DRUG_A=1",), ("REAC_X=1", "REAC_Y=1")) == (
        "single_statin_to_multi_reaction_consequent"
    )
