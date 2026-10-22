"""Small deterministic review packet; source details stay local and unsigned."""

import csv
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from faersight.audit import sha256, write_json
from faersight.deduplicate import latest_cases
from faersight.normalize import normalized_name
from faersight.weka import write_csv


def make_review_package(
    primary: Path, derived: Path, output: Path, signals: dict, runs: dict, benchmark: dict
) -> dict:
    output.mkdir(parents=True)
    selected = {}
    with duckdb.connect(str(derived), read_only=True) as c:
        # Categories overlap deliberately; keep all selection reasons per report.
        predicates = {
            "exact_SS_alias_correction": (
                "EXISTS(SELECT 1 FROM sensitivity_mapping_audit a WHERE a.case_id=c.case_id)",
                2,
            ),
            "PS_primary_exposure": (
                "EXISTS(SELECT 1 FROM case_drugs d WHERE d.case_id=c.case_id "
                "AND d.role_code='PS' AND d.is_target_exposure)",
                3,
            ),
            "SS_added_exposure_without_PS": (
                "EXISTS(SELECT 1 FROM case_drugs d WHERE d.case_id=c.case_id "
                "AND d.role_code='SS' AND d.is_target_exposure) AND NOT EXISTS"
                "(SELECT 1 FROM case_drugs d WHERE d.case_id=c.case_id "
                "AND d.role_code='PS' AND d.is_target_exposure)",
                4,
            ),
            "co_suspected_statins": (
                "(SELECT count(DISTINCT drug) FROM case_drug_presence d "
                "WHERE d.case_id=c.case_id)>1",
                2,
            ),
            "unexposed_empty_mining_basket": (
                "NOT EXISTS(SELECT 1 FROM case_items i WHERE i.case_id=c.case_id)",
                2,
            ),
            "C_only_statin_remains_background": (
                "NOT EXISTS(SELECT 1 FROM case_drug_presence d WHERE d.case_id=c.case_id) "
                "AND EXISTS(SELECT 1 FROM case_drugs d WHERE d.case_id=c.case_id "
                "AND d.role_code='C' AND d.canonical_ingredient IS NOT NULL)",
                2,
            ),
        }
        for reason, (predicate, limit) in predicates.items():
            for case_id, primary_id, version in c.execute(f"""
                SELECT case_id,primary_id,case_version FROM cases c WHERE {predicate}
                ORDER BY CAST(case_id AS BIGINT) LIMIT {limit}
            """).fetchall():
                if case_id not in selected:
                    selected[case_id] = {
                        "case_id": case_id,
                        "primary_id": primary_id,
                        "case_version": version,
                        "reasons": [],
                    }
                selected[case_id]["reasons"].append(reason)
        source_files = c.execute(
            "SELECT table_name,source_path,source_sha256 FROM source_files ORDER BY table_name"
        ).fetchall()
        # Rescan original text files independently, including older DEMO versions.
        source_rows = {table: defaultdict(list) for table in ("DEMO", "DRUG", "REAC")}
        source_headers = {}
        for table, path_string, digest in source_files:
            path = Path(path_string)
            if sha256(path) != digest:
                raise ValueError("Manual review source file changed")
            with path.open(encoding="ascii", newline="") as stream:
                reader = csv.DictReader(stream, delimiter="$", quoting=csv.QUOTE_NONE)
                source_headers[table] = reader.fieldnames
                for source_row, row in enumerate(reader, 2):
                    case_id = row["caseid"].strip()
                    if case_id not in selected:
                        continue
                    if (
                        table == "DEMO"
                        or row["primaryid"].strip() == selected[case_id]["primary_id"]
                    ):
                        source_rows[table][case_id].append({"source_row": source_row, "row": row})
        details = []
        ps = duckdb.connect(str(primary), read_only=True)
        try:
            for case_id, case in sorted(selected.items(), key=lambda item: int(item[0])):
                source_demo = [
                    dict(r["row"], quarter="2025Q4") for r in source_rows["DEMO"][case_id]
                ]
                chosen = latest_cases(source_demo)
                latest_ok = (
                    len(chosen) == 1 and chosen[0]["primaryid"].strip() == case["primary_id"]
                )
                columns = ",".join('"' + h.replace('"', '""') + '"' for h in source_headers["DRUG"])
                loaded = c.execute(
                    f"SELECT {columns} FROM case_drugs WHERE case_id=?", [case_id]
                ).fetchall()
                expected = Counter(
                    tuple(r["row"][h] for h in source_headers["DRUG"])
                    for r in source_rows["DRUG"][case_id]
                )
                actual = Counter(tuple(v or "" for v in row) for row in loaded)
                source_reactions = {
                    normalized_name(r["row"]["pt"])
                    for r in source_rows["REAC"][case_id]
                    if r["row"]["pt"].strip()
                }
                reactions = {
                    r[0]
                    for r in c.execute(
                        "SELECT reaction FROM case_reactions WHERE case_id=?", [case_id]
                    ).fetchall()
                }
                ps_drugs = [
                    r[0]
                    for r in ps.execute(
                        "SELECT drug FROM case_drug_presence WHERE case_id=? ORDER BY drug",
                        [case_id],
                    ).fetchall()
                ]
                ss_drugs = [
                    r[0]
                    for r in c.execute(
                        "SELECT drug FROM case_drug_presence WHERE case_id=? ORDER BY drug",
                        [case_id],
                    ).fetchall()
                ]
                drugs = c.execute(
                    """
                    SELECT drug_seq,role_code,drugname,prod_ai,canonical_ingredient,
                           mapping_method,is_target_exposure,_source_row
                    FROM case_drugs WHERE case_id=? ORDER BY _source_row
                """,
                    [case_id],
                ).fetchall()
                checks = {
                    "latest_source_identity": latest_ok,
                    "all_drug_source_rows": expected == actual,
                    "reaction_membership": reactions == source_reactions,
                }
                if not all(checks.values()):
                    raise ValueError("Manual package source cross-check failed")
                details.append(
                    {
                        **case,
                        "quarter": "2025Q4",
                        "automated_checks": checks,
                        "ps_exposure": ps_drugs,
                        "ps_ss_exposure": ss_drugs,
                        "drug_records": [
                            dict(
                                zip(
                                    [
                                        "drug_seq",
                                        "role",
                                        "drugname",
                                        "prod_ai",
                                        "canonical",
                                        "mapping_method",
                                        "ps_ss_exposure",
                                        "source_row",
                                    ],
                                    row,
                                    strict=True,
                                )
                            )
                            for row in drugs
                        ],
                        "reactions": sorted(reactions),
                        "source_records": {
                            table: source_rows[table][case_id] for table in source_rows
                        },
                        "student_verdict": "pending",
                        "student_notes": "",
                    }
                )
        finally:
            ps.close()
    write_json(output / "cases.json", details)
    write_csv(
        output / "case_checklist.csv",
        [
            {
                "case_id": r["case_id"],
                "primary_id": r["primary_id"],
                "reasons": ";".join(r["reasons"]),
                "latest_version_verified": "",
                "drug_roles_verified": "",
                "mapping_verified": "",
                "reactions_verified": "",
                "reviewer": "",
                "reviewed_on": "",
                "notes": "",
            }
            for r in details
        ],
    )
    lookups = {
        role: {(r["drug"], r["reaction"]): r for r in rows} for role, rows in signals.items()
    }
    reasons = defaultdict(list)
    for pair in benchmark["pairs"]:
        reasons[pair["drug"], pair["reaction"]].append("frozen_positive_benchmark")
    low_support = min(runs["PS"])
    ps_keys = set(runs["PS"][low_support]["pairs"])
    ss_keys = set(runs["PS+SS"][low_support]["pairs"])
    for name, keys in [
        ("lost_after_SS", ps_keys - ss_keys),
        ("gained_after_SS", ss_keys - ps_keys),
    ]:
        for key in sorted(keys)[:2]:
            reasons[key].append(name)
    for role in lookups:
        candidates = [r for r in signals[role] if (r["drug"], r["reaction"]) in ss_keys & ps_keys]
        if candidates:
            row = max(candidates, key=lambda r: (r["lift_python_check"], r["drug"], r["reaction"]))
            reasons[row["drug"], row["reaction"]].append(f"highest_shared_lift_{role}")
        sparse = [r for r in signals[role] if 0 < r["a"] < 5]
        if sparse:
            row = max(sparse, key=lambda r: (r["lift_python_check"], r["drug"], r["reaction"]))
            reasons[row["drug"], row["reaction"]].append(f"sparse_high_lift_{role}")
    screen_changes = sorted(
        k
        for k in lookups["PS"]
        if lookups["PS"][k]["prr_screen_convention"] != lookups["PS+SS"][k]["prr_screen_convention"]
    )
    for key in screen_changes[:2]:
        reasons[key].append("PRR_screen_flip")
    rows = []
    for key, why in sorted(reasons.items()):
        for role in lookups:
            row = lookups[role][key]
            rows.append(
                {
                    "selection_reasons": ";".join(why),
                    "role": role,
                    **row,
                    "accepted_lowest_support": key in runs[role][low_support]["pairs"],
                    "student_verdict": "pending",
                    "student_notes": "",
                }
            )
    write_csv(output / "rules.csv", rows)
    write_csv(
        output / "benchmark_checklist.csv",
        [
            {
                **pair,
                "source_url": benchmark["sources"][pair["source"]]["url"],
                "label_section_verified": "",
                "exact_term_appropriate": "",
                "reviewer": "",
                "reviewed_on": "",
                "notes": "",
            }
            for pair in benchmark["pairs"]
        ],
    )
    (output / "README.md").write_text(
        "# Student inspection packet (2025 Q4 only)\n\n"
        "This is a deterministic engineering sample, not a representative random sample "
        "or course-report prose. "
        "All student verdicts remain pending. Detailed public report records stay local.\n\n"
        "1. Open cases.json alongside case_checklist.csv. Verify latest retained report, "
        "complete source DRUG rows, PS/SS/C roles, distinct ingredient presence, "
        "combination handling and exact reaction memberships. "
        "Source rows are physical text lines including the header. "
        "Automated source checks do not sign off this review.\n"
        "2. Inspect both exact SS zinc-salt cases against "
        "mappings/sensitivity_ss_review.yaml and the regulatory sources. "
        "Confirm that C remains background and the primary mapping is unchanged.\n"
        "3. Use rules.csv to compare raw a,b,c,d,N, lift/PRR/ROR, ROR intervals, "
        "sparse counts and screening flips. "
        "Explain a stable benchmark, a role-sensitive association and a sparse extreme. "
        "Co-listed drugs/reactions do not establish a causal link.\n"
        "4. Check all eight benchmark labels using benchmark_checklist.csv. "
        "Positive-only references cannot estimate specificity.\n"
        "5. Record reviewer/date/verdict/notes yourself. "
        "Draft submission interpretation in your own words. "
        "The PRR flag (a>=3, PRR>=2, Yates chi-square>=4) and unadjusted log-Wald "
        "ROR intervals are descriptive screening conventions, not clinical truth. "
        "Zero-cell ROR intervals are unavailable; no pseudocount is added.\n",
        encoding="utf-8",
        newline="\n",
    )
    result = {
        "status": "ready_for_student_review",
        "student_review_completed": False,
        "cases": len(details),
        "rule_pairs": len(reasons),
        "benchmark_pairs": len(benchmark["pairs"]),
        "automated_source_checks": "passed",
        "report_level_details_in_git": False,
        "source_hashes": {table: digest for table, _, digest in source_files},
        "files": {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    write_json(output / "package_manifest.json", result)
    return result
