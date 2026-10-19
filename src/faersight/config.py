"""Validate planning configuration without inventing unresolved research decisions."""

import math
import re
from pathlib import Path

import yaml


def load_experiment(path: Path, *, require_frozen: bool = False) -> tuple[dict, list[str]]:
    try:
        with path.open(encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise ValueError("Expected a schema_version: 1 experiment mapping")
    if config.get("status") not in {"draft", "frozen"}:
        raise ValueError("status must be draft or frozen")
    quarters = config.get("quarters")
    if (
        not isinstance(quarters, list)
        or len(quarters) > 2
        or any(not isinstance(q, str) or not re.fullmatch(r"20\d{2}Q[1-4]", q) for q in quarters)
        or len(set(quarters)) != len(quarters)
    ):
        raise ValueError("quarters must contain at most two unique YYYYQ1..YYYYQ4 strings")
    roles = config.get("drug_roles")
    if roles not in (["PS"], ["PS", "SS"]):
        raise ValueError("drug_roles must be [PS] or [PS, SS]")
    weka = config.get("weka")
    if not isinstance(weka, dict):
        raise ValueError("weka must be a mapping")
    if (
        weka.get("metric") != "lift"
        or weka.get("treat_zero_as_missing") is not True
        or str(weka.get("version")) != "3.8.6"
    ):
        raise ValueError("Expected WEKA 3.8.6, metric lift and treat_zero_as_missing: true")
    grid = weka.get("support_grid")
    if not isinstance(grid, list):
        raise ValueError("weka.support_grid must be a list")
    if any(type(x) not in (int, float) or not math.isfinite(x) or not 0 < x <= 1 for x in grid):
        raise ValueError("Every support threshold must be finite and in (0, 1]")
    count = config.get("reaction_min_target_cases")
    if count is not None and (type(count) is not int or count < 1):
        raise ValueError("reaction_min_target_cases must be a positive integer")
    minimum = weka.get("min_metric")
    if minimum is not None and (
        type(minimum) not in (int, float) or not math.isfinite(minimum) or minimum <= 0
    ):
        raise ValueError("weka.min_metric must be positive and finite")
    if type(weka.get("max_rules")) is not int or weka["max_rules"] < 1:
        raise ValueError("weka.max_rules must be a positive integer")
    class_name = config.get("therapeutic_class")
    if class_name is not None and (not isinstance(class_name, str) or not class_name.strip()):
        raise ValueError("therapeutic_class must be a nonempty string or null")
    pending = [
        name
        for name, value in {
            "quarters": quarters,
            "therapeutic_class": class_name,
            "reaction_min_target_cases": count,
            "weka.support_grid": grid,
            "weka.min_metric": minimum,
        }.items()
        if value is None or value == []
    ]
    if (require_frozen or config["status"] == "frozen") and (
        config["status"] != "frozen" or pending
    ):
        raise ValueError("Experiment is not frozen; unresolved: " + ", ".join(pending))
    return config, pending
