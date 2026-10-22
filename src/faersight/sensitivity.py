"""Isolated 2025 Q4 role sensitivity; frozen primary artifacts stay read-only."""

import json
import re
import shutil
from pathlib import Path

import duckdb
import yaml

from faersight.arff import export_mart_arff
from faersight.audit import sha256, write_json
from faersight.benchmark_ranking import benchmark_ranks
from faersight.disproportionality import Counts
from faersight.evaluation import benchmark_rows, ranking_comparison, spearman, verify_weka
from faersight.integration import validate_connection, validate_mart
from faersight.mining import load_mining_config, read_csv, run_apriori
from faersight.screening import screening_metrics
from faersight.weka import write_csv


def load_sensitivity_config(path: Path) -> tuple[dict, dict, dict, dict, dict]:
    root = path.resolve().parent.parent
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    expected = {
        "schema_version": 1,
        "scope": "2025Q4_statins_only",
        "roles": ["PS", "SS"],
        "vocabulary": "fixed_primary_reactions",
        "screening": {
            "prr_min_reports": 3,
            "prr_min": 2,
            "chi_square_min": 4,
            "chi_square": "yates_corrected",
            "ror_ci": "log_wald_95_no_zero_cell_correction",
        },
        "ranking": {
            "ties": "average_descending",
            "percentile": "100 * (pool_size - rank) / (pool_size - 1); singleton=100",
            "population": "shared_finite_lift_prr_ror",
        },
    }
    if not isinstance(config, dict) or any(config.get(k) != v for k, v in expected.items()):
        raise ValueError("Unsupported sensitivity contract")
    paths = [path.resolve()]
    for key in ("primary_mining_config", "mapping_overlay", "mapping_review"):
        selected = (root / config[key]).resolve()
        if not selected.is_relative_to(root) or not selected.is_file():
            raise ValueError("Sensitivity inputs must exist inside the repository")
        paths.append(selected)
    mining, experiment, benchmark, hashes = load_mining_config(paths[1])
    if (
        experiment["quarters"] != ["2025Q4"]
        or experiment["drug_roles"] != ["PS"]
        or experiment["therapeutic_class"] != "statins"
    ):
        raise ValueError("Sensitivity requires frozen 2025 Q4 statins PS primary")
    hashes.update({p: sha256(p) for p in paths})
    return config, mining, experiment, benchmark, hashes


def read_signals(database: Path) -> list[dict]:
    with duckdb.connect(str(database), read_only=True) as c:
        return [
            {"drug": drug, "reaction": reaction, **screening_metrics(Counts(a, b, x, d))}
            for drug, reaction, a, b, x, d in c.execute(
                "SELECT drug,reaction,a,b,c,d FROM signal_counts ORDER BY drug,reaction"
            ).fetchall()
        ]


def rebuild_presence(c: duckdb.DuckDBPyConnection) -> None:
    """Reuse primary counting SQL and retain the primary reaction vocabulary."""
    sql = (Path(__file__).parent / "sql/analytical_mart.sql").read_text()
    names = {"case_drug_presence", "drug_presence", "case_items", "signal_counts"}
    for table in ("case_items", "signal_counts", "case_drug_presence"):
        c.execute(f"DROP TABLE {table}")
    for statement in c.extract_statements(sql):
        match = re.search(r"CREATE (?:TABLE|UNIQUE INDEX) (\w+)", statement.query)
        if match and match[1] in names:
            c.execute(statement)


def build_sensitivity_mart(
    primary: Path, output: Path, overlay: Path, review_path: Path
) -> tuple[Path, dict]:
    quality = validate_mart(primary)
    if quality["status"] != "passed":
        raise ValueError("Primary mart failed validation")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Sensitivity mart exists; choose a new directory")
    aliases = read_csv(overlay)
    review = yaml.safe_load(review_path.read_text(encoding="utf-8"))
    if (
        len(aliases) != 1
        or aliases[0]["raw_name"] != "ROSUVASTATIN ZINC"
        or aliases[0]["canonical_ingredient"] != "rosuvastatin"
        or aliases[0]["reviewed"] != "true"
        or aliases[0]["alias_type"] != "ingredient"
        or review.get("primary_mapping_changed") is not False
        or review.get("scope") != "sensitivity_only_SS_ingredient_token"
    ):
        raise ValueError("Unexpected sensitivity-only mapping review")
    decisions = review["decisions"]
    expected = {
        (r["normalized_name"], r["normalized_prod_ai"], r["role_code"]): r for r in decisions
    }
    output.mkdir(parents=True, exist_ok=True)
    database = output / "analytical.building.duckdb"
    shutil.copyfile(primary, database)
    with duckdb.connect(str(database)) as c:
        c.execute("SET memory_limit='4GB'")
        c.execute("SET threads=4")
        observed = c.execute("""
            SELECT normalized_name,normalized_prod_ai,role_code,count(*)
            FROM case_drugs WHERE is_unmapped_target_candidate AND role_code IN ('PS','SS')
            GROUP BY ALL ORDER BY ALL
        """).fetchall()
        if set(expected) != {(name, ai, role) for name, ai, role, _ in observed}:
            raise ValueError("Unreviewed PS/SS candidate or stale mapping review")
        for name, ai, role, count in observed:
            decision = expected[name, ai, role]
            if (
                role != "SS"
                or decision["expected_source_rows"] != count
                or decision["decision"] != "map_exact_ingredient_token"
                or decision["token"] not in ai.split("\\")
                or decision["token"] != aliases[0]["raw_name"]
                or decision["canonical_ingredient"] != aliases[0]["canonical_ingredient"]
                or not decision.get("sources")
            ):
                raise ValueError("Invalid mapping decision or candidate row count")
        c.execute("INSERT INTO analysis_roles VALUES ('SS')")
        c.execute("""
            UPDATE case_drugs SET is_target_exposure =
                canonical_ingredient IS NOT NULL AND NOT mapping_conflict
                AND role_code IN ('PS','SS')
        """)
        rebuild_presence(c)
        # Isolate the mapping contribution from the effect of simply adding SS.
        uncorrected_exposed = c.execute(
            "SELECT count(DISTINCT case_id) FROM case_drug_presence"
        ).fetchone()[0]
        uncorrected_counts = c.execute(
            "SELECT drug,reaction,a,b,c,d FROM signal_counts ORDER BY drug,reaction"
        ).fetchall()
        c.execute("CREATE TABLE sensitivity_mapping_audit AS SELECT * FROM case_drugs WHERE false")
        for name, ai, role, _ in observed:
            params = [name, ai, role]
            predicate = "normalized_name=? AND normalized_prod_ai=? AND role_code=?"
            c.execute(
                f"INSERT INTO sensitivity_mapping_audit SELECT * FROM case_drugs WHERE {predicate}",
                params,
            )
            c.execute(
                f"""UPDATE case_drugs SET canonical_ingredient='rosuvastatin',
                ai_ingredient='rosuvastatin', matched_ai_count=1, target_class='statins',
                mapping_method='prod_ai_sensitivity_review', is_target_exposure=true,
                is_unmapped_target_candidate=false WHERE {predicate}""",
                params,
            )
        # Keep the generic primary mapping table intact; overlay application is SS-only.
        rebuild_presence(c)
        c.execute("""
            UPDATE candidate_reactions v SET target_case_count=(
                SELECT count(*) FROM case_reactions r WHERE r.reaction=v.reaction AND
                EXISTS (SELECT 1 FROM case_drug_presence d WHERE d.case_id=r.case_id))
        """)
        checks = validate_connection(c)
        checks["checks"]["all_ps_ss_candidates_resolved"] = (
            c.execute("""
            SELECT count(*) FROM case_drugs WHERE is_unmapped_target_candidate
            AND role_code IN ('PS','SS')
        """).fetchone()[0]
            == 0
        )
        checks["checks"]["only_2025q4"] = c.execute(
            "SELECT list(DISTINCT quarter) FROM cases"
        ).fetchone()[0] == ["2025Q4"]
        # Compare to the immutable source through an attached read-only database.
        quoted_primary = primary.resolve().as_posix().replace("'", "''")
        c.execute(f"ATTACH '{quoted_primary}' AS primary_db (READ_ONLY)")
        for table in ("cases", "case_reactions", "raw_drug", "raw_demo", "raw_reac"):
            checks["checks"][f"unchanged_{table}"] = c.execute(f"""
                SELECT NOT EXISTS(SELECT * FROM {table} EXCEPT ALL SELECT * FROM primary_db.{table})
                AND NOT EXISTS(SELECT * FROM primary_db.{table} EXCEPT ALL SELECT * FROM {table})
            """).fetchone()[0]
        checks["checks"]["fixed_primary_vocabulary"] = c.execute("""
            SELECT NOT EXISTS(SELECT reaction FROM candidate_reactions
                EXCEPT SELECT reaction FROM primary_db.candidate_reactions)
            AND NOT EXISTS(SELECT reaction FROM primary_db.candidate_reactions
                EXCEPT SELECT reaction FROM candidate_reactions)
        """).fetchone()[0]
        checks["checks"]["ps_presence_subset"] = c.execute("""
            SELECT NOT EXISTS(SELECT * FROM primary_db.case_drug_presence
                EXCEPT SELECT * FROM case_drug_presence)
        """).fetchone()[0]
        deferred = c.execute("""
            SELECT r.reaction,count(*) AS target_case_count FROM case_reactions r
            WHERE EXISTS(SELECT 1 FROM case_drug_presence d WHERE d.case_id=r.case_id)
            AND NOT EXISTS(SELECT 1 FROM candidate_reactions v WHERE v.reaction=r.reaction)
            GROUP BY r.reaction HAVING count(*) >=
                (SELECT reaction_min_target_cases FROM analysis_settings)
            ORDER BY r.reaction
        """).fetchall()
        exposure = c.execute("""
            SELECT g.drug,
              (SELECT count(*) FROM primary_db.case_drug_presence d WHERE d.drug=g.drug),
              (SELECT count(*) FROM case_drug_presence d WHERE d.drug=g.drug)
            FROM class_ingredients g ORDER BY drug
        """).fetchall()
        c.execute("DETACH primary_db")
        c.execute("CHECKPOINT")
    if not all(checks["checks"].values()):
        write_json(output / "quality_gates.json", checks)
        raise ValueError("Sensitivity mart invariant failed")
    database = database.replace(output / "analytical.duckdb")
    write_csv(
        output / "ps_ss_without_overlay_counts.csv",
        [
            {"drug": drug, "reaction": reaction, "a": a, "b": b, "c": x, "d": d}
            for drug, reaction, a, b, x, d in uncorrected_counts
        ],
    )
    write_csv(
        output / "deferred_reactions.csv",
        [{"reaction": r, "target_case_count": n} for r, n in deferred],
        fieldnames=["reaction", "target_case_count"],
    )
    record = {
        **checks,
        "status": "passed",
        "drug_roles": ["PS", "SS"],
        "source_mart_sha256": sha256(primary),
        "mapping_overlay_sha256": sha256(overlay),
        "mapping_review_sha256": sha256(review_path),
        "mapping_source_rows_resolved": sum(r[3] for r in observed),
        "unreviewed_ps_ss_candidates": 0,
        "without_overlay_exposed_n": uncorrected_exposed,
        "deferred_new_reactions": len(deferred),
        "vocabulary_policy": "fixed_primary_reactions_no_new_search",
        "exposure_by_drug": [
            {"drug": drug, "ps": ps, "ps_ss": both, "added": both - ps}
            for drug, ps, both in exposure
        ],
        "scientific_findings_validated": False,
        "artifacts": {database.name: sha256(database)},
    }
    write_json(output / "quality_gates.json", record)
    write_json(output / "integration_manifest.json", record)
    return database, record


def compare_roles(left: list[dict], right: list[dict], runs: dict, top_k: list[int]) -> dict:
    from faersight.evaluation import average_ranks

    lookup = {
        role: {(r["drug"], r["reaction"]): r for r in rows}
        for role, rows in [("PS", left), ("PS+SS", right)]
    }
    if set(lookup["PS"]) != set(lookup["PS+SS"]):
        raise ValueError("Role comparison changed the candidate pair universe")
    per_support = []
    for support in sorted(runs["PS"]):
        ps, ss = (set(runs[role][support]["pairs"]) for role in ("PS", "PS+SS"))
        per_support.append(
            {
                "support": support,
                "ps_rules": len(ps),
                "ps_ss_rules": len(ss),
                "common": len(ps & ss),
                "gained": len(ss - ps),
                "lost": len(ps - ss),
                "jaccard": len(ps & ss) / len(ps | ss) if ps | ss else None,
            }
        )
    rank_changes = []
    for score in ("lift_python_check", "prr", "ror"):
        import math

        keys = sorted(
            k for k in lookup["PS"] if all(math.isfinite(lookup[role][k][score]) for role in lookup)
        )
        values = {role: [lookup[role][k][score] for k in keys] for role in lookup}
        ranks = {role: average_ranks([-v for v in vs]) for role, vs in values.items()}
        overlaps = []
        for k in top_k:
            tops = {
                role: set(sorted(keys, key=lambda x: (-lookup[role][x][score], x))[:k])
                for role in lookup
            }
            effective = min(k, len(keys))
            overlaps.append(
                {
                    "requested_k": k,
                    "effective_k": effective,
                    "common": len(tops["PS"] & tops["PS+SS"]),
                    "tie_break": "drug_then_reaction_lexical",
                }
            )
        rank_changes.append(
            {
                "metric": score,
                "shared_finite_pairs": len(keys),
                "spearman": spearman(values["PS"], values["PS+SS"]),
                "top_k": overlaps,
                "largest_rank_changes": [
                    {
                        "drug": keys[i][0],
                        "reaction": keys[i][1],
                        "ps_rank": ranks["PS"][i],
                        "ps_ss_rank": ranks["PS+SS"][i],
                    }
                    for i in sorted(
                        range(len(keys)),
                        key=lambda i: (-abs(ranks["PS"][i] - ranks["PS+SS"][i]), keys[i]),
                    )[:10]
                ],
            }
        )
    screening = {
        role: {k for k, r in rows.items() if r["prr_screen_convention"]}
        for role, rows in lookup.items()
    }
    return {
        "support_comparison": per_support,
        "role_rank_comparison": rank_changes,
        "prr_screen": {
            "ps": len(screening["PS"]),
            "ps_ss": len(screening["PS+SS"]),
            "gained": len(screening["PS+SS"] - screening["PS"]),
            "lost": len(screening["PS"] - screening["PS+SS"]),
        },
    }


def run_sensitivity(
    primary: Path,
    primary_run: Path,
    output: Path,
    *,
    config_path: Path,
    jar: Path,
    java: str | None = None,
) -> dict:
    config, mining, experiment, benchmark, hashes = load_sensitivity_config(config_path)
    root = config_path.resolve().parent.parent
    if output.exists() and any(output.iterdir()):
        raise ValueError("Sensitivity experiment exists; choose a new output directory")
    source_hash = sha256(primary)
    baseline_manifest = json.loads((primary_run / "experiment_manifest.json").read_text())
    if baseline_manifest["source_mart_sha256"] != source_hash:
        raise ValueError("Primary experiment uses a different mart")
    # Verify the frozen baseline artifacts before using any result.
    for name, digest in baseline_manifest["artifacts"].items():
        selected = (primary_run / name).resolve()
        if not selected.is_relative_to(primary_run.resolve()) or sha256(selected) != digest:
            raise ValueError(f"Primary experiment artifact changed: {name}")
    for name, digest in baseline_manifest["input_hashes"].items():
        if sha256(root / name) != digest:
            raise ValueError(f"Frozen primary input changed: {name}")
    source_paths = [
        p for p in (root / "src/faersight").rglob("*") if p.suffix in {".py", ".sql", ".java"}
    ]
    code_hashes = {p: sha256(p) for p in source_paths}
    output.mkdir(parents=True, exist_ok=True)
    try:
        derived, mart = build_sensitivity_mart(
            primary,
            output / "mart",
            root / config["mapping_overlay"],
            root / config["mapping_review"],
        )
        exported = export_mart_arff(derived, output / "ps_ss/input")
        weka = experiment["weka"]
        run_apriori(
            output / "ps_ss/input/transactions.arff",
            output / "ps_ss/weka",
            jar=jar,
            supports=weka["support_grid"],
            min_lift=weka["min_metric"],
            max_rules=weka["max_rules"],
            expected_n=exported["eligible_n"],
            java=java,
            heap=mining["heap"],
            active_processors=mining["active_processors"],
            timeout=mining["timeout_seconds"],
        )
        signals, runs, recoveries, rankings, comparisons = {}, {}, [], [], []
        for role, database, run in [
            ("PS", primary, primary_run),
            ("PS+SS", derived, output / "ps_ss"),
        ]:
            signals[role] = read_signals(database)
            runs[role] = verify_weka(
                read_csv(run / "weka/weka_rules.csv"),
                read_csv(run / "weka/weka_runs.csv"),
                signals[role],
                supports=weka["support_grid"],
                min_lift=weka["min_metric"],
                n=exported["eligible_n"],
            )
            with duckdb.connect(str(database), read_only=True) as c:
                recoveries.extend(
                    {"role": role, **row}
                    for row in benchmark_rows(
                        benchmark,
                        signals[role],
                        runs[role],
                        c,
                        exported["eligible_n"],
                        weka["min_metric"],
                    )
                )
            rankings.extend(benchmark_ranks(signals[role], benchmark, runs[role], role))
            for support, accepted in runs[role].items():
                for score in ("prr", "ror"):
                    comparisons.append(
                        {
                            "role": role,
                            "support": support,
                            **ranking_comparison(
                                list(accepted["pairs"].values()), score, mining["top_k"]
                            ),
                        }
                    )
        write_csv(
            output / "all_counts_screened.csv",
            [{"role": role, **row} for role, rows in signals.items() for row in rows],
        )
        write_csv(output / "benchmark_ranks.csv", rankings)
        write_csv(output / "benchmark_recovery.csv", recoveries)
        write_json(output / "method_rank_comparison.json", comparisons)
        differences = compare_roles(signals["PS"], signals["PS+SS"], runs, mining["top_k"])
        write_json(output / "role_comparison.json", differences)
        from faersight.manual_review import make_review_package

        review = make_review_package(
            primary, derived, output / "manual_review", signals, runs, benchmark
        )
        if sha256(primary) != source_hash or any(sha256(p) != h for p, h in hashes.items()):
            raise ValueError("Primary mart or frozen inputs changed during sensitivity")
        if any(sha256(p) != h for p, h in code_hashes.items()):
            raise ValueError("Source code changed during sensitivity run")
        result = {
            "status": "computational_gates_passed",
            "quarters": ["2025Q4"],
            "primary_experiment_unchanged": True,
            "scientific_findings_validated": False,
            "source_mart_sha256": source_hash,
            "primary_run_manifest_sha256": sha256(primary_run / "experiment_manifest.json"),
            "input_hashes": {p.relative_to(root).as_posix(): h for p, h in hashes.items()},
            "source_code_hashes": {
                p.relative_to(root).as_posix(): h for p, h in code_hashes.items()
            },
            "mart": mart,
            "comparison": differences,
            "manual_review": review,
            "benchmark_recovery": [
                {
                    "role": role,
                    "support": support,
                    "recovered": sum(
                        r["status"] == "recovered"
                        for r in recoveries
                        if r["role"] == role and r["support_requested"] == support
                    ),
                    "total": len(benchmark["pairs"]),
                }
                for role in runs
                for support in sorted(runs[role])
            ],
            "pending_student_judgment": [
                "source_case_review",
                "exact_alias_signoff",
                "benchmark_label_review",
                "rule_interpretation",
                "course_submission",
            ],
            "artifacts": {
                p.relative_to(output).as_posix(): sha256(p)
                for p in sorted(output.rglob("*"))
                if p.is_file()
            },
        }
        write_json(output / "sensitivity_manifest.json", result)
        return result
    except Exception as exc:
        write_json(
            output / "sensitivity_failure.json",
            {"status": "failed", "error": str(exc), "scientific_findings_validated": False},
        )
        raise
