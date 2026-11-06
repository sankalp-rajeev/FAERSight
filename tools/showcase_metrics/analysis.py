"""Count-validated full-precision rankings; no rule discovery or metric filtering."""

import csv
import json
import math
import statistics
from collections import Counter
from itertools import combinations

METRICS = ("confidence", "lift", "leverage", "conviction")
VALUES = ("support", *METRICS)
TOLERANCE = 1e-12


def parse_metric(raw, metric):
    value = float(raw)
    if math.isnan(value) or value == -math.inf or (math.isinf(value) and metric != "conviction"):
        raise ValueError("Invalid metric: " + metric)
    return value


def safe_json(value):
    if isinstance(value, float) and math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {k: safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_json(v) for v in value]
    return value


def write_json(path, value):
    path.write_text(
        json.dumps(safe_json(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path, rows, fields=None):
    if fields is None:
        fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(safe_json(v), sort_keys=True, separators=(",", ":"))
                    if isinstance(v, (dict, list, tuple))
                    else safe_json(v)
                    for k, v in row.items()
                }
            )


def key(row):
    return tuple(row["antecedent"]), tuple(row["consequent"])


def recompute(joint, lhs, rhs, n):
    if not (0 < joint <= min(lhs, rhs) <= n and n - lhs - rhs + joint >= 0):
        raise ValueError("Invalid contingency counts")
    return {
        "support": joint / n,
        "confidence": joint / lhs,
        "lift": (joint / lhs) / (rhs / n),
        "leverage": joint / n - (lhs / n) * (rhs / n),
        "conviction": (lhs * (n - rhs) / n) / (lhs - joint + 1),
    }


def reconcile(row):
    expected = recompute(
        *(row[k] for k in ("joint_count", "antecedent_count", "consequent_count", "n"))
    )
    differences = {}
    for metric, wanted in expected.items():
        actual = row[metric]
        if not math.isclose(actual, wanted, rel_tol=TOLERANCE, abs_tol=TOLERANCE):
            raise ValueError("WEKA/count discrepancy in " + metric)
        differences[metric] = abs(actual - wanted)
    return differences


def ordered(rows, metric):
    return sorted(rows, key=lambda row: (-row[metric], key(row)))


def average_ranks(rows, metric):
    ranked = ordered(rows, metric)
    result, start = {}, 0
    while start < len(ranked):
        end = start + 1
        while end < len(ranked) and ranked[end][metric] == ranked[start][metric]:
            end += 1
        rank = (start + 1 + end) / 2
        for row in ranked[start:end]:
            result[key(row)] = rank
        start = end
    return result


def spearman(rows, a, b):
    ar, br = average_ranks(rows, a), average_ranks(rows, b)
    xs, ys = [ar[key(r)] for r in rows], [br[key(r)] for r in rows]
    xm, ym = statistics.mean(xs), statistics.mean(ys)
    dx, dy = [x - xm for x in xs], [y - ym for y in ys]
    denominator = math.sqrt(math.fsum(x * x for x in dx) * math.fsum(y * y for y in dy))
    if not denominator:
        return None
    return math.fsum(x * y for x, y in zip(dx, dy, strict=True)) / denominator


def single_to_single(rows):
    return [
        r
        for r in rows
        if len(r["antecedent"]) == len(r["consequent"]) == 1
        and all(i.startswith("REAC_") for i in r["antecedent"] + r["consequent"])
    ]


def correlations(rows, population):
    return [
        {
            "population": population,
            "rules": len(rows),
            "metric_a": a,
            "metric_b": b,
            "spearman": spearman(rows, a, b),
        }
        for a, b in combinations(sorted(METRICS), 2)
    ]


def top_k(rows, ks):
    overlaps, boundaries, four_way = [], [], []
    for k in ks:
        if k > len(rows):
            raise ValueError("K exceeds population")
        groups = {}
        for metric in METRICS:
            ranking = ordered(rows, metric)
            groups[metric] = {key(r) for r in ranking[:k]}
            boundary = ranking[k - 1][metric]
            total = sum(r[metric] == boundary for r in ranking)
            inside = sum(r[metric] == boundary for r in ranking[:k])
            boundaries.append(
                {
                    "metric": metric,
                    "k": k,
                    "boundary_value": boundary,
                    "boundary_group_size": total,
                    "boundary_inside": inside,
                    "boundary_outside": total - inside,
                    "membership_split_by_lexical_order": total > inside,
                }
            )
        for a, b in combinations(sorted(METRICS), 2):
            intersection, union = len(groups[a] & groups[b]), len(groups[a] | groups[b])
            overlaps.append(
                {
                    "k": k,
                    "metric_a": a,
                    "metric_b": b,
                    "intersection": intersection,
                    "union": union,
                    "jaccard": intersection / union,
                    "overlap_fraction_k": intersection / k,
                }
            )
        common = set.intersection(*groups.values())
        four_way.append({"k": k, "intersection": len(common), "rules": sorted(common)})
    return overlaps, boundaries, four_way


def distributions(rows, percentiles):
    results = []
    for metric in METRICS:
        values = sorted(r[metric] for r in rows)
        frequencies = Counter(values)
        tied = sum(count for count in frequencies.values() if count > 1)
        infinities = sum(math.isinf(v) for v in values)
        results.append(
            {
                "metric": metric,
                "minimum": values[0],
                "median": statistics.median(values),
                "mean": statistics.mean(values) if not infinities else None,
                "mean_note": "finite"
                if not infinities
                else "no conventional finite mean: positive infinity",
                "maximum": values[-1],
                "infinite_count": infinities,
                "percentiles": {
                    str(p): values[max(0, math.ceil(p * len(values) / 100) - 1)]
                    for p in percentiles
                },
                "distinct_values": len(frequencies),
                "rules_in_ties": tied,
                "fraction_in_ties": tied / len(values),
                "largest_tie_group": max(frequencies.values()),
            }
        )
    return results


def rank_gaps(rows, cfg):
    ranks = {metric: average_ranks(rows, metric) for metric in METRICS}
    result = {}
    for name, (lower, higher) in cfg["rank_gaps"].items():
        candidates = []
        for row in rows:
            gap = ranks[lower][key(row)] - ranks[higher][key(row)]
            if gap >= cfg["rank_gap_minimum"]:
                candidates.append(
                    {
                        **row,
                        "average_ranks": {m: ranks[m][key(row)] for m in METRICS},
                        "rank_gap": gap,
                        "category": name,
                    }
                )
        candidates.sort(key=lambda r: (-r["rank_gap"], key(r)))
        result[name] = {
            "eligible_rules": len(candidates),
            "examples": candidates[: cfg["rank_gap_maximum_examples"]],
        }
    return result


def plot_pairs(correlations_):
    if any(r["spearman"] is None for r in correlations_):
        raise ValueError("Undefined correlation cannot select scatterplots")
    high = min(correlations_, key=lambda r: (-r["spearman"], r["metric_a"], r["metric_b"]))
    low = min(correlations_, key=lambda r: (r["spearman"], r["metric_a"], r["metric_b"]))
    return [{"selection": name, **row} for name, row in [("highest", high), ("lowest", low)]]


def statin_itemset_bound(posts):
    drugs = sorted(k for k in posts if k.startswith("DRUG_"))
    reactions = sorted(k for k in posts if k.startswith("REAC_"))
    pairs = []
    for a, b in [(a, b) for a in drugs for b in reactions] + list(combinations(drugs, 2)):
        pairs.append(
            {
                "items": sorted([a, b]),
                "joint_count": len(posts[a] & posts[b]),
                "family": "statin_reaction" if b.startswith("REAC_") else "statin_statin",
            }
        )
    pairs.sort(key=lambda row: row["items"])
    maximum = max(r["joint_count"] for r in pairs)
    families = {}
    for family in ("statin_reaction", "statin_statin"):
        selected = [r for r in pairs if r["family"] == family]
        top = max(r["joint_count"] for r in selected)
        families[family] = {
            "pairs_checked": len(selected),
            "maximum_joint_count": top,
            "maximum_witnesses": [r for r in selected if r["joint_count"] == top],
        }
    return pairs, {
        "all_statin_containing_itemsets_size_ge_2_maximum_joint_count": maximum,
        "maximum_witnesses": [r for r in pairs if r["joint_count"] == maximum],
        "families": families,
        "proof": (
            "Every statin-containing itemset size>=2 contains a statin-reaction or "
            "statin-statin pair; support of a superset cannot exceed its subset. "
            "Pairs are in the family, so this bound is attained."
        ),
    }
