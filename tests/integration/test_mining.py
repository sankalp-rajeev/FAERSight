import os
import subprocess
from pathlib import Path

import pytest

from faersight.arff import write_arff
from faersight.mining import load_mining_config, read_csv, run_apriori
from faersight.transactions import Transaction


@pytest.fixture
def weka_jar():
    jar = os.environ.get("WEKA_JAR")
    if not jar:
        pytest.skip("Set WEKA_JAR to exercise actual WEKA")
    return Path(jar)


def test_frozen_mining_and_prefrozen_positive_benchmark():
    config, experiment, benchmark, hashes = load_mining_config(Path("config/mining.yaml"))
    assert config["retain_empty_background_cases"]
    assert experiment["drug_roles"] == ["PS"]
    assert len(benchmark["pairs"]) == 8
    assert len(hashes) == 6


@pytest.mark.weka
def test_java_api_exact_metrics_and_integer_support(tmp_path, weka_jar):
    output = tmp_path / "toy"
    run_apriori(
        Path("tests/fixtures/toy_presence.arff"),
        output,
        jar=weka_jar,
        supports=[0.21],
        min_lift=1.0,
        max_rules=10000,
        expected_n=10,
    )
    rules = read_csv(output / "weka_rules.csv")
    assert len(rules) == 1
    assert int(rules[0]["n"]) == 10
    assert int(rules[0]["drug_count"]) == int(rules[0]["reaction_count"]) == 4
    assert int(rules[0]["joint_count"]) == 3
    assert float(rules[0]["weka_confidence"]) == 0.75
    assert float(rules[0]["weka_lift"]) == 1.875
    # WEKA 3.8.6 rounds N*support rather than always taking the ceiling.
    assert int(read_csv(output / "weka_runs.csv")[0]["min_support_count"]) == 2


@pytest.mark.weka
def test_projection_equals_full_search_with_coexposures_and_empty_cases(tmp_path, weka_jar):
    arff = tmp_path / "coexposure.arff"
    transactions = [
        Transaction("1", "1", "toy", frozenset({"alpha", "beta"}), frozenset({"X", "Y"})),
        Transaction("2", "2", "toy", frozenset({"alpha", "beta"}), frozenset({"X"})),
        Transaction("3", "3", "toy", frozenset({"alpha"}), frozenset({"X", "Y"})),
        Transaction("4", "4", "toy", frozenset({"beta"}), frozenset({"Y"})),
        Transaction("5", "5", "toy", frozenset(), frozenset({"X"})),
        Transaction("6", "6", "toy", frozenset(), frozenset({"Y"})),
        *[Transaction(str(i), str(i), "toy", frozenset(), frozenset()) for i in range(7, 13)],
    ]
    write_arff(arff, transactions)
    results = []
    for mode in ("full", "projected"):
        output = tmp_path / mode
        run_apriori(
            arff,
            output,
            jar=weka_jar,
            supports=[0.1, 0.2],
            min_lift=1.0,
            max_rules=10000,
            expected_n=12,
            mode=mode,
        )
        results.append(
            {
                (r["support_requested"], r["drug"], r["reaction"]): tuple(
                    r[k]
                    for k in (
                        "drug_count",
                        "reaction_count",
                        "joint_count",
                        "n",
                        "weka_confidence",
                        "weka_lift",
                    )
                )
                for r in read_csv(output / "weka_rules.csv")
            }
        )
    assert results[0] == results[1]
    assert len(results[0]) >= 6


@pytest.mark.weka
@pytest.mark.parametrize("malformation", ["nominal_order", "population", "cap"])
def test_java_failure_retains_evidence(tmp_path, weka_jar, malformation):
    arff = tmp_path / "bad.arff"
    text = Path("tests/fixtures/toy_presence.arff").read_text()
    arff.write_text(text.replace("{0,1}", "{1,0}") if malformation == "nominal_order" else text)
    output = tmp_path / "failed"
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        run_apriori(
            arff,
            output,
            jar=weka_jar,
            supports=[0.1],
            min_lift=1.0,
            max_rules=1 if malformation == "cap" else 10000,
            expected_n=11 if malformation == "population" else 10,
        )
    assert '"status": "failed"' in (output / "manifest.json").read_text()
    assert (output / "progress.log").is_file()
