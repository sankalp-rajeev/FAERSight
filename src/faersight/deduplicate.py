"""Deterministic DEMO-driven case-version selection across configured quarters."""

import re
from collections.abc import Iterable


def latest_cases(rows: Iterable[dict]) -> list[dict]:
    """Choose max (caseversion, primaryid, quarter) per case, as numeric IDs.

    Selection precedes drug/reaction eligibility: a missing latest relation must
    not resurrect a stale case version. Conflicting same-report metadata fails.
    """
    reports: dict[str, dict] = {}
    cases: dict[str, dict] = {}
    for row in rows:
        if any(
            not row[field].isascii() or not row[field].isdigit()
            for field in ("primaryid", "caseid", "caseversion")
        ):
            raise ValueError("DEMO identifiers and caseversion must be nonnegative integers")
        if int(row["caseversion"]) < 1 or not re.fullmatch(r"20\d{2}Q[1-4]", row["quarter"]):
            raise ValueError("Invalid case version or quarter")
        prior = reports.get(row["primaryid"])
        if prior and any(prior[key] != row[key] for key in ("caseid", "caseversion")):
            raise ValueError(f"Conflicting DEMO metadata for primaryid {row['primaryid']}")
        reports[row["primaryid"]] = row

        def key(record: dict) -> tuple[int, int, str]:
            return int(record["caseversion"]), int(record["primaryid"]), record["quarter"]

        old = cases.get(row["caseid"])
        if old is None or key(row) > key(old):
            cases[row["caseid"]] = row
    return sorted(cases.values(), key=lambda row: int(row["caseid"]))
