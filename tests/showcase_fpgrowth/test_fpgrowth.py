import csv
import json
import subprocess
from pathlib import Path

import pytest

from showcase.runner import FIXTURE
from showcase_fpgrowth import runner
from tests.showcase.test_runner import require_pinned_runtime


@pytest.fixture(scope="module")
def checkpoint(tmp_path_factory):
    require_pinned_runtime()
    output = tmp_path_factory.mktemp("fp_parent") / "fixture"
    return output, runner.fixture_checkpoint(output)


@pytest.mark.parametrize("support,n", [("0", 20), ("nan", 20), ("1.1", 20), ("0.1", 0)])
def test_invalid_support_rejected(support, n):
    with pytest.raises(ValueError):
        runner.minimum_count(support, n)


def test_registered_support_rounding_and_options():
    assert runner.minimum_count("0.001", 385288) == 386
    assert [runner.minimum_count(s, 385288) for s in ("0.004", "0.003", "0.002")] == [
        1542,
        1156,
        771,
    ]
    assert runner.minimum_count("0.12", 20) == 3
    config = json.loads(runner.CONFIG.read_text())
    assert runner.options() == config["options"]
    assert config["N_is_generation_or_export_cap"] is False


def test_no_full_data_without_explicit_authorization(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(runner, "invoke", lambda *a, **kw: calls.append(True))
    with pytest.raises(ValueError, match="Explicit"):
        runner.full_run(tmp_path / "absent.json")
    assert not calls


def test_wrong_manifest_rejected_even_with_flag(tmp_path):
    with pytest.raises(ValueError, match="Only locked"):
        runner.full_run(tmp_path / "wrong.json", authorize=True)


def test_fixture_guard_before_java(tmp_path):
    with pytest.raises(ValueError, match="Fixture invocation"):
        runner.invoke(tmp_path / "forbidden", arff=FIXTURE, n=385288, attributes=366)
    assert not (tmp_path / "forbidden").exists()


@pytest.mark.weka
def test_fixed_mode_is_complete_and_N_is_ignored(checkpoint):
    _, result = checkpoint
    probes = result["probes"]
    assert probes["first"]["tree_build_passes"] == 1
    assert probes["S_N1"]["returned_rules"] == 50
    assert probes["S_N1"]["api_equals_internal_count"]
    assert probes["S_N1"]["rule_policy_limit_reached"]
    assert probes["iter_N1"]["returned_rules"] == 1
    assert probes["iter_N1"]["internal_qualifying_rules"] == 50
    assert probes["iter_N1"]["tree_build_passes"] == 2
    assert probes["iter_N100000"]["tree_build_passes"] == 2


@pytest.mark.weka
def test_sparse_positive_labels_and_itemset_limit(checkpoint):
    _, result = checkpoint
    assert not result["probes"]["first"]["has_nonpresence_items"]
    assert result["probes"]["sparse_P1"]["has_nonpresence_items"]
    assert result["probes"]["I2"]["maximum_frequent_itemset_length"] == 2
    assert result["probes"]["first"]["maximum_frequent_itemset_length"] == 4


@pytest.mark.weka
def test_all_partitions_metrics_rounding_and_determinism(checkpoint):
    output, result = checkpoint
    assert result["fixture"]["returned_rules"] == 50
    assert result["fixture"]["multi_item_consequents"] == 22
    assert result["fixture"]["empty_transactions"] == 8
    assert len(result["fixture"]["required_structures"]) == 5
    assert result["fixture"]["all_counts_and_four_metrics_match"]
    assert result["fixture"]["exhaustive_family_matches"]
    assert result["probes"]["rounding"]["resolved_lower_count"] == 3
    assert (output / "first/rules.csv").read_bytes() == (output / "second/rules.csv").read_bytes()


@pytest.mark.weka
def test_independent_check_detects_direction_count_corruption(checkpoint, tmp_path):
    source = checkpoint[0] / "first/rules.csv"
    with source.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows[0]["antecedent_count"] = "999"
    with (tmp_path / "rules.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=runner.SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="counts disagree"):
        runner.check_fixture(tmp_path)


@pytest.mark.weka
def test_bad_nominal_input_preserves_failure(tmp_path):
    require_pinned_runtime()
    arff = tmp_path / "bad.arff"
    arff.write_text(FIXTURE.read_text().replace("{0,1}", "{1,0}"))
    output = tmp_path / "failure"
    with pytest.raises(subprocess.CalledProcessError):
        runner.invoke(output, arff=arff)
    record = json.loads((output / "invocation.json").read_text())
    assert record["status"] == "failed" and record["process_exit_code"] != 0
    assert not (output / "complete.txt").exists()
    assert (output / "stderr.txt").stat().st_size > 0


def test_locked_apriori_is_unchanged():
    runner.verify_locked_apriori()
    assert isinstance(runner.source_hashes(), dict)
    assert all(Path(runner.ROOT / p).is_file() for p in runner.source_hashes())
