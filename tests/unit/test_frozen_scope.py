from pathlib import Path

import pytest

from faersight.config import load_ingestion_config
from faersight.normalize import load_mapping, normalized_name

ROOT = Path(__file__).parents[2]


def test_real_scope_is_frozen_with_pinned_official_source():
    config, therapeutic_class, mapping = load_ingestion_config(ROOT / "config/experiment.yaml")
    assert config["quarters"] == ["2025Q4"]
    assert config["sources"][0]["bytes"] == 67144585
    assert config["drug_roles"] == ["PS"]
    assert len(therapeutic_class["ingredients"]) == 7
    assert set(load_mapping(mapping).values()) == set(therapeutic_class["ingredients"])


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  lipitor  ", "atorvastatin"),
        ("atorvastatin\tcalcium", "atorvastatin"),
        ("LESCOL XL", "fluvastatin"),
        ("ALTOPREV", "lovastatin"),
        ("PITAVASTATIN MAGNESIUM", "pitavastatin"),
        ("PRAVASTATIN SODIUM", "pravastatin"),
        ("CRESTOR", "rosuvastatin"),
        ("VYTORIN", "simvastatin"),
    ],
)
def test_reviewed_statin_aliases(raw, expected):
    mapping = load_mapping(ROOT / "mappings/drug_mapping.csv")
    assert mapping[normalized_name(raw)] == expected
