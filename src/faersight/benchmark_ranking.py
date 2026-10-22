"""Benchmark ranks with declared pools, ties, finite-score and exclusion policies."""

import math

from faersight.evaluation import average_ranks

SCORES = ("lift_python_check", "prr", "ror")


def benchmark_ranks(
    signals: list[dict], benchmark: dict, accepted: dict[float, dict], role: str
) -> list[dict]:
    lookup = {(r["drug"], r["reaction"]): r for r in signals}
    pools = [("all_candidates", None, set(lookup))] + [
        ("weka_accepted", support, set(run["pairs"])) for support, run in sorted(accepted.items())
    ]
    output = []
    for pool_name, support, keys in pools:
        finite = sorted(key for key in keys if all(math.isfinite(lookup[key][s]) for s in SCORES))
        size = len(finite)
        rank_maps = {
            score: dict(
                zip(finite, average_ranks([-lookup[key][score] for key in finite]), strict=True)
            )
            for score in SCORES
        }
        for pair in benchmark["pairs"]:
            key = pair["drug"], pair["reaction"]
            if key not in lookup:
                status = "not_in_candidate_vocabulary"
            elif key not in keys:
                status = "not_weka_accepted"
            elif key not in rank_maps[SCORES[0]]:
                status = "nonfinite_score_excluded_from_shared_pool"
            else:
                status = "ranked"
            for score in SCORES:
                rank = rank_maps[score].get(key)
                percentile = (
                    (100 * (size - rank) / (size - 1) if size > 1 else 100.0)
                    if rank is not None
                    else None
                )
                output.append(
                    {
                        "role": role,
                        **pair,
                        "pool": pool_name,
                        "support_requested": support,
                        "metric": "lift" if score == SCORES[0] else score,
                        "score": lookup[key][score] if key in lookup else None,
                        "rank": rank,
                        "percentile": percentile,
                        "pool_size": size,
                        "nonfinite_pairs_excluded": len(keys) - size,
                        "status": status,
                        "rank_ties": "average_descending",
                        "percentile_direction": "100_highest_0_lowest",
                    }
                )
    return output
