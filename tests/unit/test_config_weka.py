from pathlib import Path

import pytest
import yaml

from faersight.config import load_experiment
from faersight.weka import parse_rules

EXAMPLE = Path(__file__).parents[2] / "config" / "experiment.example.yaml"


def test_template_is_valid_but_not_frozen():
    _, pending = load_experiment(EXAMPLE)
    assert "quarters" in pending and "therapeutic_class" in pending
    with pytest.raises(ValueError, match="not frozen"):
        load_experiment(EXAMPLE, require_frozen=True)


def test_complete_configuration_can_be_frozen(tmp_path):
    config = yaml.safe_load(EXAMPLE.read_text())
    config.update(
        status="frozen",
        quarters=["2025Q1"],
        therapeutic_class="synthetic",
        reaction_min_target_cases=2,
    )
    config["weka"].update(support_grid=[0.1, 0.2], min_metric=1.2)
    path = tmp_path / "frozen.yaml"
    path.write_text(yaml.safe_dump(config))
    _, pending = load_experiment(path, require_frozen=True)
    assert not pending


@pytest.mark.parametrize(
    "field,value",
    [
        ("quarters", ["2025Q1"] * 2),
        ("quarters", ["2025Q5"]),
        ("drug_roles", ["C"]),
        ("reaction_min_target_cases", 0),
    ],
)
def test_invalid_configuration(tmp_path, field, value):
    config = yaml.safe_load(EXAMPLE.read_text())
    config[field] = value
    path = tmp_path / "experiment.yaml"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError):
        load_experiment(path)


def test_direction_and_single_item_filtering():
    output = """
1. DRUG_alpha=1 4 ==> REAC_REACTION X=1 3 conf:(0.75) <lift:(1.88)> lev:(0.14)
2. REAC_REACTION X=1 4 ==> DRUG_alpha=1 3 conf:(0.75) <lift:(1.88)>
3. DRUG_alpha=1 DRUG_beta=1 4 ==> REAC_REACTION X=1 3 conf:(0.75) <lift:(1.88)>
"""
    rules = parse_rules(output)
    assert len(rules) == 1
    assert rules[0].drug == "alpha" and rules[0].reaction == "REACTION X"
    assert rules[0].joint_count == 3 and rules[0].weka_lift == 1.88


def test_absence_rules_fail_globally():
    with pytest.raises(ValueError, match="absence"):
        parse_rules("1. REAC_X=0 8 ==> DRUG_alpha=1 3 conf:(0.5) lift:(1.5)")


def test_malformed_rule_fails_instead_of_disappearing():
    with pytest.raises(ValueError, match="format"):
        parse_rules("1. DRUG_alpha=1 ==> REAC_X=1 changed-format")
