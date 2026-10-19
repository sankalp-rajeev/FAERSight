from pathlib import Path

import pytest

from faersight.deduplicate import latest_cases
from faersight.normalize import load_mapping
from faersight.parse import read_table
from faersight.transactions import build_transactions

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_numeric_version_order_and_quarter_overlap():
    rows = [
        {"primaryid": pid, "caseid": "1", "caseversion": version, "quarter": quarter}
        for pid, version, quarter in [
            ("2", "2", "2025Q1"),
            ("9", "10", "2025Q2"),
            ("10", "10", "2025Q1"),
        ]
    ]
    assert latest_cases(rows)[0]["primaryid"] == "10"
    assert latest_cases(list(reversed(rows))) == latest_cases(rows)


def test_conflicting_primary_id_fails(source_rows):
    row = source_rows[0][0]
    with pytest.raises(ValueError, match="Conflicting"):
        latest_cases([row, {**row, "caseid": "200"}])


def test_exact_aliases_and_unknowns(source_rows):
    mapping = load_mapping(FIXTURES / "drug_mapping.csv")
    assert mapping["ALPHA BRAND"] == "alpha"
    assert "ALPHA BRNAD" not in mapping
    transactions, audit = build_transactions(*source_rows, mapping, min_target_cases=2)
    assert transactions[0].drugs == {"alpha"}
    assert transactions[0].primary_id == "11"
    assert audit["unmapped_eligible_role_names"] == {"BACKGROUND PRODUCT": 5}
    assert audit["orphan_drug_rows"] == audit["orphan_reaction_rows"] == 1


def test_role_sensitivity_preserves_background(source_rows):
    mapping = load_mapping(FIXTURES / "drug_mapping.csv")
    primary, _ = build_transactions(*source_rows, mapping)
    sensitivity, _ = build_transactions(*source_rows, mapping, roles=("PS", "SS"))
    assert len(primary) == len(sensitivity) == 10
    assert not primary[5].drugs
    assert sensitivity[5].drugs == {"alpha"}


def test_reactions_are_sets_and_empty_transactions_survive(transactions):
    assert transactions[0].reactions == {"REACTION X"}
    assert len(transactions) == 10
    assert transactions[-1].drugs == transactions[-1].reactions == frozenset()
    assert all("OLD REACTION" not in t.reactions for t in transactions)


def test_source_order_does_not_change_transactions_or_audit(source_rows):
    mapping = load_mapping(FIXTURES / "drug_mapping.csv")
    first = build_transactions(*source_rows, mapping, min_target_cases=2)
    second = build_transactions(
        *(list(reversed(rows)) for rows in source_rows), mapping, min_target_cases=2
    )
    assert first == second


def test_latest_missing_relation_does_not_resurrect_old_version(source_rows):
    demo, drugs, reactions = source_rows
    newer = {"primaryid": "12", "caseid": "1", "caseversion": "3", "quarter": "2025Q2"}
    transactions, audit = build_transactions(
        demo + [newer], drugs, reactions, load_mapping(FIXTURES / "drug_mapping.csv")
    )
    assert "1" not in {t.case_id for t in transactions}
    assert audit["excluded_latest_cases_missing_drug_or_reaction"] == 1


@pytest.mark.parametrize(
    "content",
    [
        "primaryid$caseid\n1$2\n",
        "primaryid$caseid$caseversion\n1$2\n",
        "primaryid$caseid$caseversion\n1$2$\n",
    ],
)
def test_malformed_rows_fail_with_context(tmp_path, content):
    source = tmp_path / "DEMO.txt"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="DEMO.txt"):
        list(read_table(source, "DEMO"))


def test_unreviewed_mapping_is_rejected(tmp_path):
    path = tmp_path / "mapping.csv"
    path.write_text("raw_name,canonical_ingredient,mapping_basis,reviewed\nA,a,guess,false\n")
    with pytest.raises(ValueError, match="reviewed"):
        load_mapping(path)
