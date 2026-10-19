from pathlib import Path

from faersight.audit import sha256
from faersight.pipeline import build_fixture

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_fixture_artifacts_are_order_stable(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    build_fixture(FIXTURES, first)
    build_fixture(FIXTURES, second)
    for name in (
        "transactions.arff",
        "case_index.csv",
        "preprocess_audit.json",
        "signal_counts.csv",
        "manifest.json",
    ):
        assert sha256(first / name) == sha256(second / name)


def test_frozen_statistics_csv(tmp_path):
    build_fixture(FIXTURES, tmp_path)
    assert (tmp_path / "signal_counts.csv").read_text() == (
        "drug,reaction,a,b,c,d,n,support,confidence,lift_python_check,prr,ror,zero_cell,score_flags\n"
        "alpha,REACTION X,3,1,1,5,10,0.3,0.75,1.875,4.5,15.0,False,\n"
    )
