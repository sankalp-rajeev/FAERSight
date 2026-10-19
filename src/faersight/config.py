"""Validate planning configuration without inventing unresolved research decisions."""

import math
import re
from pathlib import Path

import yaml

from faersight.acquire import official_url
from faersight.normalize import load_mapping


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


def load_ingestion_config(path: Path) -> tuple[dict, dict, Path]:
    config, _ = load_experiment(path, require_frozen=True)
    root = path.resolve().parent.parent
    sources = config.get("sources")
    if not isinstance(sources, list) or len(sources) != len(config["quarters"]):
        raise ValueError("One frozen FDA source is required per selected quarter")
    source_quarters = []
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Each source must be a mapping")
        source_quarters.append(source.get("quarter"))
        official_url(source.get("url", ""))
        official_url(source.get("source_page", ""))
        if not re.fullmatch(r"[a-f0-9]{64}", str(source.get("sha256", ""))):
            raise ValueError("Each source must have a frozen SHA-256")
        name = source.get("archive_name", "")
        if not isinstance(name, str) or Path(name).name != name or not name.endswith(".zip"):
            raise ValueError("archive_name must be a simple ZIP filename")
        if type(source.get("bytes")) is not int or source["bytes"] < 1:
            raise ValueError("Each source must have a positive frozen byte size")
    if sorted(source_quarters) != sorted(config["quarters"]):
        raise ValueError("Source quarters differ from the frozen scope")
    ingestion = config.get("ingestion", {})
    required = {
        "eligibility": "latest_report_with_drug_and_nonblank_reaction",
        "deleted_case_policy": "exclude_union_of_selected_quarters",
        "missing_primary_suspect_policy": "preserve_without_imputation",
    }
    if any(ingestion.get(key) != value for key, value in required.items()):
        raise ValueError("Unsupported or missing eligibility/deletion/role-imputation policy")
    if ingestion.get("encoding") not in {"ascii", "utf-8", "latin-1"}:
        raise ValueError("Source encoding must be explicitly selected")
    if not re.fullmatch(r"[1-9]\d*(MB|GB)", str(ingestion.get("memory_limit", ""))):
        raise ValueError("memory_limit must be an integer MB or GB quantity")
    if type(ingestion.get("threads")) is not int or not 1 <= ingestion["threads"] <= 32:
        raise ValueError("threads must be between 1 and 32")
    class_path = (root / config.get("therapeutic_class_file", "")).resolve()
    if not class_path.is_relative_to(root) or not class_path.is_file():
        raise ValueError("therapeutic_class_file must exist within the project")
    with class_path.open(encoding="utf-8") as stream:
        therapeutic_class = yaml.safe_load(stream)
    if (
        not isinstance(therapeutic_class, dict)
        or therapeutic_class.get("status") != "frozen"
        or therapeutic_class.get("name") != config["therapeutic_class"]
    ):
        raise ValueError("Therapeutic class must be frozen and match experiment scope")
    ingredients = therapeutic_class.get("ingredients")
    if (
        not isinstance(ingredients, list)
        or not ingredients
        or any(not isinstance(x, str) or not x.strip() for x in ingredients)
        or len(ingredients) != len(set(ingredients))
    ):
        raise ValueError("Expected unique canonical ingredients")
    if (
        therapeutic_class.get("mapping_policy")
        != "exact_ingredient_tokens_in_prod_ai_then_reviewed_drugname_alias"
        or therapeutic_class.get("active_ingredient_separator") != "\\"
    ):
        raise ValueError("Unsupported ingredient mapping policy")
    mapping_path = (root / therapeutic_class.get("mapping_file", "")).resolve()
    if not mapping_path.is_relative_to(root):
        raise ValueError("mapping_file must be within the project")
    mapping = load_mapping(mapping_path)
    if set(mapping.values()) != set(ingredients):
        raise ValueError("Reviewed mapping must cover exactly the frozen class ingredients")
    return config, therapeutic_class, mapping_path
