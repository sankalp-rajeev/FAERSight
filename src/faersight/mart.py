"""A small local DuckDB mart for fixture validation of the mining representation."""

from pathlib import Path

import duckdb

from faersight.transactions import Transaction


def write_mart(path: Path, transactions: list[Transaction]) -> None:
    """Store deduplicated cases and selected presence items, not raw drug records.

    The full retained drug/reaction record mart is a later real-data milestone.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(path)) as connection:
        connection.execute("BEGIN TRANSACTION")
        for table in ("cases", "case_items"):
            connection.execute(f"DROP TABLE IF EXISTS {table}")
        connection.execute(
            "CREATE TABLE cases (case_id VARCHAR PRIMARY KEY, primary_id VARCHAR, quarter VARCHAR)"
        )
        connection.execute(
            "CREATE TABLE case_items (case_id VARCHAR, "
            "item_type VARCHAR, item_value VARCHAR, "
            "PRIMARY KEY (case_id, item_type, item_value))"
        )
        if transactions:
            connection.executemany(
                "INSERT INTO cases VALUES (?, ?, ?)",
                [(t.case_id, t.primary_id, t.quarter) for t in transactions],
            )
        items = [
            (t.case_id, kind, value)
            for t in transactions
            for kind, values in (("DRUG", t.drugs), ("REAC", t.reactions))
            for value in sorted(values)
        ]
        if items:
            connection.executemany("INSERT INTO case_items VALUES (?, ?, ?)", items)
        connection.execute(
            "CREATE OR REPLACE VIEW item_summary AS "
            "SELECT quarter, item_type, item_value, count(*) AS report_count "
            "FROM cases JOIN case_items USING (case_id) GROUP BY ALL"
        )
        connection.execute("COMMIT")
