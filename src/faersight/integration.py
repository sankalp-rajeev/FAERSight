"""Streaming source preparation and a complete, bounded-resource DuckDB mart."""

import csv
import json
import platform
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from faersight.acquire import archive_inventory, download_archive, extract_required
from faersight.audit import sha256, write_json
from faersight.config import load_ingestion_config
from faersight.normalize import load_mapping, normalized_name
from faersight.parse import stage_relation


def prepare_sources(config_path: Path, raw_dir: Path, *, download: bool = False) -> list[dict]:
    config, _, _ = load_ingestion_config(config_path)
    sources = []
    for source in config["sources"]:
        quarter = source["quarter"]
        archive = raw_dir / quarter / source["archive_name"]
        if not download and not archive.is_file():
            raise ValueError(f"Run acquire first; missing frozen archive: {archive}")
        manifest = download_archive(
            source["url"],
            quarter,
            archive,
            expected_sha256=source["sha256"],
            source_page=source["source_page"],
        )
        if archive.stat().st_size != source["bytes"]:
            raise ValueError("Source archive byte size differs from the frozen scope")
        paths = extract_required(archive, quarter, archive.parent / "extracted")
        if "DELETE" not in paths:
            raise ValueError("Frozen modern-quarter ingestion requires a deleted-case list")
        sources.append(
            {
                "quarter": quarter,
                "paths": paths,
                "download": manifest,
                "archive_path": archive.as_posix(),
                "inventory": archive_inventory(archive, quarter),
                "extraction": json.loads(
                    (archive.parent / "extracted" / "extraction_manifest.json").read_text()
                ),
            }
        )
    return sources


def _count(connection: duckdb.DuckDBPyConnection, query: str) -> int:
    return int(connection.execute(query).fetchone()[0])


def _csv_query(connection: duckdb.DuckDBPyConnection, path: Path, query: str) -> None:
    """Stream query output directly to disk; do not fetch all raw records into Python."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection.execute(f"COPY ({query}) TO ? (FORMAT CSV, HEADER true)", [str(path)])


def _load_staged(
    connection: duckdb.DuckDBPyConnection, table: str, audit: dict, *, first: bool
) -> None:
    columns = {
        "_source_row": "BIGINT",
        "_quarter": "VARCHAR",
        **{column: "VARCHAR" for column in audit["header"]},
    }
    # Table names are internal enum values, never taken from source data or SQL input.
    if table not in {"DEMO", "DRUG", "REAC"}:
        raise ValueError("Invalid raw table")
    statement = (
        f"CREATE TABLE raw_{table.lower()} AS "
        if first
        else f"INSERT INTO raw_{table.lower()} BY NAME "
    )
    connection.execute(
        statement + "SELECT * FROM read_csv(?, columns=?, header=true, "
        "auto_detect=false, delim=',', quote='\"', escape='\"', "
        "strict_mode=true, ignore_errors=false, parallel=false)",
        [audit["staged_path"], columns],
    )


def _load_deleted(connection: duckdb.DuckDBPyConnection, sources: list[dict]) -> dict:
    deleted = set()
    audits = []
    for source in sources:
        path = source["paths"].get("DELETE")
        rows = blanks = 0
        if path is None:
            raise ValueError("Deleted-case source is required")
        with path.open(encoding="ascii") as stream:
            for line_number, line in enumerate(stream, 1):
                case_id = line.strip()
                if not case_id:
                    blanks += 1
                    continue
                if not case_id.isascii() or not case_id.isdigit():
                    raise ValueError(f"{path}:{line_number}: invalid deleted case ID")
                deleted.add(case_id)
                rows += 1
        audits.append(
            {
                "quarter": source["quarter"],
                "path": path.as_posix(),
                "sha256": sha256(path),
                "rows": rows,
                "blank_lines": blanks,
            }
        )
    connection.execute("CREATE TABLE deleted_cases(case_id VARCHAR PRIMARY KEY)")
    if deleted:
        connection.executemany(
            "INSERT INTO deleted_cases VALUES (?)", [(x,) for x in sorted(deleted)]
        )
    return {"sources": audits, "unique_deleted_case_ids": len(deleted)}


def _load_mapping(
    connection: duckdb.DuckDBPyConnection, mapping_path: Path, ingredients: list[str]
) -> None:
    reviewed = load_mapping(mapping_path)
    if set(reviewed.values()) != set(ingredients):
        raise ValueError("Mapping does not cover exactly the selected class")
    rows = []
    with mapping_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            kind = row.get("alias_type")
            if kind not in {"ingredient", "brand"}:
                raise ValueError("Each real drug alias needs alias_type ingredient or brand")
            rows.append(
                (
                    normalized_name(row["raw_name"]),
                    row["canonical_ingredient"].strip(),
                    row["mapping_basis"],
                    kind,
                )
            )
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("Duplicate normalized aliases in frozen mapping")
    connection.execute(
        "CREATE TABLE drug_mapping(raw_name VARCHAR PRIMARY KEY, "
        "canonical_ingredient VARCHAR, mapping_basis VARCHAR, alias_type VARCHAR)"
    )
    connection.executemany("INSERT INTO drug_mapping VALUES (?, ?, ?, ?)", rows)
    connection.execute("CREATE TABLE class_ingredients(drug VARCHAR PRIMARY KEY)")
    connection.executemany("INSERT INTO class_ingredients VALUES (?)", [(x,) for x in ingredients])


def _validate_source_identities(connection: duckdb.DuckDBPyConnection) -> dict:
    errors = {
        "invalid_demo_identity": _count(
            connection,
            """
            SELECT count(*) FROM raw_demo WHERE
            NOT regexp_full_match(trim(primaryid), '[0-9]+') OR
            NOT regexp_full_match(trim(caseid), '[0-9]+') OR
            NOT regexp_full_match(trim(caseversion), '[0-9]+') OR
            try_cast(primaryid AS BIGINT) IS NULL OR try_cast(caseid AS BIGINT) IS NULL OR
            try_cast(caseversion AS BIGINT) IS NULL OR try_cast(caseversion AS BIGINT) < 1
        """,
        ),
        "conflicting_report_identities": _count(
            connection,
            """
            SELECT count(*) FROM (
                SELECT trim(primaryid) FROM raw_demo GROUP BY trim(primaryid)
                HAVING count(DISTINCT (trim(caseid), trim(caseversion))) > 1
            )
        """,
        ),
    }
    for table in ("drug", "reac"):
        errors[f"invalid_{table}_identity"] = _count(
            connection,
            f"""
            SELECT count(*) FROM raw_{table} WHERE
            NOT regexp_full_match(trim(primaryid), '[0-9]+') OR
            NOT regexp_full_match(trim(caseid), '[0-9]+') OR
            try_cast(primaryid AS BIGINT) IS NULL OR try_cast(caseid AS BIGINT) IS NULL
        """,
        )
        errors[f"{table}_case_id_join_mismatches"] = _count(
            connection,
            f"""
            SELECT count(*) FROM raw_{table} r
            WHERE EXISTS (SELECT 1 FROM raw_demo d WHERE d._quarter = r._quarter
                          AND trim(d.primaryid) = trim(r.primaryid))
              AND NOT EXISTS (SELECT 1 FROM raw_demo d WHERE d._quarter = r._quarter
                              AND trim(d.primaryid) = trim(r.primaryid)
                              AND trim(d.caseid) = trim(r.caseid))
        """,
        )
    if any(errors.values()):
        raise ValueError("Source identity quality gate failed: " + json.dumps(errors))
    return errors


def validate_connection(connection: duckdb.DuckDBPyConnection) -> dict:
    """Independently query the mart's invariants; usable again after ingestion."""
    n = _count(connection, "SELECT count(*) FROM cases")
    exposed = _count(connection, "SELECT count(DISTINCT case_id) FROM case_drug_presence")
    checks = {
        "nonempty_reporting_population": n > 0,
        "target_exposure_present": exposed > 0,
        "nonempty_candidate_vocabulary": _count(
            connection, "SELECT count(*) FROM candidate_reactions"
        )
        > 0,
        "unique_cases": _count(connection, "SELECT count(DISTINCT case_id) FROM cases") == n,
        "complete_eligible_population": _count(
            connection,
            """
            SELECT count(*) FROM case_eligibility
            WHERE NOT is_deleted AND has_drug AND has_reaction
        """,
        )
        == n,
        "no_deleted_cases": _count(
            connection,
            """
            SELECT count(*) FROM cases c JOIN deleted_cases d USING (case_id)
        """,
        )
        == 0,
        "no_mapping_conflicts": _count(
            connection,
            """
            SELECT count(*) FROM case_drugs WHERE mapping_conflict
        """,
        )
        == 0,
        "all_eligible_drug_records_preserved": _count(
            connection,
            """
            SELECT count(*) FROM raw_drug r JOIN cases c ON trim(r.primaryid) = c.primary_id
            AND trim(r.caseid) = c.case_id AND r._quarter = c.quarter
        """,
        )
        == _count(connection, "SELECT count(*) FROM case_drugs"),
        "valid_drug_joins": _count(
            connection,
            """
            SELECT count(*) FROM case_drugs d LEFT JOIN cases c ON d.case_id = c.case_id
            AND d.primary_id = c.primary_id AND d.quarter = c.quarter WHERE c.case_id IS NULL
        """,
        )
        == 0,
        "valid_reaction_joins": _count(
            connection,
            """
            SELECT count(*) FROM case_reactions r LEFT JOIN cases c ON r.case_id = c.case_id
            AND r.primary_id = c.primary_id AND r.quarter = c.quarter WHERE c.case_id IS NULL
        """,
        )
        == 0,
        "valid_item_joins": _count(
            connection,
            """
            SELECT count(*) FROM case_items i ANTI JOIN cases c USING(case_id)
        """,
        )
        == 0,
        "unique_presence_items": _count(connection, "SELECT count(*) FROM case_items")
        == _count(connection, "SELECT count(*) FROM (SELECT DISTINCT * FROM case_items)"),
        "role_filter_integrity": _count(
            connection,
            """
            SELECT count(*) FROM case_drugs WHERE is_target_exposure
            AND role_code NOT IN (SELECT role_code FROM analysis_roles)
        """,
        )
        == 0,
        "common_denominator_and_nonnegative_cells": _count(
            connection,
            """
            SELECT count(*) FROM signal_counts WHERE a < 0 OR b < 0 OR c < 0 OR d < 0
            OR a+b+c+d <> n OR n <> (SELECT count(*) FROM cases)
        """,
        )
        == 0,
        "contingency_marginals": _count(
            connection,
            """
            SELECT count(*) FROM signal_counts s WHERE
            a+b <> (SELECT count(*) FROM case_drug_presence d WHERE d.drug=s.drug) OR
            a+c <> (SELECT count(*) FROM case_reactions r WHERE r.reaction=s.reaction) OR
            c+d <> (SELECT count(*) FROM cases) -
                   (SELECT count(*) FROM case_drug_presence d WHERE d.drug=s.drug)
        """,
        )
        == 0,
        "complete_candidate_pair_grid": _count(connection, "SELECT count(*) FROM signal_counts")
        == _count(connection, "SELECT count(*) FROM candidate_reactions")
        * _count(connection, "SELECT count(*) FROM class_ingredients"),
        "background_reports_preserved": n - exposed
        == _count(
            connection,
            """
            SELECT count(*) FROM cases c WHERE NOT EXISTS
            (SELECT 1 FROM case_drug_presence d WHERE d.case_id = c.case_id)
        """,
        ),
        "latest_versions_not_resurrected": _count(
            connection,
            """
            SELECT count(*) FROM cases c JOIN latest_cases l USING(case_id)
            WHERE c.primary_id <> l.primary_id OR c.case_version <> l.case_version
            OR c.quarter <> l.quarter
        """,
        )
        == 0,
    }
    for table in ("demo", "drug", "reac"):
        checks[f"{table}_source_row_reconciliation"] = (
            _count(
                connection,
                f"""
            SELECT count(*) FROM source_files s WHERE s.table_name = '{table.upper()}'
            AND s.source_rows <> (SELECT count(*) FROM raw_{table} r WHERE r._quarter = s.quarter)
        """,
            )
            == 0
        )
    unresolved = _count(
        connection, "SELECT count(*) FROM case_drugs WHERE is_unmapped_target_candidate"
    )
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "eligible_n": n,
        "target_exposed_n": exposed,
        "background_n": n - exposed,
        "candidate_reactions": _count(connection, "SELECT count(*) FROM candidate_reactions"),
        "counted_pairs": _count(connection, "SELECT count(*) FROM signal_counts"),
        "unmapped_target_candidate_drug_rows": unresolved,
        "warnings": (
            ["Target-relevant unmapped names require review; no fuzzy mapping applied"]
            if unresolved
            else []
        ),
        "scientific_findings_validated": False,
        "remaining_scientific_gates": [
            "real WEKA experiment",
            "manual source review",
            "benchmark freeze/recovery",
            "sensitivity/evaluation",
        ],
    }


def _audit_mart(
    connection: duckdb.DuckDBPyConnection,
    stage_audits: list[dict],
    identities: dict,
    deleted_audit: dict,
) -> dict:
    tables = (
        "raw_demo",
        "raw_drug",
        "raw_reac",
        "latest_cases",
        "cases",
        "case_drugs",
        "case_reactions",
        "case_drug_presence",
        "case_items",
        "candidate_reactions",
    )
    audit = {
        "table_counts": {
            table: _count(connection, f"SELECT count(*) FROM {table}") for table in tables
        },
        "sources": stage_audits,
        "identity_checks": identities,
        "deletions": deleted_audit,
    }
    audit["case_versions_removed"] = (
        audit["table_counts"]["raw_demo"] - audit["table_counts"]["latest_cases"]
    )
    audit["unique_case_ids_before_dedup"] = _count(
        connection, "SELECT count(DISTINCT trim(caseid)) FROM raw_demo"
    )
    audit["exclusions"] = {
        "deleted_latest_cases": _count(
            connection, "SELECT count(*) FROM case_eligibility WHERE is_deleted"
        ),
        "nondeleted_latest_missing_drug": _count(
            connection,
            "SELECT count(*) FROM case_eligibility WHERE NOT is_deleted AND NOT has_drug",
        ),
        "nondeleted_latest_missing_reaction": _count(
            connection,
            "SELECT count(*) "
            "FROM case_eligibility WHERE NOT is_deleted AND has_drug AND NOT has_reaction",
        ),
    }
    for table in ("drug", "reac"):
        audit[f"orphan_{table}_rows"] = _count(
            connection,
            f"""
            SELECT count(*) FROM raw_{table} r WHERE NOT EXISTS (
                SELECT 1 FROM raw_demo d WHERE trim(d.primaryid) = trim(r.primaryid)
                AND d._quarter = r._quarter)
        """,
        )
        audit[f"nonretained_{table}_rows"] = _count(
            connection,
            f"""
            SELECT count(*) FROM raw_{table} r WHERE NOT EXISTS (
                SELECT 1 FROM cases c WHERE c.primary_id = trim(r.primaryid)
                AND c.case_id = trim(r.caseid) AND c.quarter = r._quarter)
        """,
        )
    audit["cases_without_primary_suspect"] = _count(
        connection,
        """
        SELECT count(*) FROM cases c WHERE NOT EXISTS (
            SELECT 1 FROM case_drugs d WHERE d.case_id = c.case_id AND d.role_code = 'PS')
    """,
    )
    audit["duplicate_drug_sequence_groups_preserved"] = _count(
        connection,
        """
        SELECT count(*) FROM (SELECT case_id, drug_seq FROM case_drugs
                              GROUP BY case_id, drug_seq HAVING count(*) > 1)
    """,
    )
    audit["mapping_methods"] = dict(
        connection.execute(
            "SELECT mapping_method, count(*) FROM case_drugs GROUP BY mapping_method"
        ).fetchall()
    )
    audit["retained_drug_rows_by_role"] = dict(
        connection.execute(
            "SELECT role_code, count(*) FROM case_drugs GROUP BY role_code"
        ).fetchall()
    )
    audit["unmapped_target_candidate_drug_rows"] = _count(
        connection, "SELECT count(*) FROM case_drugs WHERE is_unmapped_target_candidate"
    )
    return audit


def build_full_mart(
    sources: list[dict],
    output: Path,
    *,
    mapping_path: Path,
    ingredients: list[str],
    therapeutic_class: str,
    roles: list[str],
    min_target_cases: int,
    encoding: str = "ascii",
    memory_limit: str = "4GB",
    threads: int = 4,
) -> dict:
    """Build atomically; failed builds keep diagnostic files and never replace a good mart."""
    if (
        not 1 <= len(sources) <= 2
        or len({s["quarter"] for s in sources}) != len(sources)
        or roles not in (["PS"], ["PS", "SS"])
        or min_target_cases < 1
    ):
        raise ValueError("Invalid quarter scope, roles or reaction floor")
    output.mkdir(parents=True, exist_ok=True)
    if (output / "analytical.duckdb").exists():
        raise ValueError(
            "Validated output already exists; select a new output directory for a rerun"
        )
    work = output / "staging"
    database = output / "analytical.building.duckdb"
    if database.exists():
        raise ValueError(f"Unfinished build exists; use a new output directory: {database}")
    stage_audits = []
    started = datetime.now(UTC).isoformat()
    try:
        with duckdb.connect(str(database)) as connection:
            connection.execute("SET memory_limit = ?", [memory_limit])
            connection.execute("SET threads = ?", [threads])
            connection.execute("SET temp_directory = ?", [str(output / "duckdb_tmp")])
            connection.execute(
                "CREATE TABLE source_files(table_name VARCHAR, quarter VARCHAR, "
                "source_path VARCHAR, source_sha256 VARCHAR, source_rows BIGINT, "
                "schema_json VARCHAR, PRIMARY KEY(table_name, quarter))"
            )
            for i, source in enumerate(sources):
                for table in ("DEMO", "DRUG", "REAC"):
                    print(f"Staging {source['quarter']} {table}...", flush=True)
                    audit = stage_relation(
                        source["paths"][table],
                        table,
                        source["quarter"],
                        work / f"{source['quarter']}_{table}.csv",
                        encoding=encoding,
                    )
                    stage_audits.append(audit)
                    _load_staged(connection, table, audit, first=i == 0)
                    connection.execute(
                        "INSERT INTO source_files VALUES (?, ?, ?, ?, ?, ?)",
                        [
                            table,
                            source["quarter"],
                            audit["source_path"],
                            audit["source_sha256"],
                            audit["source_rows"],
                            json.dumps(audit["header"]),
                        ],
                    )
            identities = _validate_source_identities(connection)
            deleted_audit = _load_deleted(connection, sources)
            _load_mapping(connection, mapping_path, ingredients)
            connection.execute("CREATE TABLE analysis_roles(role_code VARCHAR PRIMARY KEY)")
            connection.executemany("INSERT INTO analysis_roles VALUES (?)", [(r,) for r in roles])
            connection.execute(
                "CREATE TABLE analysis_settings(therapeutic_class VARCHAR, "
                "reaction_min_target_cases BIGINT, ingredient_separator VARCHAR, "
                "target_candidate_pattern VARCHAR)"
            )
            connection.execute(
                "INSERT INTO analysis_settings VALUES (?, ?, ?, ?)",
                [
                    therapeutic_class,
                    min_target_cases,
                    "\\",
                    "|".join(re.escape(name) for name in load_mapping(mapping_path)),
                ],
            )
            print(
                "Integrating latest cases, complete source records and presence items...",
                flush=True,
            )
            connection.execute((Path(__file__).parent / "sql/analytical_mart.sql").read_text())
            quality = validate_connection(connection)
            for table in ("DEMO", "DRUG", "REAC"):
                expected = sum(a["source_rows"] for a in stage_audits if a["table"] == table)
                quality["checks"][f"{table.lower()}_source_row_reconciliation"] = (
                    expected == _count(connection, f"SELECT count(*) FROM raw_{table.lower()}")
                )
            quality["status"] = "passed" if all(quality["checks"].values()) else "failed"
            audit = _audit_mart(connection, stage_audits, identities, deleted_audit)
            write_json(output / "preprocess_audit.json", audit)
            write_json(output / "quality_gates.json", quality)
            for view, order in (
                ("quarter_population", "quarter"),
                ("quarter_drug_role", "quarter, drug, role_code"),
                ("quarter_reaction", "quarter, reaction"),
            ):
                _csv_query(
                    connection, output / f"{view}.csv", f"SELECT * FROM {view} ORDER BY {order}"
                )
            _csv_query(
                connection,
                output / "unmapped_drugs.csv",
                """
                SELECT normalized_name, normalized_prod_ai, role_code, count(*) AS source_rows
                FROM case_drugs WHERE canonical_ingredient IS NULL
                GROUP BY ALL
                ORDER BY source_rows DESC, normalized_name, normalized_prod_ai, role_code
            """,
            )
            _csv_query(
                connection,
                output / "mapping_conflicts.csv",
                """
                SELECT case_id, primary_id, quarter, _source_row, drugname, prod_ai, role_code
                FROM case_drugs WHERE mapping_conflict ORDER BY quarter, _source_row
            """,
            )
            _csv_query(
                connection,
                output / "unmapped_target_candidates.csv",
                """
                SELECT normalized_name, normalized_prod_ai, role_code, count(*) AS source_rows
                FROM case_drugs WHERE is_unmapped_target_candidate
                GROUP BY ALL
                ORDER BY source_rows DESC, normalized_name, normalized_prod_ai, role_code
            """,
            )
            _csv_query(
                connection,
                output / "signal_counts.csv",
                "SELECT * FROM signal_counts ORDER BY drug, reaction",
            )
            connection.execute("CHECKPOINT")
        if quality["status"] != "passed":
            raise ValueError(
                f"Integration quality gates failed; inspect {output / 'quality_gates.json'}"
            )
        database.replace(output / "analytical.duckdb")
        write_json(
            output / "integration_manifest.json",
            {
                "status": "passed",
                "scientific_findings_validated": False,
                "started_utc": started,
                "finished_utc": datetime.now(UTC).isoformat(),
                "python_version": platform.python_version(),
                "duckdb_version": duckdb.__version__,
                "source_inputs": [
                    {key: value for key, value in s.items() if key != "paths"} for s in sources
                ],
                "mapping_sha256": sha256(mapping_path),
                "drug_roles": roles,
                "reaction_min_target_cases": min_target_cases,
                "artifacts": {
                    p.name: sha256(p)
                    for p in sorted(output.iterdir())
                    if p.is_file() and p.name != "integration_manifest.json"
                },
            },
        )
        return quality
    except Exception as exc:
        write_json(
            output / "integration_failure.json",
            {
                "status": "failed",
                "started_utc": started,
                "failed_utc": datetime.now(UTC).isoformat(),
                "error": str(exc),
                "scientific_findings_validated": False,
            },
        )
        raise


def ingest_experiment(config_path: Path, raw_dir: Path, output: Path) -> dict:
    config, therapeutic_class, mapping = load_ingestion_config(config_path)
    sources = prepare_sources(config_path, raw_dir)
    ingestion = config["ingestion"]
    quality = build_full_mart(
        sources,
        output,
        mapping_path=mapping,
        ingredients=therapeutic_class["ingredients"],
        therapeutic_class=therapeutic_class["name"],
        roles=config["drug_roles"],
        min_target_cases=config["reaction_min_target_cases"],
        encoding=ingestion["encoding"],
        memory_limit=ingestion["memory_limit"],
        threads=ingestion["threads"],
    )
    # Capture code/config provenance after all gates pass. Absence of Git is explicit.
    git = subprocess.run(
        ["git", "-c", f"safe.directory={Path.cwd().as_posix()}", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    manifest_path = output / "integration_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update(
        {
            "git_commit": git.stdout.strip() if git.returncode == 0 else None,
            "experiment_config_sha256": sha256(config_path),
            "class_config_sha256": sha256(
                config_path.resolve().parent.parent / config["therapeutic_class_file"]
            ),
            "source_code_hashes": {
                p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))
            },
            "mart_sql_sha256": sha256(Path(__file__).parent / "sql/analytical_mart.sql"),
        }
    )
    write_json(manifest_path, manifest)
    return quality


def validate_mart(path: Path) -> dict:
    with duckdb.connect(str(path), read_only=True) as connection:
        return validate_connection(connection)
