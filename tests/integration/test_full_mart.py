import csv
import json
import os
from pathlib import Path

import duckdb
import pytest

from faersight.arff import export_mart_arff
from faersight.audit import sha256
from faersight.evaluation import evaluate_experiment
from faersight.integration import build_full_mart, validate_mart
from faersight.mining import read_csv, run_apriori
from faersight.parse import stage_relation
from faersight.spotcheck import spotcheck_sources


@pytest.fixture
def real_format_sources(tmp_path):
    folder = tmp_path / "source"
    folder.mkdir()
    demo = folder / "DEMO25Q4.txt"
    demo.write_text(
        "primaryid$caseid$caseversion$sex\n"
        "10$1$1$F\n11$1$2$F\n20$2$1$M\n30$3$1$\n"
        "40$4$1$M\n50$5$1$F\n60$6$1$\n",
        encoding="ascii",
    )
    drug = folder / "DRUG25Q4.txt"
    drug.write_text(
        "primaryid$caseid$drug_seq$role_cod$drugname$prod_ai$route\n"
        "10$1$1$PS$ATORVASTATIN$ATORVASTATIN$Oral\n"
        "11$1$1$PS$LIPITOR$ATORVASTATIN CALCIUM$Oral\n"
        "11$1$1$PS$LIPITOR$ATORVASTATIN CALCIUM$Other\n"
        "20$2$1$SS$CRESTOR$ROSUVASTATIN$Oral\n"
        "30$3$1$PS$BACKGROUND PRODUCT$$Oral\n"
        "40$4$1$C$ATORVASTATIN$ATORVASTATIN$Oral\n"
        "50$5$1$PS$COMBINATION$AMLODIPINE BESILATE\\ATORVASTATIN CALCIUM$Oral\n"
        "60$6$1$PS$ATORVASTATIN UNKNOWN$UNKNOWN$\n"
        "999$999$1$PS$LIPITOR$ATORVASTATIN$Oral\n",
        encoding="ascii",
    )
    reac = folder / "REAC25Q4.txt"
    reac.write_text(
        "primaryid$caseid$pt$drug_rec_act\n10$1$OLD$\n"
        "11$1$REACTION X$\n11$1$REACTION X$\n20$2$REACTION X$\n"
        "30$3$REACTION X$\n40$4$REACTION Y$\n50$5$REACTION Y$\n"
        "60$6$REACTION Z$\n999$999$ORPHAN$\n",
        encoding="ascii",
    )
    deleted = folder / "DELETE25Q4.txt"
    deleted.write_text(" \n9999\n", encoding="ascii")
    mapping = folder / "mapping.csv"
    mapping.write_text(
        "raw_name,canonical_ingredient,mapping_basis,reviewed,alias_type\n"
        "ATORVASTATIN,atorvastatin,synthetic reviewed ingredient,true,ingredient\n"
        "ATORVASTATIN CALCIUM,atorvastatin,synthetic reviewed salt,true,ingredient\n"
        "LIPITOR,atorvastatin,synthetic reviewed brand,true,brand\n"
        "ROSUVASTATIN,rosuvastatin,synthetic reviewed ingredient,true,ingredient\n"
        "CRESTOR,rosuvastatin,synthetic reviewed brand,true,brand\n",
        encoding="ascii",
    )
    return (
        [
            {
                "quarter": "2025Q4",
                "paths": {"DEMO": demo, "DRUG": drug, "REAC": reac, "DELETE": deleted},
            }
        ],
        mapping,
    )


def build(sources, mapping, output, *, roles=None):
    return build_full_mart(
        sources,
        output,
        mapping_path=mapping,
        ingredients=["atorvastatin", "rosuvastatin"],
        therapeutic_class="statins",
        roles=roles or ["PS"],
        min_target_cases=1,
        memory_limit="256MB",
        threads=1,
    )


def test_full_source_mart_and_denominator(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    output = tmp_path / "mart"
    quality = build(sources, mapping, output)
    assert quality["status"] == "passed"
    assert quality["eligible_n"] == 6
    assert quality["target_exposed_n"] == 2
    assert quality["background_n"] == 4
    assert quality["scientific_findings_validated"] is False
    assert validate_mart(output / "analytical.duckdb")["status"] == "passed"
    with duckdb.connect(str(output / "analytical.duckdb"), read_only=True) as c:
        assert c.execute(
            "SELECT a,b,c,d,n FROM signal_counts WHERE drug='atorvastatin' "
            "AND reaction='REACTION X'"
        ).fetchone() == (1, 1, 2, 2, 6)
        assert c.execute("SELECT count(*) FROM case_drugs WHERE case_id='1'").fetchone()[0] == 2
        assert c.execute("SELECT count(*) FROM case_reactions WHERE case_id='1'").fetchone()[0] == 1
        assert c.execute("SELECT primary_id FROM cases WHERE case_id='1'").fetchone()[0] == "11"
        assert (
            c.execute("SELECT canonical_ingredient FROM case_drugs WHERE case_id='5'").fetchone()[0]
            == "atorvastatin"
        )
        assert (
            c.execute("SELECT canonical_ingredient FROM case_drugs WHERE case_id='6'").fetchone()[0]
            is None
        )
        assert c.execute("SELECT count(*) FROM case_items WHERE case_id='6'").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM cases WHERE case_id='6'").fetchone()[0] == 1
        assert (
            c.execute(
                "SELECT count(*) FROM case_drug_presence WHERE case_id IN ('2','4')"
            ).fetchone()[0]
            == 0
        )
    audit = json.loads((output / "preprocess_audit.json").read_text())
    assert audit["case_versions_removed"] == 1
    assert audit["orphan_drug_rows"] == audit["orphan_reac_rows"] == 1
    assert audit["duplicate_drug_sequence_groups_preserved"] == 1


def test_ss_sensitivity_changes_exposure_but_not_population(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    ps = build(sources, mapping, tmp_path / "ps")
    psss = build(sources, mapping, tmp_path / "psss", roles=["PS", "SS"])
    assert ps["eligible_n"] == psss["eligible_n"] == 6
    assert ps["target_exposed_n"] == 2 and psss["target_exposed_n"] == 3


def test_deleted_cases_excluded_and_counted(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    sources[0]["paths"]["DELETE"].write_text("\n3\n")
    output = tmp_path / "deleted"
    quality = build(sources, mapping, output)
    assert quality["eligible_n"] == 5
    audit = json.loads((output / "preprocess_audit.json").read_text())
    assert audit["exclusions"]["deleted_latest_cases"] == 1


def test_incomplete_new_version_cannot_resurrect_old_case(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    with sources[0]["paths"]["DEMO"].open("a") as stream:
        stream.write("12$1$3$F\n")
    quality = build(sources, mapping, tmp_path / "missing_latest")
    assert quality["eligible_n"] == 5
    with duckdb.connect(str(tmp_path / "missing_latest/analytical.duckdb"), read_only=True) as c:
        assert c.execute("SELECT count(*) FROM cases WHERE case_id='1'").fetchone()[0] == 0


def test_case_report_join_mismatch_fails_closed(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    drug = sources[0]["paths"]["DRUG"]
    drug.write_text(drug.read_text().replace("11$1$", "11$999$"))
    with pytest.raises(ValueError, match="identity quality gate"):
        build(sources, mapping, tmp_path / "bad_join")
    assert not (tmp_path / "bad_join/analytical.duckdb").exists()
    assert (tmp_path / "bad_join/integration_failure.json").is_file()


def test_mapping_disagreement_blocks_quality_gate(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    drug = sources[0]["paths"]["DRUG"]
    drug.write_text(drug.read_text().replace("CRESTOR$ROSUVASTATIN", "CRESTOR$ATORVASTATIN"))
    with pytest.raises(ValueError, match="quality gates failed"):
        build(sources, mapping, tmp_path / "conflicting_mapping")
    quality = json.loads((tmp_path / "conflicting_mapping/quality_gates.json").read_text())
    assert not quality["checks"]["no_mapping_conflicts"]


def test_two_quarters_choose_one_source_version_without_join_multiplication(
    real_format_sources, tmp_path
):
    sources, mapping = real_format_sources
    first_quarter = {**sources[0], "quarter": "2025Q3"}
    output = tmp_path / "two_quarters"
    quality = build([first_quarter, *sources], mapping, output)
    assert quality["eligible_n"] == 6
    with duckdb.connect(str(output / "analytical.duckdb"), read_only=True) as c:
        assert c.execute("SELECT DISTINCT quarter FROM cases").fetchall() == [("2025Q4",)]
        assert c.execute("SELECT count(*) FROM case_drugs").fetchone()[0] == 7
        assert c.execute("SELECT count(*) FROM raw_drug").fetchone()[0] == 18


def test_staging_preserves_blanks_and_raw_columns(real_format_sources, tmp_path):
    sources, _ = real_format_sources
    output = tmp_path / "stage.csv"
    audit = stage_relation(sources[0]["paths"]["DRUG"], "DRUG", "2025Q4", output)
    assert audit["source_rows"] == 9
    assert audit["blank_required_values"]["prod_ai"] == 1
    with output.open(newline="") as stream:
        records = list(csv.DictReader(stream))
    assert records[0]["_source_row"] == "2"
    assert records[0]["route"] == "Oral"


def test_malformed_ingestion_retains_diagnostic_and_no_final_database(
    real_format_sources, tmp_path
):
    sources, mapping = real_format_sources
    with sources[0]["paths"]["REAC"].open("a") as stream:
        stream.write("unbalanced$row\n")
    with pytest.raises(ValueError, match="malformed row"):
        build(sources, mapping, tmp_path / "malformed")
    assert not (tmp_path / "malformed/analytical.duckdb").exists()


def test_validated_snapshot_is_not_overwritten(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    output = tmp_path / "immutable"
    build(sources, mapping, output)
    before = sha256(output / "integration_manifest.json")
    with pytest.raises(ValueError, match="new output directory"):
        build(sources, mapping, output)
    assert sha256(output / "integration_manifest.json") == before


def test_revalidation_detects_changed_denominators(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    output = tmp_path / "tampered"
    build(sources, mapping, output)
    with duckdb.connect(str(output / "analytical.duckdb")) as c:
        c.execute("UPDATE signal_counts SET n = n + 1")
    quality = validate_mart(output / "analytical.duckdb")
    assert quality["status"] == "failed"
    assert not quality["checks"]["common_denominator_and_nonnegative_cells"]


def test_independent_source_sample_check(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    output = tmp_path / "sample"
    build(sources, mapping, output)
    result = spotcheck_sources(output / "analytical.duckdb", sources, output)
    assert result["status"] == "passed"
    assert result["checked_cases"] == 6
    assert result["strata"] == {"primary_target": 2, "other_role_target": 2, "other_background": 2}
    assert result["student_manual_review"] == "pending"


def test_independent_check_detects_lost_drug_record(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    output = tmp_path / "lost_record"
    build(sources, mapping, output)
    with duckdb.connect(str(output / "analytical.duckdb")) as c:
        c.execute("DELETE FROM case_drugs WHERE case_id='1' AND route='Other'")
    with pytest.raises(ValueError, match="spot-check failed"):
        spotcheck_sources(output / "analytical.duckdb", sources, output)


def test_real_arff_export_keeps_empty_background_and_unexposed_drug(real_format_sources, tmp_path):
    sources, mapping = real_format_sources
    output = tmp_path / "mart"
    build(sources, mapping, output)
    database = output / "analytical.duckdb"
    before = sha256(database)
    exported = tmp_path / "export"
    result = export_mart_arff(database, exported)
    assert result["eligible_n"] == 6
    assert result["empty_transactions"] == 1
    assert result["attributes"] == [
        "DRUG_atorvastatin",
        "DRUG_rosuvastatin",
        "REAC_REACTION X",
        "REAC_REACTION Y",
    ]
    assert sha256(database) == before
    rows = (exported / "transactions.arff").read_text().split("@data\n")[1].splitlines()
    assert len(rows) == 6 and rows[-1] == "{}"
    with (exported / "case_index.csv").open(newline="") as stream:
        index = list(csv.DictReader(stream))
    assert index[-1]["case_id"] == "6" and index[0]["primary_id"] == "11"
    with pytest.raises(ValueError, match="new output directory"):
        export_mart_arff(database, exported)


@pytest.mark.weka
def test_tiny_mart_through_actual_weka_and_evaluation(real_format_sources, tmp_path):
    jar = os.environ.get("WEKA_JAR")
    if not jar:
        pytest.skip("Set WEKA_JAR")
    sources, mapping = real_format_sources
    build(sources, mapping, tmp_path / "mart")
    database = tmp_path / "mart/analytical.duckdb"
    output = tmp_path / "experiment"
    export_mart_arff(database, output / "input")
    run_apriori(
        output / "input/transactions.arff",
        output / "weka",
        jar=Path(jar),
        supports=[0.1, 0.4],
        min_lift=1.2,
        max_rules=10000,
        expected_n=6,
    )
    result = evaluate_experiment(
        database,
        output,
        {"top_k": [1, 10]},
        {"weka": {"support_grid": [0.1, 0.4], "min_metric": 1.2}},
        {
            "pairs": [
                {"drug": "atorvastatin", "reaction": "REACTION Y"},
                {"drug": "atorvastatin", "reaction": "REACTION Z"},
            ]
        },
    )
    assert result["status"] == "computational_gates_passed"
    assert [r["accepted_pairs"] for r in result["support_runs"]] == [1, 0]
    assert all(result["checks"].values())
    positives = read_csv(output / "evaluation/benchmark_recovery.csv")
    assert len(positives) == 4
    assert positives[0]["status"] == "recovered"
    assert positives[1]["status"] == "below_support_count"
    assert positives[2]["status"] == "not_in_candidate_vocabulary"
    assert int(positives[2]["c"]) == 1  # Filtered term retains its actual background count.
