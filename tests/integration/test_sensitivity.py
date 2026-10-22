import json
import os
from pathlib import Path

import duckdb
import pytest

from faersight.arff import export_mart_arff
from faersight.audit import sha256
from faersight.evaluation import verify_weka
from faersight.integration import build_full_mart
from faersight.manual_review import make_review_package
from faersight.mining import read_csv, run_apriori
from faersight.sensitivity import (
    build_sensitivity_mart,
    compare_roles,
    load_sensitivity_config,
    read_signals,
)


@pytest.fixture
def primary(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    demo, drug, reac, deleted = [source / name for name in ("demo", "drug", "reac", "deleted")]
    demo.write_text(
        "primaryid$caseid$caseversion\n" + "".join(f"{i}0${i}$1\n" for i in range(1, 9))
    )
    drug.write_text(
        "primaryid$caseid$drug_seq$role_cod$drugname$prod_ai\n"
        "10$1$1$PS$ATORVASTATIN$ATORVASTATIN\n"
        "20$2$1$PS$CRESTOR$ROSUVASTATIN\n"
        "30$3$1$SS$EZETIMIBE\\ROSUVASTATIN ZINC$EZETIMIBE\\ROSUVASTATIN ZINC\n"
        "40$4$1$PS$CRESTOR$ROSUVASTATIN\n"
        "40$4$2$SS$EZETIMIBE\\ROSUVASTATIN ZINC$EZETIMIBE\\ROSUVASTATIN ZINC\n"
        "50$5$1$SS$ATORVASTATIN$ATORVASTATIN\n"
        "60$6$1$C$EZETIMIBE\\ROSUVASTATIN ZINC$EZETIMIBE\\ROSUVASTATIN ZINC\n"
        "70$7$1$PS$BACKGROUND$\n80$8$1$PS$BACKGROUND$\n"
    )
    reac.write_text(
        "primaryid$caseid$pt\n"
        + "".join(
            f"{i}0${i}${pt}\n"
            for i, pts in {
                1: "XY",
                2: "Y",
                3: "XYZ",
                4: "Y",
                5: "XZ",
                6: "X",
                7: "Y",
                8: "X",
            }.items()
            for pt in pts
        )
    )
    deleted.write_text("9999\n")
    sources = [
        {
            "quarter": "2025Q4",
            "paths": {"DEMO": demo, "DRUG": drug, "REAC": reac, "DELETE": deleted},
        }
    ]
    output = tmp_path / "primary"
    build_full_mart(
        sources,
        output,
        mapping_path=Path("mappings/drug_mapping.csv"),
        ingredients=[
            "atorvastatin",
            "fluvastatin",
            "lovastatin",
            "pitavastatin",
            "pravastatin",
            "rosuvastatin",
            "simvastatin",
        ],
        therapeutic_class="statins",
        roles=["PS"],
        min_target_cases=1,
    )
    return output / "analytical.duckdb"


def derive(primary, tmp_path):
    return build_sensitivity_mart(
        primary,
        tmp_path / "derived",
        Path("mappings/sensitivity_ss_aliases.csv"),
        Path("mappings/sensitivity_ss_review.yaml"),
    )


def test_role_sensitivity_preserves_population_vocab_and_exact_overlay(primary, tmp_path):
    original_hash = sha256(primary)
    derived, record = derive(primary, tmp_path)
    assert sha256(primary) == original_hash
    assert record["eligible_n"] == 8 and record["target_exposed_n"] == 5
    assert record["without_overlay_exposed_n"] == 4
    assert record["mapping_source_rows_resolved"] == 2
    assert record["deferred_new_reactions"] == 1
    assert all(record["checks"].values())
    with duckdb.connect(str(derived), read_only=True) as c:
        assert c.execute("SELECT drug FROM case_drug_presence WHERE case_id='3'").fetchall() == [
            ("rosuvastatin",)
        ]
        assert (
            c.execute("SELECT count(*) FROM case_drug_presence WHERE case_id='4'").fetchone()[0]
            == 1
        )
        assert (
            c.execute("SELECT count(*) FROM case_drug_presence WHERE case_id='6'").fetchone()[0]
            == 0
        )
        assert (
            c.execute("SELECT canonical_ingredient FROM case_drugs WHERE role_code='C'").fetchone()[
                0
            ]
            is None
        )
        assert (
            c.execute(
                "SELECT count(*) FROM drug_mapping WHERE raw_name='ROSUVASTATIN ZINC'"
            ).fetchone()[0]
            == 0
        )
    counts = {(r["drug"], r["reaction"]): r for r in read_signals(derived)}
    assert counts["rosuvastatin", "X"]["a"] == 1
    assert counts["rosuvastatin", "Y"]["a"] == 3
    assert all(r["n"] == 8 for r in counts.values())
    with pytest.raises(ValueError, match="exists"):
        derive(primary, tmp_path)


def test_new_unreviewed_ss_candidate_fails_closed(primary, tmp_path):
    # A new target-like unknown must not silently enter a sensitivity experiment.
    with duckdb.connect(str(primary)) as c:
        c.execute(
            "UPDATE case_drugs SET normalized_name='UNKNOWN STATIN', "
            "normalized_prod_ai='UNKNOWN',is_unmapped_target_candidate=true "
            "WHERE role_code='SS' AND case_id='5'"
        )
        c.execute("CHECKPOINT")
    manifest = primary.parent / "integration_manifest.json"
    record = json.loads(manifest.read_text())
    record["artifacts"][primary.name] = sha256(primary)
    manifest.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="Unreviewed"):
        derive(primary, tmp_path)


def test_frozen_primary_contract_and_additional_sensitivity_hashes():
    _, _, experiment, benchmark, hashes = load_sensitivity_config(Path("config/sensitivity.yaml"))
    assert experiment["quarters"] == ["2025Q4"] and experiment["drug_roles"] == ["PS"]
    assert len(benchmark["pairs"]) == 8
    assert Path("mappings/sensitivity_ss_aliases.csv").resolve() in hashes


@pytest.mark.weka
def test_actual_weka_role_difference_and_manual_packet(primary, tmp_path):
    if not os.environ.get("WEKA_JAR"):
        pytest.skip("Set WEKA_JAR to exercise actual WEKA")
    derived, _ = derive(primary, tmp_path)
    signals, runs = {}, {}
    benchmark = {
        "pairs": [{"drug": "rosuvastatin", "reaction": "X", "source": "toy"}],
        "sources": {"toy": {"url": "https://example.invalid/toy"}},
    }
    for role, database in [("PS", primary), ("PS+SS", derived)]:
        folder = tmp_path / role.replace("+", "_")
        export_mart_arff(database, folder / "input")
        run_apriori(
            folder / "input/transactions.arff",
            folder / "weka",
            jar=Path(os.environ["WEKA_JAR"]),
            supports=[0.1],
            min_lift=1.0,
            max_rules=10000,
            expected_n=8,
        )
        signals[role] = read_signals(database)
        runs[role] = verify_weka(
            read_csv(folder / "weka/weka_rules.csv"),
            read_csv(folder / "weka/weka_runs.csv"),
            signals[role],
            supports=[0.1],
            min_lift=1.0,
            n=8,
        )
    comparison = compare_roles(signals["PS"], signals["PS+SS"], runs, [1, 2])
    assert comparison["support_comparison"][0]["ps_rules"] > 0
    result = make_review_package(primary, derived, tmp_path / "review", signals, runs, benchmark)
    assert result["automated_source_checks"] == "passed"
    assert not result["student_review_completed"]
    cases = json.loads((tmp_path / "review/cases.json").read_text())
    assert any("exact_SS_alias_correction" in r["reasons"] for r in cases)
