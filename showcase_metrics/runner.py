"""Lock and analyze existing A3 API exports; never launch an association algorithm."""

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

from faersight.audit import sha256
from showcase.inspect import ROOT, pinned_runtime
from showcase.runner import SCHEMA
from showcase_fallback_a1.compare import independent_count_check, read_postings
from showcase_fpgrowth.runner import git
from showcase_metrics.analysis import (
    METRICS,
    VALUES,
    average_ranks,
    correlations,
    distributions,
    key,
    ordered,
    parse_metric,
    plot_pairs,
    rank_gaps,
    reconcile,
    single_to_single,
    statin_itemset_bound,
    top_k,
    write_csv,
    write_json,
)
from showcase_metrics.probe import run_probe

BASE = ROOT / "showcase_metrics"
EVIDENCE = ROOT / "artifacts/manifests/weka-showcase-metrics"
LOCK = EVIDENCE / "locked/analysis_manifest.json"
OUTPUT = ROOT / "artifacts/generated/weka-showcase-metrics/analysis"


def config():
    return json.loads((BASE / "config.json").read_text())


def source_hashes():
    files = [p for p in BASE.rglob("*") if p.suffix in {".py", ".java", ".json"}]
    files += list((ROOT / "tests/showcase_metrics").glob("*.py"))
    return {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(files)}


def protected_history():
    excluded = {"README.md", "docs/decisions.md", "docs/roadmap.md"}
    hashes = {}
    for name in git("ls-tree", "-r", "--name-only", "0c80bd1").splitlines():
        if name in excluded:
            continue
        digest = hashlib.sha256(git("show", "0c80bd1:" + name, binary=True)).hexdigest()
        if sha256(ROOT / name) != digest:
            raise ValueError("Prior file changed: " + name)
        hashes[name] = digest
    return hashes


def mining_inventory():
    result = {}
    for p in (ROOT / "artifacts/generated").rglob("invocation.json"):
        if json.loads(p.read_text()).get("fixture") is False:
            result[p.relative_to(ROOT).as_posix()] = sha256(p)
    return result


def plotting_env():
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(ROOT / ".tools/metric-matplotlib-config")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def plotting_versions():
    code = (
        "import importlib.metadata as m,json; "
        "print(json.dumps({p:m.version(p) for p in ('matplotlib','numpy','pillow')}))"
    )
    result = subprocess.run(
        [config()["plotting_python"], "-c", code],
        capture_output=True,
        timeout=30,
        check=True,
        env=plotting_env(),
    )
    versions = json.loads(result.stdout)
    if versions != config()["plotting_versions"]:
        raise ValueError("Plotting dependency version changed")
    return versions


def lock():
    cfg = config()
    own = source_hashes()
    commit = git("rev-parse", "HEAD").strip()
    for name, digest in own.items():
        if hashlib.sha256(git("show", commit + ":" + name, binary=True)).hexdigest() != digest:
            raise ValueError("Commit analysis sources before locking")
    LOCK.parent.mkdir(parents=True, exist_ok=False)
    original, _, _ = pinned_runtime()
    manifest = {
        "status": "locked_before_full_pool_rank_calculations",
        "code_commit": commit,
        "config": cfg,
        "source_hashes": own,
        "protected_prior_hashes": protected_history(),
        "input": original["input"],
        "runtime": original["runtime"],
        "plotting_versions": plotting_versions(),
        "plotting_python_sha256": sha256(Path(cfg["plotting_python"])),
        "full_data_mining_invocations_before": mining_inventory(),
        "new_association_runs": 0,
        "scientific_findings_validated": False,
    }
    archive = ROOT / cfg["source_area"] / "run/raw_output.zip"
    if sha256(archive) != cfg["source_archive_sha256"]:
        raise ValueError("A3 source archive changed")
    write_json(LOCK, manifest)
    LOCK.with_suffix(".sha256").write_bytes((sha256(LOCK) + "  analysis_manifest.json\n").encode())
    return {
        "manifest_sha256": sha256(LOCK),
        "protected_files": len(manifest["protected_prior_hashes"]),
    }


def verify_lock():
    m = json.loads(LOCK.read_text())
    if git("show", "HEAD:" + LOCK.relative_to(ROOT).as_posix(), binary=True) != LOCK.read_bytes():
        raise ValueError("Analysis manifest must be committed")
    if m["source_hashes"] != source_hashes() or m["config"] != config():
        raise ValueError("Locked code/configuration changed")
    if sha256(Path(config()["plotting_python"])) != m["plotting_python_sha256"]:
        raise ValueError("Locked plotting Python changed")
    for name, digest in m["protected_prior_hashes"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("Protected prior artifact changed: " + name)
    if mining_inventory() != m["full_data_mining_invocations_before"]:
        raise ValueError("Unexpected new or modified full-data mining invocation")
    return m


def load_pool():
    cfg = config()
    area = ROOT / cfg["source_area"]
    index = json.loads((area / "run/evidence_index.json").read_text())
    for name, digest in index["artifacts"].items():
        if sha256(area / "run" / name) != digest:
            raise ValueError("A3 indexed evidence mismatch")
    archive = area / "run/raw_output.zip"
    if sha256(archive) != cfg["source_archive_sha256"]:
        raise ValueError("Wrong source archive")
    miners, provenance = {}, {}
    with zipfile.ZipFile(archive) as zipped:
        if set(zipped.namelist()) != set(index["raw_output_hashes"]):
            raise ValueError("Archive members changed")
        for name, digest in index["raw_output_hashes"].items():
            if hashlib.sha256(zipped.read(name)).hexdigest() != digest:
                raise ValueError("Native artifact hash mismatch")
        for algorithm in ("apriori", "fpgrowth"):
            raw = zipped.read(algorithm + "/rules.csv")
            metadata = json.loads(zipped.read(algorithm + "/run.json"))
            invocation = json.loads(zipped.read(algorithm + "/invocation.json"))
            if invocation["status"] != "passed" or metadata["returned_rules"] != 586:
                raise ValueError("A3 completion mismatch")
            if metadata.get("minimum_count", metadata.get("resolved_lower_count")) != 771:
                raise ValueError("A3 minimum count mismatch")
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
            if reader.fieldnames != SCHEMA:
                raise ValueError("Wrong API export schema")
            pool = {}
            for original in reader:
                lhs, rhs = (json.loads(original[k]) for k in ("antecedent", "consequent"))
                if not lhs or not rhs or lhs != sorted(set(lhs)) or rhs != sorted(set(rhs)):
                    raise ValueError("Noncanonical rule")
                if set(lhs) & set(rhs) or any(not i.endswith("=1") for i in lhs + rhs):
                    raise ValueError("Nonpresence or overlapping rule")
                row = {"antecedent": lhs, "consequent": rhs}
                row.update(
                    {
                        k: int(original[k])
                        for k in ("joint_count", "antecedent_count", "consequent_count", "n")
                    }
                )
                row.update({m: parse_metric(original[m], m) for m in VALUES})
                if row["n"] != 385288 or row["joint_count"] < 771 or row["lift"] < 1.2:
                    raise ValueError("Frozen population/qualification changed")
                reconcile(row)
                row["raw_API_values"] = {m: original[m] for m in VALUES}
                if key(row) in pool:
                    raise ValueError("Duplicate rule")
                pool[key(row)] = row
            miners[algorithm] = pool
            provenance[algorithm] = {
                "archive_member": algorithm + "/rules.csv",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "rules": len(pool),
                "minimum_count": 771,
            }
    a, f = miners["apriori"], miners["fpgrowth"]
    if set(a) != set(f) or len(a) != 586:
        raise ValueError("Frozen common-pool identity changed")
    for k in a:
        for field in ("joint_count", "antecedent_count", "consequent_count", "n", *VALUES):
            if a[k][field] != f[k][field]:
                raise ValueError("Source pools no longer have exactly identical counts/metrics")
    rows = [a[k] for k in sorted(a)]
    if len(single_to_single(rows)) != 472:
        raise ValueError("Single-to-single population changed")
    return rows, provenance


def run():
    manifest = verify_lock()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    cfg = config()
    rows, provenance = load_pool()
    if sha256(ROOT / manifest["input"]["path"]) != manifest["input"]["sha256"]:
        raise ValueError("Frozen ARFF changed")
    names = json.loads(
        (ROOT / "artifacts/manifests/2025Q4-statins-mining/arff_manifest.json").read_text()
    )["attributes"]
    posts, n, empty = read_postings(ROOT / manifest["input"]["path"], names)
    if (n, empty) != (385288, 117325):
        raise ValueError("Frozen denominator changed")
    count_check = independent_count_check({key(r): r for r in rows}, posts)
    maxima = {m: max(reconcile(r)[m] for r in rows) for m in VALUES}
    ranks = {m: average_ranks(rows, m) for m in METRICS}
    for row in rows:
        row["average_ranks"] = {m: ranks[m][key(row)] for m in METRICS}
        row["source_miners"] = ["apriori", "fpgrowth"]
    write_json(OUTPUT / "canonical_pool.json", rows)
    write_csv(OUTPUT / "canonical_pool.csv", rows)
    for metric in METRICS:
        ranking = [
            {
                "deterministic_position": i,
                "metric": metric,
                "metric_value": r[metric],
                "statistical_average_rank": ranks[metric][key(r)],
                **r,
            }
            for i, r in enumerate(ordered(rows, metric), 1)
        ]
        write_json(OUTPUT / f"ranking_{metric}.json", ranking)
        write_csv(OUTPUT / f"ranking_{metric}.csv", ranking)
    full = correlations(rows, "all_586")
    single = correlations(single_to_single(rows), "single_to_single_472")
    overlaps, boundaries, four = top_k(rows, cfg["top_k"])
    gaps = rank_gaps(rows, cfg)
    stats = distributions(rows, cfg["percentiles"])
    pairs, bound = statin_itemset_bound(posts)
    bound["singleton_counts"] = {k: len(v) for k, v in posts.items() if k.startswith("DRUG_")}
    bound["thresholds"] = cfg["support_count_comparisons"]
    maximum = bound["all_statin_containing_itemsets_size_ge_2_maximum_joint_count"]
    bound["comparisons"] = [
        {
            "support": support,
            "algorithm": a,
            "minimum_count": minimum,
            "maximum_statin_itemset_joint_count": maximum,
            "below_minimum": maximum < minimum,
        }
        for support, algorithms in cfg["support_count_comparisons"].items()
        for a, minimum in algorithms.items()
    ]
    if not all(r["below_minimum"] for r in bound["comparisons"]):
        raise ValueError("Proposed statin absence explanation not supported")
    bound["conclusion"] = "No statin-containing itemset of size 2 or more reaches the minimum."
    confidence_one = [r for r in rows if r["confidence"] == 1.0]
    probe = run_probe(OUTPUT / "metric_api_probe")
    edge = {
        "pool_confidence_one_rules": confidence_one,
        "pool_confidence_one_count": len(confidence_one),
        "pool_positive_infinite_conviction_count": sum(
            r["conviction"] == float("inf") for r in rows
        ),
        "pool_special_sentinel_or_capped_conviction_count": 0,
        "convention": probe["formula"],
        "count_only_API_probe": probe,
    }
    data = {
        "metrics": list(METRICS),
        "correlations": full,
        "scatter_pairs": plot_pairs(full),
        "rules": rows,
    }
    for name, value in [
        ("spearman_full", full),
        ("spearman_single_to_single", single),
        ("top_k_overlap", overlaps),
        ("boundary_ties", boundaries),
        ("four_way_top_k", four),
        ("rank_gap_examples", gaps),
        ("metric_distributions", stats),
        ("statin_support_bound", bound),
        ("conviction_edge_cases", edge),
        ("chart_data", data),
    ]:
        write_json(OUTPUT / f"{name}.json", value)
    for name, values in [
        ("spearman", full + single),
        ("top_k_overlap", overlaps),
        ("boundary_ties", boundaries),
        ("metric_distributions", stats),
        ("statin_pair_counts", pairs),
        ("statin_threshold_comparison", bound["comparisons"]),
    ]:
        write_csv(OUTPUT / f"{name}.csv", values)
    versions = plotting_versions()
    command = [
        cfg["plotting_python"],
        "-m",
        "showcase_metrics.plots",
        str(OUTPUT / "chart_data.json"),
        str(OUTPUT / "charts"),
    ]
    rendered = subprocess.run(
        command, env=plotting_env(), capture_output=True, timeout=120, check=True
    )
    (OUTPUT / "plot_stdout.txt").write_bytes(rendered.stdout)
    (OUTPUT / "plot_stderr.txt").write_bytes(rendered.stderr)
    report = {
        "status": "passed",
        "analysis_manifest_sha256": sha256(LOCK),
        "code_commit": manifest["code_commit"],
        "source_provenance": provenance,
        "canonical_rules": len(rows),
        "source_pools_identical": True,
        "independent_ARFF_counts": count_check,
        "maximum_independent_metric_differences": maxima,
        "plot_command": command,
        "plot_versions": versions,
        "new_association_runs": 0,
        "scientific_findings_validated": False,
    }
    write_json(OUTPUT / "outcome.json", report)
    verify_lock()
    return report


def snapshot():
    verify_lock()
    target = EVIDENCE / "run"
    target.mkdir(parents=True, exist_ok=False)
    hashes = {
        p.relative_to(OUTPUT).as_posix(): sha256(p)
        for p in sorted(OUTPUT.rglob("*"))
        if p.is_file()
    }
    for name in hashes:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(OUTPUT / name, dest)
    write_json(
        target / "evidence_index.json",
        {"artifacts": hashes, "scientific_findings_validated": False},
    )
    return {"status": "snapshotted", "files": len(hashes)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["lock", "run", "snapshot"])
    args = parser.parse_args()
    print(json.dumps({"lock": lock, "run": run, "snapshot": snapshot}[args.mode](), indent=2))
