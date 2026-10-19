from pathlib import Path

import pytest

from faersight.normalize import load_mapping
from faersight.parse import read_table
from faersight.transactions import build_transactions

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def source_rows():
    demo = [{**row, "quarter": "2025Q1"} for row in read_table(FIXTURES / "DEMO.txt", "DEMO")]
    return (
        demo,
        list(read_table(FIXTURES / "DRUG.txt", "DRUG")),
        list(read_table(FIXTURES / "REAC.txt", "REAC")),
    )


@pytest.fixture
def transactions(source_rows):
    return build_transactions(
        *source_rows, load_mapping(FIXTURES / "drug_mapping.csv"), min_target_cases=2
    )[0]
