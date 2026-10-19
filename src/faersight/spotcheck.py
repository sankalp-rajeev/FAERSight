"""Independent streaming source-to-mart checks on deterministic report samples."""

import csv
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from faersight.audit import sha256, write_json
from faersight.deduplicate import latest_cases
from faersight.normalize import normalized_name


def spotcheck_sources(
    database: Path,
    sources: list[dict],
    output: Path,
    *,
    per_stratum: int = 5,
    encoding: str = "ascii",
) -> dict:
    """Compare full raw drug rows, latest IDs, reaction and exposure memberships.

    This automated independent check does not replace the student's manual audit.
    Detailed case records stay beside the ignored database, not in Git evidence.
    """
    if not 1 <= per_stratum <= 50:
        raise ValueError("per_stratum must be between 1 and 50")
    with duckdb.connect(str(database), read_only=True) as connection:
        predicates = {
            "primary_target": (
                "EXISTS (SELECT 1 FROM case_drug_presence d WHERE d.case_id=c.case_id)"
            ),
            "other_role_target": """NOT EXISTS (SELECT 1 FROM case_drug_presence d
                WHERE d.case_id=c.case_id) AND EXISTS (SELECT 1 FROM case_drugs d
                WHERE d.case_id=c.case_id AND d.canonical_ingredient IS NOT NULL)""",
            "other_background": """NOT EXISTS (SELECT 1 FROM case_drugs d
                WHERE d.case_id=c.case_id AND d.canonical_ingredient IS NOT NULL)""",
        }
        selected = {}
        for stratum, predicate in predicates.items():
            rows = connection.execute(
                f"""
                SELECT case_id, primary_id, case_version, quarter FROM cases c
                WHERE {predicate} ORDER BY CAST(case_id AS BIGINT) LIMIT ?
            """,
                [per_stratum],
            ).fetchall()
            for case_id, primary_id, version, quarter in rows:
                selected[case_id] = {
                    "primary_id": primary_id,
                    "case_version": version,
                    "quarter": quarter,
                    "stratum": stratum,
                }
        if not selected:
            raise ValueError("No cases available for source spot-check")
        mapping = {
            name: (ingredient, kind)
            for name, ingredient, kind in connection.execute(
                "SELECT raw_name, canonical_ingredient, alias_type FROM drug_mapping"
            ).fetchall()
        }
        roles = {
            r[0] for r in connection.execute("SELECT role_code FROM analysis_roles").fetchall()
        }
        vocabulary = {
            r[0] for r in connection.execute("SELECT reaction FROM candidate_reactions").fetchall()
        }
        original_demo = []
        original_drugs, original_reactions = defaultdict(list), defaultdict(set)
        source_hashes = {}
        drug_headers = {}
        for source in sources:
            quarter = source["quarter"]
            for table in ("DEMO", "DRUG", "REAC"):
                path = source["paths"][table]
                source_hashes[f"{quarter}_{table}"] = sha256(path)
                with path.open(encoding=encoding, newline="") as stream:
                    reader = csv.DictReader(stream, delimiter="$", quoting=csv.QUOTE_NONE)
                    if table == "DRUG":
                        drug_headers[quarter] = reader.fieldnames
                    for row in reader:
                        case_id = row["caseid"].strip()
                        if case_id not in selected:
                            continue
                        chosen = selected[case_id]
                        if table == "DEMO":
                            original_demo.append({**row, "quarter": quarter})
                        elif (
                            row["primaryid"].strip() == chosen["primary_id"]
                            and quarter == chosen["quarter"]
                        ):
                            if table == "DRUG":
                                original_drugs[case_id].append(row)
                            elif row["pt"].strip():
                                original_reactions[case_id].add(normalized_name(row["pt"]))
        latest = {row["caseid"].strip(): row for row in latest_cases(original_demo)}
        details = []
        for case_id, case in sorted(selected.items(), key=lambda pair: int(pair[0])):
            source_drugs = original_drugs[case_id]
            headers = drug_headers[case["quarter"]]
            columns = ",".join('"' + name.replace('"', '""') + '"' for name in headers)
            loaded = connection.execute(
                f"SELECT {columns} FROM case_drugs WHERE case_id=?", [case_id]
            ).fetchall()
            expected_rows = Counter(tuple(row[key] for key in headers) for row in source_drugs)
            loaded_rows = Counter(
                tuple(value if value is not None else "" for value in row) for row in loaded
            )
            expected_exposure = set()
            for row in source_drugs:
                direct = mapping.get(normalized_name(row["drugname"]))
                active = {
                    mapping[token][0]
                    for token in (normalized_name(part) for part in row["prod_ai"].split("\\"))
                    if token in mapping and mapping[token][1] == "ingredient"
                }
                conflict = len(active) > 1 or (direct and active and direct[0] not in active)
                canonical = (
                    next(iter(active)) if len(active) == 1 else direct[0] if direct else None
                )
                if not conflict and canonical and normalized_name(row["role_cod"]) in roles:
                    expected_exposure.add(canonical)
            actual_exposure = {
                r[0]
                for r in connection.execute(
                    "SELECT drug FROM case_drug_presence WHERE case_id=?", [case_id]
                ).fetchall()
            }
            actual_reactions = {
                r[0]
                for r in connection.execute(
                    "SELECT reaction FROM case_reactions WHERE case_id=?", [case_id]
                ).fetchall()
            }
            actual_items = {
                tuple(row)
                for row in connection.execute(
                    "SELECT item_type, item_value FROM case_items WHERE case_id=?", [case_id]
                ).fetchall()
            }
            expected_items = {("DRUG", drug) for drug in expected_exposure} | {
                ("REAC", term) for term in original_reactions[case_id] & vocabulary
            }
            demo = latest[case_id]
            checks = {
                "latest_report": demo["primaryid"].strip() == case["primary_id"]
                and int(demo["caseversion"]) == case["case_version"]
                and demo["quarter"] == case["quarter"],
                "complete_drug_records": expected_rows == loaded_rows,
                "reactions": original_reactions[case_id] == actual_reactions,
                "role_filtered_exposures": expected_exposure == actual_exposure,
                "mining_items": actual_items == expected_items,
            }
            details.append(
                {
                    "case_id": case_id,
                    **case,
                    "source_drug_rows": len(source_drugs),
                    "source_reactions": len(original_reactions[case_id]),
                    "checks": checks,
                }
            )
    result = {
        "status": "passed" if all(all(row["checks"].values()) for row in details) else "failed",
        "checked_cases": len(details),
        "checks_per_case": 5,
        "strata": dict(Counter(case["stratum"] for case in selected.values())),
        "source_hashes": source_hashes,
        "student_manual_review": "pending",
        "scientific_findings_validated": False,
    }
    write_json(output / "source_spotcheck.json", result)
    write_json(output / "source_spotcheck_cases.json", details)
    if result["status"] != "passed":
        raise ValueError("Source spot-check failed; inspect case diagnostics")
    return result
