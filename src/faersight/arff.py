"""Deterministic nominal-binary sparse ARFF; absent values use index zero."""

import csv
from pathlib import Path

import duckdb

from faersight.audit import sha256, write_json
from faersight.integration import validate_mart
from faersight.transactions import Transaction


def quote(value: str) -> str:
    return (
        "'"
        + value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
        + "'"
    )


def write_arff(path: Path, transactions: list[Transaction]) -> list[str]:
    if not transactions or len({t.case_id for t in transactions}) != len(transactions):
        raise ValueError("Expected nonempty, unique case transactions")
    items = sorted(
        {"DRUG_" + drug for t in transactions for drug in t.drugs}
        | {"REAC_" + reaction for t in transactions for reaction in t.reactions}
    )
    if not items:
        raise ValueError("No attributes survive the vocabulary filter")
    index = {item: i for i, item in enumerate(items)}
    lines = ["@relation faersight", ""]
    lines.extend(f"@attribute {quote(item)} {{0,1}}" for item in items)
    lines.extend(["", "@data"])
    for transaction in transactions:
        present = {index["DRUG_" + drug] for drug in transaction.drugs}
        present.update(index["REAC_" + reaction] for reaction in transaction.reactions)
        lines.append("{" + ",".join(f"{i} 1" for i in sorted(present)) + "}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return items


def export_mart_arff(database: Path, output: Path) -> dict:
    """Stream the complete eligible population; keep empty/background baskets."""
    quality = validate_mart(database)
    if quality["status"] != "passed":
        raise ValueError("Source mart failed validation")
    output.mkdir(parents=True, exist_ok=True)
    arff_path = output / "transactions.arff"
    if arff_path.exists():
        raise ValueError("ARFF snapshot exists; choose a new output directory")
    n = empty = 0
    with duckdb.connect(str(database), read_only=True) as connection:
        items = [
            "DRUG_" + row[0]
            for row in connection.execute(
                "SELECT drug FROM class_ingredients ORDER BY drug"
            ).fetchall()
        ] + [
            "REAC_" + row[0]
            for row in connection.execute(
                "SELECT reaction FROM candidate_reactions ORDER BY reaction"
            ).fetchall()
        ]
        if not items or len(items) != len(set(items)):
            raise ValueError("Invalid mining attribute vocabulary")
        index = {item: i for i, item in enumerate(items)}
        cursor = connection.execute("""
            SELECT c.case_id, c.primary_id, c.quarter,
                   list(i.item_type || '_' || i.item_value ORDER BY i.item_type, i.item_value)
                       FILTER (WHERE i.item_value IS NOT NULL) AS items
            FROM cases c LEFT JOIN case_items i USING(case_id)
            GROUP BY c.case_id, c.primary_id, c.quarter
            ORDER BY CAST(c.case_id AS BIGINT)
        """)
        with (
            arff_path.open("w", encoding="utf-8", newline="\n") as stream,
            (output / "case_index.csv").open("w", encoding="utf-8", newline="") as case_stream,
        ):
            stream.write("@relation faersight\n\n")
            for item in items:
                stream.write(f"@attribute {quote(item)} {{0,1}}\n")
            stream.write("\n@data\n")
            writer = csv.writer(case_stream, lineterminator="\n")
            writer.writerow(["row", "case_id", "primary_id", "quarter"])
            while rows := cursor.fetchmany(4096):
                for case_id, primary_id, quarter, present in rows:
                    indices = sorted(index[item] for item in present or [])
                    stream.write("{" + ",".join(f"{i} 1" for i in indices) + "}\n")
                    writer.writerow([n, case_id, primary_id, quarter])
                    n += 1
                    empty += not indices
    if n != quality["eligible_n"]:
        raise ValueError("Export changed the eligible reporting universe")
    manifest = {
        "eligible_n": n,
        "empty_transactions": empty,
        "attributes": items,
        "source_mart_sha256": sha256(database),
        "source_integration_manifest_sha256": sha256(database.parent / "integration_manifest.json"),
        "arff_sha256": sha256(arff_path),
        "case_index_sha256": sha256(output / "case_index.csv"),
        "scientific_findings_validated": False,
    }
    write_json(output / "manifest.json", manifest)
    return manifest
