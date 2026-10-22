import csv
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from faersight.audit import sha256
from showcase import runner


def require_pinned_runtime():
    config = yaml.safe_load(runner.CONFIG.read_text())
    if not os.environ.get("WEKA_JAR") or not Path(config["runtime"]["java"]).is_file():
        pytest.skip("Exact previously-used WEKA/JDK runtime is required for showcase integration")


@pytest.fixture(scope="module")
def actual_checkpoint(tmp_path_factory):
    require_pinned_runtime()
    folder = tmp_path_factory.mktemp("showcase_fixture")
    result = runner.fixture_checkpoint(folder)
    return folder, result


def test_locked_counts_and_options():
    config = yaml.safe_load(runner.CONFIG.read_text())
    assert [
        runner.minimum_count(r["fraction"], 385288) for r in config["apriori"]["support_ladder"]
    ] == [385, 193, 77, 39]
    assert runner.minimum_count("0.12", 20) == 2
    assert runner.minimum_count("0.001", 20) == 1
    opts = runner.options("0.001")
    assert "-Z" in opts and opts[opts.index("-D") + 1] == "1.0"
    assert opts[opts.index("-S") + 1] == "-1.0"


@pytest.mark.parametrize("support,n", [("0", 20), ("nan", 20), ("1.1", 20), ("0.1", 0)])
def test_bad_support_rejected(support, n):
    with pytest.raises(ValueError):
        runner.minimum_count(support, n)


def test_full_execution_is_not_implicitly_authorized(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(runner, "invoke", lambda *a, **k: called.append(True))
    with pytest.raises(ValueError, match="explicit"):
        runner.full_run(tmp_path / "absent.json", tmp_path / "full", "0.001")
    assert not called
    assert not (tmp_path / "full").exists()


def test_fixture_guard_rejects_full_input_before_java(tmp_path):
    config = yaml.safe_load(runner.CONFIG.read_text())
    with pytest.raises(ValueError, match="Fixture invocation"):
        runner.invoke(
            tmp_path / "forbidden",
            arff=runner.ROOT / config["input"]["path"],
            n=385288,
            attributes=366,
        )
    assert not (tmp_path / "forbidden").exists()


@pytest.mark.weka
def test_all_structures_metrics_and_determinism(actual_checkpoint):
    folder, result = actual_checkpoint
    assert result["status"] == "passed" and result["full_data_mining_started"] is False
    assert result["fixture"]["returned_rules"] == 50
    assert result["fixture"]["multi_item_consequents"] == 22
    assert result["fixture"]["empty_transactions"] == 8
    assert len(result["fixture"]["required_structures_recovered"]) == 5
    assert result["fixture"]["exhaustive_rule_family_matches"]
    assert sha256(folder / "first/rules.csv") == sha256(folder / "second/rules.csv")


@pytest.mark.weka
def test_defaults_fixed_schedule_zero_option_and_upper_pruning(actual_checkpoint):
    folder, result = actual_checkpoint
    audit = json.loads((folder / "options_audit/runtime_and_options.json").read_text())
    assert audit["metric_identifiers"] == {
        "0": "Confidence",
        "1": "Lift",
        "2": "Leverage",
        "3": "Conviction",
    }
    assert audit["available_processors"] == 2 and audit["max_heap_bytes"] == 4294967296
    assert audit["defaults"]["delta"] == 0.05
    assert audit["defaults"]["significance_level"] == -1
    probes = result["semantic_probes"]
    assert probes["fixed"]["cycles"] == 1 and probes["default_delta"]["cycles"] == 18
    assert probes["without_Z"]["has_zero_items"]
    assert probes["upper_equals_lower"]["returned_rules"] == 0


@pytest.mark.weka
def test_cap_is_conservative_stop_and_retains_truncated_output(actual_checkpoint):
    folder, result = actual_checkpoint
    cap = json.loads((folder / "cap_probe/invocation.json").read_text())
    assert cap["status"] == "stop_cap_ambiguity"
    assert result["cap_probe_returned"] == 1
    assert (folder / "cap_probe/apriori_raw.txt").is_file()


@pytest.mark.weka
def test_independent_validation_detects_wrong_direction_counts(actual_checkpoint, tmp_path):
    folder, _ = actual_checkpoint
    source = folder / "first/rules.csv"
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
def test_semantic_input_failure_preserves_log_and_no_completion(tmp_path):
    require_pinned_runtime()
    arff = tmp_path / "bad.arff"
    arff.write_text(runner.FIXTURE.read_text().replace("{0,1}", "{1,0}"))
    output = tmp_path / "failed"
    with pytest.raises(subprocess.CalledProcessError):
        runner.invoke(output, arff=arff, n=20, attributes=4)
    status = json.loads((output / "invocation.json").read_text())
    assert status["status"] == "failed"
    assert (output / "process.txt").stat().st_size > 0
    assert not (output / "complete.txt").exists()


def test_no_concurrent_jvm_allowed():
    with runner.single_jvm(), pytest.raises(FileExistsError):
        with runner.single_jvm():
            pytest.fail("Concurrent JVM lock was acquired")
