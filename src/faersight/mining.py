"""Pinned Java/WEKA execution; Python performs no association-rule search."""

import csv
import json
import math
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import yaml

from faersight.arff import export_mart_arff
from faersight.audit import sha256, write_json
from faersight.config import load_ingestion_config
from faersight.weka import find_java


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_mining_config(path: Path) -> tuple[dict, dict, dict, dict[Path, str]]:
    root = path.resolve().parent.parent
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {
        "schema_version": 1,
        "status": "frozen",
        "strategy": "weka_apriori_per_reaction_projection",
        "support_schedule": "fixed_lower_bound_upper_one_delta_one",
        "binary_values": ["0", "1"],
        "treat_zero_as_missing": True,
        "retain_empty_background_cases": True,
    }
    if not isinstance(config, dict) or any(config.get(k) != v for k, v in required.items()):
        raise ValueError("Unsupported or unfrozen mining configuration")
    if (
        not re.fullmatch(r"[1-9]\d*[mg]", str(config.get("heap", "")))
        or type(config.get("active_processors")) is not int
        or not 1 <= config["active_processors"] <= 32
        or type(config.get("timeout_seconds")) is not int
        or config["timeout_seconds"] < 1
        or not isinstance(config.get("top_k"), list)
        or not config["top_k"]
        or any(type(k) is not int or k < 1 for k in config["top_k"])
    ):
        raise ValueError("Invalid resource or ranking configuration")
    paths = [path.resolve()]
    for key in ("experiment_file", "benchmark_file"):
        selected = (root / config[key]).resolve()
        if not selected.is_relative_to(root) or not selected.is_file():
            raise ValueError(f"{key} must exist inside the repository")
        paths.append(selected)
    experiment, class_config, mapping = load_ingestion_config(paths[1])
    grid = experiment["weka"]["support_grid"]
    if len(grid) != len(set(grid)):
        raise ValueError("Duplicate support thresholds")
    benchmark = yaml.safe_load(paths[2].read_text(encoding="utf-8"))
    if (
        not isinstance(benchmark, dict)
        or benchmark.get("schema_version") != 1
        or benchmark.get("status") != "frozen"
        or benchmark.get("coding_policy") != "exact_uppercase_reaction_term_no_synonym_expansion"
        or not 5 <= len(benchmark.get("pairs", [])) <= 10
    ):
        raise ValueError("Expected a frozen 5-10 pair exact-term positive benchmark")
    keys = set()
    for pair in benchmark["pairs"]:
        source = benchmark.get("sources", {}).get(pair.get("source"), {})
        key = (pair.get("drug"), pair.get("reaction"))
        if (
            key in keys
            or key[0] not in class_config["ingredients"]
            or not isinstance(key[1], str)
            or not key[1].strip()
            or key[1] != key[1].upper().strip()
            or source.get("drug") != key[0]
            or not str(source.get("url", "")).startswith(
                "https://www.accessdata.fda.gov/drugsatfda_docs/label/"
            )
            or type(source.get("label_year")) is not int
            or source["label_year"] >= int(min(experiment["quarters"])[:4])
        ):
            raise ValueError("Invalid or duplicate benchmark pair/source")
        keys.add(key)
    paths.extend([root / experiment["therapeutic_class_file"], mapping, root / "uv.lock"])
    return config, experiment, benchmark, {p: sha256(p) for p in paths}


def run_apriori(
    arff: Path,
    output: Path,
    *,
    jar: Path,
    supports: list[float],
    min_lift: float,
    max_rules: int,
    expected_n: int,
    mode: str = "projected",
    java: str | None = None,
    heap: str = "4g",
    active_processors: int = 2,
    timeout: int = 1800,
) -> dict:
    """Compile the bundled bridge with the existing JDK, retaining failures/logs."""
    if (
        not supports
        or len(supports) != len(set(supports))
        or any(not math.isfinite(s) or not 0 < s <= 1 for s in supports)
        or not math.isfinite(min_lift)
        or min_lift <= 0
        or max_rules < 1
        or expected_n < 1
        or mode not in {"full", "projected"}
        or not re.fullmatch(r"[1-9]\d*[mg]", heap)
        or not 1 <= active_processors <= 32
        or timeout < 1
    ):
        raise ValueError("Invalid WEKA execution arguments")
    if output.exists() and any(output.iterdir()):
        raise ValueError("WEKA output exists; choose a new output directory")
    java_path = Path(find_java(java)).resolve()
    javac = java_path.with_name("javac.exe" if os.name == "nt" else "javac")
    if not javac.is_file() or not jar.is_file():
        raise ValueError("Existing JDK compiler and WEKA jar are required")
    output.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).parent / "java" / "WekaExperiment.java"
    classes = output / "classes"
    classes.mkdir()
    classpath = os.pathsep.join([str(jar.resolve()), str(jar.resolve().parent / "*")])
    manifest = {
        "status": "running",
        "started_utc": datetime.now(UTC).isoformat(),
        "java_executable": str(java_path),
        "java_executable_sha256": sha256(java_path),
        "javac_sha256": sha256(javac),
        "bridge_sha256": sha256(source),
        "arff_sha256": sha256(arff),
        "runtime_jars": {p.name: sha256(p) for p in sorted(jar.parent.glob("*.jar"))},
        "weka_version": "3.8.6",
        "expected_n": expected_n,
        "mode": mode,
        "supports": supports,
        "min_lift": min_lift,
        "max_rules": max_rules,
        "scientific_findings_validated": False,
    }
    write_json(output / "manifest.json", manifest)
    try:
        for command, log in [
            ([str(java_path), "-version"], "java_version.log"),
            ([str(javac), "-version"], "javac_version.log"),
            (
                [
                    str(javac),
                    "-encoding",
                    "UTF-8",
                    "-cp",
                    classpath,
                    "-d",
                    str(classes.resolve()),
                    str(source.resolve()),
                ],
                "compile.log",
            ),
        ]:
            with (output / log).open("wb") as stream:
                subprocess.run(
                    command, stdout=stream, stderr=subprocess.STDOUT, timeout=120, check=True
                )
        command = [
            str(java_path),
            f"-Xmx{heap}",
            f"-XX:ActiveProcessorCount={active_processors}",
            "-cp",
            str(classes.resolve()) + os.pathsep + classpath,
            "faersight.WekaExperiment",
            str(arff.resolve()),
            str(output.resolve()),
            ",".join(str(s) for s in supports),
            str(min_lift),
            str(max_rules),
            str(expected_n),
            mode,
        ]
        manifest["command"] = command
        write_json(output / "manifest.json", manifest)
        with (output / "progress.log").open("wb") as stream:
            subprocess.run(
                command, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout, check=True
            )
        if not (output / "complete.txt").is_file() or sha256(arff) != manifest["arff_sha256"]:
            raise ValueError("Incomplete WEKA run or input changed during execution")
        runs = read_csv(output / "weka_runs.csv")
        if not runs or any(row["cap_reached"] != "false" for row in runs):
            raise ValueError("WEKA output cap reached or no projections completed")
        if any(int(row["n"]) != expected_n for row in runs):
            raise ValueError("WEKA changed the reporting universe")
        manifest["status"] = "passed"
        manifest["runs"] = len(runs)
        manifest["accepted_rules"] = len(read_csv(output / "weka_rules.csv"))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        raise
    finally:
        manifest["finished_utc"] = datetime.now(UTC).isoformat()
        manifest["artifacts"] = {
            str(p.relative_to(output)).replace("\\", "/"): sha256(p)
            for p in sorted(output.rglob("*"))
            if p.is_file() and p.name != "manifest.json"
        }
        write_json(output / "manifest.json", manifest)
    return manifest


def run_experiment(
    database: Path, output: Path, *, config_path: Path, jar: Path, java: str | None = None
) -> dict:
    config, experiment, benchmark, inputs = load_mining_config(config_path)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Experiment exists; choose a new output directory")
    integration = json.loads((database.parent / "integration_manifest.json").read_text())
    root = config_path.resolve().parent.parent
    for key, path in [
        ("experiment_config_sha256", root / config["experiment_file"]),
        ("class_config_sha256", root / experiment["therapeutic_class_file"]),
    ]:
        if integration.get(key) != sha256(path):
            raise ValueError("Mart configuration differs from frozen experiment")
    mapping_path = next(p for p in inputs if p.suffix == ".csv")
    if integration.get("mapping_sha256") != inputs[mapping_path]:
        raise ValueError("Mart mapping differs from frozen experiment")
    source_paths = [
        p for p in sorted(Path(__file__).parent.rglob("*")) if p.suffix in {".py", ".java", ".sql"}
    ]
    source_hashes = {p: sha256(p) for p in source_paths}
    exported = export_mart_arff(database, output / "input")
    weka = experiment["weka"]
    git_prefix = ["git", "-c", f"safe.directory={root.as_posix()}"]
    git = subprocess.run(
        [*git_prefix, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30, check=True
    ).stdout.strip()
    dirty = subprocess.run(
        [*git_prefix, "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    ).stdout.strip()
    try:
        run_apriori(
            output / "input/transactions.arff",
            output / "weka",
            jar=jar,
            supports=weka["support_grid"],
            min_lift=weka["min_metric"],
            max_rules=weka["max_rules"],
            expected_n=exported["eligible_n"],
            java=java,
            heap=config["heap"],
            active_processors=config["active_processors"],
            timeout=config["timeout_seconds"],
        )
        from faersight.evaluation import evaluate_experiment

        result = evaluate_experiment(database, output, config, experiment, benchmark)
        if any(sha256(p) != digest for p, digest in inputs.items()):
            raise ValueError("Frozen inputs changed during experiment")
        if any(sha256(p) != digest for p, digest in source_hashes.items()):
            raise ValueError("Source code changed during experiment")
        if sha256(database) != exported["source_mart_sha256"]:
            raise ValueError("Mart changed during experiment")
        result["input_hashes"] = {str(p.relative_to(root)): h for p, h in inputs.items()}
        result["source_mart_sha256"] = exported["source_mart_sha256"]
        result["git_commit"] = git
        result["git_worktree_dirty"] = bool(dirty)
        result["source_code_hashes"] = {
            str(p.relative_to(Path(__file__).parent)).replace("\\", "/"): h
            for p, h in source_hashes.items()
        }
        result["artifacts"] = {
            str(p.relative_to(output)).replace("\\", "/"): sha256(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        }
        write_json(output / "experiment_manifest.json", result)
        return result
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        write_json(
            output / "experiment_failure.json",
            {
                "status": "failed",
                "error": str(exc),
                "scientific_findings_validated": False,
            },
        )
        raise
