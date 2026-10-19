"""Executable synthetic milestone; deliberately separate from real FDA experiments."""

import platform
from dataclasses import asdict
from pathlib import Path

from faersight.arff import write_arff
from faersight.audit import sha256, write_json
from faersight.disproportionality import signal_rows
from faersight.mart import write_mart
from faersight.normalize import load_mapping
from faersight.parse import read_table
from faersight.transactions import build_transactions
from faersight.weka import run_smoke, write_csv


def build_fixture(fixtures: Path, output: Path) -> dict:
    demo = [{**row, "quarter": "2025Q1"} for row in read_table(fixtures / "DEMO.txt", "DEMO")]
    drugs = list(read_table(fixtures / "DRUG.txt", "DRUG"))
    reactions = list(read_table(fixtures / "REAC.txt", "REAC"))
    mapping_path = fixtures / "drug_mapping.csv"
    transactions, audit = build_transactions(
        demo, drugs, reactions, load_mapping(mapping_path), min_target_cases=2
    )
    output.mkdir(parents=True, exist_ok=True)
    items = write_arff(output / "transactions.arff", transactions)
    write_json(output / "preprocess_audit.json", audit)
    write_csv(
        output / "case_index.csv",
        [
            {"row": i, "case_id": t.case_id, "primary_id": t.primary_id, "quarter": t.quarter}
            for i, t in enumerate(transactions)
        ],
    )
    signals = signal_rows(transactions)
    write_csv(output / "signal_counts.csv", signals)
    write_mart(output / "analytical.duckdb", transactions)
    write_json(
        output / "manifest.json",
        {
            "dataset": "synthetic_only",
            "python_version": platform.python_version(),
            "eligible_n": len(transactions),
            "attributes": items,
            "role_policy": ["PS"],
            "reaction_min_target_cases": 2,
            "sources": {
                name: sha256(fixtures / name)
                for name in ("DEMO.txt", "DRUG.txt", "REAC.txt", "drug_mapping.csv")
            },
            "artifacts": {
                name: sha256(output / name)
                for name in (
                    "transactions.arff",
                    "preprocess_audit.json",
                    "case_index.csv",
                    "signal_counts.csv",
                )
            },
        },
    )
    return {"eligible_n": len(transactions), "attributes": len(items), "signals": signals}


def reproduce_fixture(fixtures: Path, output: Path, *, jar: Path, java: str | None = None) -> dict:
    result = build_fixture(fixtures, output)
    rules = run_smoke(output / "transactions.arff", output / "weka", jar=jar, java=java)
    lookup = {(rule.drug, rule.reaction): rule for rule in rules}
    comparison = []
    for signal in result["signals"]:
        rule = lookup.get((signal["drug"], signal["reaction"]))
        if rule and (
            rule.joint_count != signal["a"] or rule.antecedent_count != signal["a"] + signal["b"]
        ):
            raise ValueError("WEKA and PRR/ROR counts disagree")
        comparison.append(
            {
                **signal,
                "weka_rank": rule.weka_rank if rule else "",
                "weka_lift": rule.weka_lift if rule else "",
                "weka_confidence": rule.weka_confidence if rule else "",
            }
        )
    write_csv(output / "comparison.csv", comparison)
    write_json(
        output / "repro_manifest.json",
        {
            "dataset": "synthetic_only",
            "eligible_n": result["eligible_n"],
            "accepted_rules": [asdict(rule) for rule in rules],
            "comparison_sha256": sha256(output / "comparison.csv"),
            "preprocess_manifest_sha256": sha256(output / "manifest.json"),
            "weka_manifest_sha256": sha256(output / "weka" / "manifest.json"),
        },
    )
    return result
