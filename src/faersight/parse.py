"""Strict streaming parser for dollar-delimited DEMO/DRUG/REAC extracts."""

import csv
from collections.abc import Iterator
from pathlib import Path

REQUIRED = {
    "DEMO": {"primaryid", "caseid", "caseversion"},
    "DRUG": {"primaryid", "role_cod", "drugname"},
    "REAC": {"primaryid", "pt"},
}


def read_table(path: Path, table: str, *, encoding: str = "utf-8-sig") -> Iterator[dict]:
    """Reject malformed rows with locations; never silently skip source records.

    Real-quarter encodings must be chosen from that quarter's retained README.
    """
    required = REQUIRED[table]
    with path.open(encoding=encoding, newline="") as stream:
        reader = csv.reader(stream, delimiter="$", quoting=csv.QUOTE_NONE)
        try:
            header = [field.strip().lower() for field in next(reader)]
        except StopIteration as exc:
            raise ValueError(f"{path}: empty {table} file") from exc
        if len(header) != len(set(header)) or not required <= set(header):
            raise ValueError(f"{path}: invalid {table} header; requires {sorted(required)}")
        for line_number, fields in enumerate(reader, 2):
            if len(fields) != len(header):
                raise ValueError(
                    f"{path}:{line_number}: expected {len(header)} fields, received {len(fields)}"
                )
            row = dict(zip(header, (value.strip() for value in fields), strict=True))
            if any(not row[field] for field in required):
                raise ValueError(f"{path}:{line_number}: blank required {table} field")
            yield row
