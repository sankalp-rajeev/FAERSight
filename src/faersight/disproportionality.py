"""Independent count-based verification; no association-rule search happens here."""

import math
from dataclasses import dataclass

from faersight.transactions import Transaction


@dataclass(frozen=True)
class Counts:
    a: int
    b: int
    c: int
    d: int

    def __post_init__(self) -> None:
        if any(type(value) is not int or value < 0 for value in (self.a, self.b, self.c, self.d)):
            raise ValueError("Contingency cells must be nonnegative integers")

    @property
    def n(self) -> int:
        return self.a + self.b + self.c + self.d


def ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return math.inf if numerator > 0 else math.nan
    return numerator / denominator


def metrics(counts: Counts) -> dict:
    a, b, c, d = counts.a, counts.b, counts.c, counts.d
    confidence = ratio(a, a + b)
    values = {
        "support": ratio(a, counts.n),
        "confidence": confidence,
        "lift_python_check": ratio(confidence, ratio(a + c, counts.n)),
        "prr": ratio(confidence, ratio(c, c + d)),
        "ror": ratio(a * d, b * c),
    }
    flags = [
        f"{key}_{'undefined' if math.isnan(value) else 'infinite'}"
        for key, value in values.items()
        if not math.isfinite(value)
    ]
    return {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "n": counts.n,
        **values,
        "zero_cell": min(a, b, c, d) == 0,
        "score_flags": ";".join(flags),
    }


def count_pair(transactions: list[Transaction], drug: str, reaction: str) -> Counts:
    if len({t.case_id for t in transactions}) != len(transactions):
        raise ValueError("Duplicate cases would change the analysis universe")
    cells = [0, 0, 0, 0]
    for txn in transactions:
        exposed, event = drug in txn.drugs, reaction in txn.reactions
        cells[0 if exposed and event else 1 if exposed else 2 if event else 3] += 1
    return Counts(*cells)


def signal_rows(transactions: list[Transaction]) -> list[dict]:
    drugs = sorted({drug for txn in transactions for drug in txn.drugs})
    reactions = sorted({reaction for txn in transactions for reaction in txn.reactions})
    return [
        {"drug": drug, "reaction": reaction, **metrics(count_pair(transactions, drug, reaction))}
        for drug in drugs
        for reaction in reactions
    ]
