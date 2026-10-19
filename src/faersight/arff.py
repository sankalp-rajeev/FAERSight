"""Deterministic nominal-binary sparse ARFF; absent values use index zero."""

from pathlib import Path

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
