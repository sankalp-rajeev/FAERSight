import json
import os
from pathlib import Path

import duckdb
import pytest

from faersight.arff import write_arff
from faersight.cli import main
from faersight.pipeline import build_fixture, reproduce_fixture

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_sparse_arff_keeps_empty_cases_and_separate_items(tmp_path, transactions):
    target = tmp_path / "test.arff"
    items = write_arff(target, transactions)
    assert items == ["DRUG_alpha", "REAC_REACTION X"]
    assert target.read_bytes() == (FIXTURES / "toy_presence.arff").read_bytes()
    assert target.read_text().count("{}") == 5


def test_fixture_mart_and_manifest(tmp_path):
    result = build_fixture(FIXTURES, tmp_path)
    assert result["eligible_n"] == 10
    assert result["signals"][0]["a"] == 3
    assert result["signals"][0]["n"] == 10
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["dataset"] == "synthetic_only"
    with duckdb.connect(str(tmp_path / "analytical.duckdb"), read_only=True) as connection:
        assert connection.execute("SELECT count(*) FROM cases").fetchone()[0] == 10
        rows = connection.execute(
            "SELECT item_type, report_count FROM item_summary ORDER BY item_type"
        ).fetchall()
        assert rows == [("DRUG", 4), ("REAC", 4)]


def test_cli_validates_template(capsys):
    assert main(["validate-config", "config/experiment.example.yaml"]) == 0
    assert "Pending:" in capsys.readouterr().out


@pytest.mark.weka
@pytest.mark.skipif(not os.environ.get("WEKA_JAR"), reason="WEKA_JAR is not configured")
def test_actual_weka_end_to_end(tmp_path):
    reproduce_fixture(FIXTURES, tmp_path, jar=Path(os.environ["WEKA_JAR"]))
    assert (tmp_path / "comparison.csv").is_file()
    assert (tmp_path / "weka" / "apriori.log").is_file()
    manifest = json.loads((tmp_path / "repro_manifest.json").read_text())
    assert manifest["eligible_n"] == 10
    assert len(manifest["accepted_rules"]) == 1
