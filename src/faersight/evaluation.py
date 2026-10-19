"""Independent contingency checks and explicitly matched ranking comparisons."""

import math
import statistics
from pathlib import Path

import duckdb

from faersight.audit import write_json
from faersight.disproportionality import Counts, metrics
from faersight.mining import read_csv
from faersight.weka import write_csv


def average_ranks(values: list[float]) -> list[float]:
    ranks = [0.0] * len(values)
    order = sorted(range(len(values)), key=values.__getitem__)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        for i in order[start:end]:
            ranks[i] = (start + 1 + end) / 2
        start = end
    return ranks


def spearman(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or any(not math.isfinite(x) for x in left + right):
        raise ValueError("Correlation requires equal, finite pair sets")
    if len(left) < 2 or len(set(left)) < 2 or len(set(right)) < 2:
        return None
    return statistics.correlation(average_ranks(left), average_ranks(right))


def ranking_comparison(rows: list[dict], score: str, top_k: list[int]) -> dict:
    shared = [r for r in rows if math.isfinite(r["weka_lift"]) and math.isfinite(r[score])]
    left = sorted(shared, key=lambda r: (-r["weka_lift"], r["drug"], r["reaction"]))
    right = sorted(shared, key=lambda r: (-r[score], r["drug"], r["reaction"]))
    overlaps = []
    for requested in top_k:
        k = min(requested, len(shared))
        keys = lambda group: {(r["drug"], r["reaction"]) for r in group}  # noqa: E731
        common = len(keys(left[:k]) & keys(right[:k]))
        overlaps.append(
            {
                "requested_k": requested,
                "effective_k": k,
                "overlap_count": common,
                "overlap_fraction": common / k if k else None,
                "lift_boundary_tie": bool(
                    0 < k < len(left) and left[k - 1]["weka_lift"] == left[k]["weka_lift"]
                ),
                "comparison_boundary_tie": bool(
                    0 < k < len(right) and right[k - 1][score] == right[k][score]
                ),
            }
        )
    return {
        "comparison": f"weka_lift_vs_{score}",
        "shared_finite_pairs": len(shared),
        "excluded_nonfinite_pairs": len(rows) - len(shared),
        "spearman": spearman([r["weka_lift"] for r in shared], [r[score] for r in shared]),
        "undefined_correlation_policy": "null_for_less_than_two_or_constant_scores",
        "rank_ties": "average_ranks",
        "top_k_ties": "drug_then_reaction_lexical",
        "top_k": overlaps,
    }


def verify_weka(
    rows: list[dict],
    runs: list[dict],
    signals: list[dict],
    *,
    supports: list[float],
    min_lift: float,
    n: int,
) -> dict[float, dict]:
    """Verify every API rule and exhaustive eligible one-to-one pair coverage."""
    lookup = {(r["drug"], r["reaction"]): r for r in signals}
    reactions = sorted({r["reaction"] for r in signals})
    projections = {f"r{i:04d}": reaction for i, reaction in enumerate(reactions)}
    expected_runs = {(s, p) for s in supports for p in projections}
    observed_runs = set()
    counts = {s: set() for s in supports}
    for run in runs:
        support, projection = float(run["support_requested"]), run["projection"]
        key = support, projection
        if key not in expected_runs or key in observed_runs:
            raise ValueError("Missing, duplicated or unexpected WEKA projection")
        options = run["options"].split()
        if (
            int(run["n"]) != n
            or int(run["attributes"]) != len({r["drug"] for r in signals}) + 1
            or run["cap_reached"] != "false"
            or int(run["cycles"]) != 1
            or "-Z" not in options
            or float(options[options.index("-U") + 1]) != 1.0
            or float(options[options.index("-D") + 1]) != 1.0
            or float(options[options.index("-M") + 1]) != support
            or options[options.index("-T") + 1] != "1"
            or float(options[options.index("-C") + 1]) != min_lift
        ):
            raise ValueError("WEKA settings/population/cap gate failed")
        counts[support].add(int(run["min_support_count"]))
        observed_runs.add(key)
    if observed_runs != expected_runs or any(len(c) != 1 or min(c) < 1 for c in counts.values()):
        raise ValueError("Incomplete projection schedule or inconsistent minimum counts")
    accepted = {s: {} for s in supports}
    for rule in rows:
        support = float(rule["support_requested"])
        key = rule["drug"], rule["reaction"]
        if support not in accepted or key not in lookup or key in accepted[support]:
            raise ValueError("Unknown or duplicate accepted WEKA pair")
        expected = lookup[key]
        if (
            projections.get(rule["projection"]) != rule["reaction"]
            or int(rule["n"]) != n
            or int(rule["joint_count"]) != expected["a"]
            or int(rule["drug_count"]) != expected["a"] + expected["b"]
            or int(rule["reaction_count"]) != expected["a"] + expected["c"]
            or not math.isclose(
                float(rule["weka_confidence"]), expected["confidence"], rel_tol=1e-12, abs_tol=1e-12
            )
            or not math.isclose(
                float(rule["weka_lift"]),
                expected["lift_python_check"],
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        ):
            raise ValueError("WEKA integer counts or exact metrics disagree with mart")
        accepted[support][key] = {
            **expected,
            "weka_lift": float(rule["weka_lift"]),
            "weka_confidence": float(rule["weka_confidence"]),
        }
    result = {}
    for support in supports:
        minimum = next(iter(counts[support]))
        expected = {
            key
            for key, r in lookup.items()
            if r["a"] >= minimum and r["lift_python_check"] >= min_lift
        }
        if set(accepted[support]) != expected:
            raise ValueError("WEKA accepted pair coverage differs from independent thresholds")
        result[support] = {"min_support_count": minimum, "pairs": accepted[support]}
    return result


def benchmark_rows(
    benchmark: dict,
    signals: list[dict],
    accepted: dict,
    connection: duckdb.DuckDBPyConnection,
    n: int,
    min_lift: float,
) -> list[dict]:
    lookup = {(r["drug"], r["reaction"]): r for r in signals}
    result = []
    for pair in benchmark["pairs"]:
        key = pair["drug"], pair["reaction"]
        signal = lookup.get(key)
        if signal is None:
            # An absent candidate vocabulary entry is not a zero count or dropped reference.
            a, exposed, event = connection.execute(
                """
                SELECT
                  (SELECT count(*) FROM case_drug_presence d JOIN case_reactions r USING(case_id)
                   WHERE d.drug=? AND r.reaction=?),
                  (SELECT count(*) FROM case_drug_presence WHERE drug=?),
                  (SELECT count(*) FROM case_reactions WHERE reaction=?)
            """,
                [key[0], key[1], key[0], key[1]],
            ).fetchone()
            signal = metrics(Counts(a, exposed - a, event - a, n - exposed - event + a))
        for support, run in accepted.items():
            if key in run["pairs"]:
                status = "recovered"
            elif key not in lookup:
                status = "not_in_candidate_vocabulary"
            elif signal["a"] + signal["b"] == 0:
                status = "no_target_exposure"
            elif signal["a"] < run["min_support_count"]:
                status = "below_support_count"
            elif signal["lift_python_check"] < min_lift:
                status = "below_lift"
            else:
                raise ValueError("Unexplained missing benchmark pair")
            result.append(
                {
                    **pair,
                    "support_requested": support,
                    "status": status,
                    "in_candidate_vocabulary": key in lookup,
                    **signal,
                }
            )
    return result


def evaluate_experiment(
    database: Path, output: Path, config: dict, experiment: dict, benchmark: dict
) -> dict:
    with duckdb.connect(str(database), read_only=True) as connection:
        n = connection.execute("SELECT count(*) FROM cases").fetchone()[0]
        signals = [
            {"drug": drug, "reaction": reaction, **metrics(Counts(a, b, c, d))}
            for drug, reaction, a, b, c, d in connection.execute(
                "SELECT drug,reaction,a,b,c,d FROM signal_counts ORDER BY drug,reaction"
            ).fetchall()
        ]
        runs = verify_weka(
            read_csv(output / "weka/weka_rules.csv"),
            read_csv(output / "weka/weka_runs.csv"),
            signals,
            supports=experiment["weka"]["support_grid"],
            min_lift=experiment["weka"]["min_metric"],
            n=n,
        )
        positives = benchmark_rows(
            benchmark, signals, runs, connection, n, experiment["weka"]["min_metric"]
        )
    folder = output / "evaluation"
    folder.mkdir()
    write_csv(folder / "all_candidate_counts.csv", signals)
    write_csv(folder / "benchmark_recovery.csv", positives)
    comparisons = []
    ranked = []
    for support, run in runs.items():
        rows = list(run["pairs"].values())
        for score in ("prr", "ror"):
            comparisons.append(
                {"support_requested": support, **ranking_comparison(rows, score, config["top_k"])}
            )
        for rank, row in enumerate(
            sorted(rows, key=lambda r: (-r["weka_lift"], r["drug"], r["reaction"])), 1
        ):
            ranked.append({"support_requested": support, "display_lift_rank": rank, **row})
    fields = ["support_requested", "display_lift_rank", *signals[0], "weka_lift", "weka_confidence"]
    write_csv(folder / "accepted_rules_scored.csv", ranked, fieldnames=fields)
    stability = []
    for low, high in zip(sorted(runs), sorted(runs)[1:], strict=False):
        left, right = set(runs[low]["pairs"]), set(runs[high]["pairs"])
        if not right <= left:
            raise ValueError("Increasing support produced a nonnested accepted set")
        stability.append(
            {
                "lower_support": low,
                "higher_support": high,
                "lower_pairs": len(left),
                "higher_pairs": len(right),
                "jaccard": len(left & right) / len(left | right) if left | right else None,
            }
        )
    write_json(folder / "ranking_comparison.json", comparisons)
    write_json(folder / "support_stability.json", stability)
    result = {
        "status": "computational_gates_passed",
        "eligible_n": n,
        "candidate_pairs": len(signals),
        "support_runs": [
            {
                "support_requested": s,
                "min_support_count": r["min_support_count"],
                "accepted_pairs": len(r["pairs"]),
                "benchmark_total": len(benchmark["pairs"]),
                "benchmark_recovered": sum(
                    p["status"] == "recovered" for p in positives if p["support_requested"] == s
                ),
            }
            for s, r in runs.items()
        ],
        "checks": {
            key: True
            for key in [
                "complete_projection_schedule",
                "fixed_support_options",
                "no_output_cap",
                "complete_reporting_population",
                "unique_accepted_pairs",
                "all_integer_counts_match",
                "exact_confidence_lift_match",
                "exhaustive_threshold_coverage",
                "nested_support_sets",
                "benchmark_denominator_preserved",
                "shared_finite_ranking_universes",
            ]
        },
        "scientific_findings_validated": False,
        "pending_scientific_gates": [
            "student_manual_source_review",
            "benchmark_review",
            "suspect_role_sensitivity",
            "student_interpretation",
        ],
    }
    write_json(folder / "quality_gates.json", result)
    return result
