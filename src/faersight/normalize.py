"""Exact reviewed aliases only; unknown names remain unmapped."""

import csv
from pathlib import Path


def normalized_name(value: str) -> str:
    return " ".join(value.upper().split())


def load_mapping(path: Path) -> dict[str, str]:
    result = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"raw_name", "canonical_ingredient", "mapping_basis", "reviewed"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("Drug mapping is missing required columns")
        for row in reader:
            if row["reviewed"].strip().lower() != "true":
                raise ValueError("Only reviewed mappings may enter the experiment")
            raw = normalized_name(row["raw_name"])
            canonical = row["canonical_ingredient"].strip()
            if not raw or not canonical or not row["mapping_basis"].strip():
                raise ValueError("Mapping names and evidence must be nonempty")
            if raw in result and result[raw] != canonical:
                raise ValueError(f"Conflicting mapping for {raw}")
            result[raw] = canonical
    if not result:
        raise ValueError("Drug mapping cannot be empty")
    return result
