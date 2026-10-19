"""Strict streaming parser for dollar-delimited DEMO/DRUG/REAC extracts."""

import csv
from collections.abc import Iterator
from pathlib import Path

from faersight.audit import sha256, write_json

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


def stage_relation(
    source: Path, table: str, quarter: str, target: Path, *, encoding: str = "ascii"
) -> dict:
    """Validate and transcode one record at a time for DuckDB's native CSV loader.

    Preserve every source column. Blank drug names, role codes and PTs are data
    quality counters, not reasons to discard entire reports during parsing.
    Physical source rows and quarter travel with every ingested record.
    """
    required = REQUIRED[table] | {"caseid"}
    if table == "DRUG":
        required |= {"drug_seq", "prod_ai"}
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    count = 0
    blanks = {field: 0 for field in sorted(required)}
    with source.open(encoding=encoding, errors="strict", newline="") as input_stream:
        reader = csv.reader(input_stream, delimiter="$", quoting=csv.QUOTE_NONE)
        try:
            header = [name.strip().lower() for name in next(reader)]
        except StopIteration as exc:
            raise ValueError(f"{source}: empty source") from exc
        if (
            len(header) != len(set(header))
            or not required <= set(header)
            or any(not name or name.startswith("_") for name in header)
        ):
            raise ValueError(f"{source}: invalid {table} schema; requires {sorted(required)}")
        with partial.open("w", encoding="utf-8", newline="") as output_stream:
            writer = csv.writer(output_stream, lineterminator="\n")
            writer.writerow(["_source_row", "_quarter", *header])
            for source_row, fields in enumerate(reader, 2):
                if len(fields) != len(header):
                    raise ValueError(
                        f"{source}:{source_row}: malformed row: expected "
                        f"{len(header)} fields, got {len(fields)}"
                    )
                record = dict(zip(header, fields, strict=True))
                if not record["primaryid"].strip() or not record["caseid"].strip():
                    raise ValueError(f"{source}:{source_row}: missing report/case identity")
                for field in required:
                    blanks[field] += not record[field].strip()
                writer.writerow([source_row, quarter, *fields])
                count += 1
    partial.replace(target)
    audit = {
        "table": table,
        "quarter": quarter,
        "source_path": source.as_posix(),
        "source_sha256": sha256(source),
        "source_bytes": source.stat().st_size,
        "encoding": encoding,
        "header": header,
        "source_rows": count,
        "blank_required_values": blanks,
        "malformed_rows": 0,
        "staged_path": target.as_posix(),
        "staged_sha256": sha256(target),
    }
    write_json(target.with_suffix(".audit.json"), audit)
    return audit
