"""Prepare deterministic Explorer inputs and references; never run an associator."""

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from decimal import Decimal

import yaml

from faersight.audit import sha256, write_json
from showcase.inspect import ROOT, pinned_runtime
from showcase.runner import single_jvm
from showcase_fpgrowth.runner import git
from showcase_metrics.runner import mining_inventory

BASE = ROOT / "showcase_explorer"
GENERATED = ROOT / "artifacts/generated/weka-explorer-demo"
EVIDENCE = ROOT / "artifacts/manifests/weka-explorer-demo"
PRIMARY = ROOT / "artifacts/manifests/2025Q4-statins-mining"


def config():
    return json.loads((BASE / "config.json").read_text())


def select_pair(benchmark, rules):
    positive = {(r["drug"], r["reaction"]) for r in benchmark["pairs"]}
    candidates = [
        r
        for r in rules
        if (r["drug"], r["reaction"]) in positive
        and Decimal(r["support_requested"]) == Decimal("0.00001")
    ]
    candidates.sort(key=lambda r: (r["drug"], r["reaction"]))
    if not candidates:
        raise ValueError("No accepted frozen benchmark-positive pair at 0.00001")
    chosen = candidates[0]
    if (
        sum((r["drug"], r["reaction"]) == (chosen["drug"], chosen["reaction"]) for r in candidates)
        != 1
    ):
        raise ValueError("Ambiguous duplicate frozen representative")
    return {
        "rule": chosen,
        "selection_rule": config()["pair_selection"],
        "candidate_order": [(r["drug"], r["reaction"]) for r in candidates],
    }


def frozen_selection():
    benchmark = yaml.safe_load((ROOT / "benchmarks/known_signals.yaml").read_text())
    with (PRIMARY / "weka_rules.csv").open(encoding="utf-8", newline="") as stream:
        rules = list(csv.DictReader(stream))
    return select_pair(benchmark, rules)


def project_arff(source, destination, names, reaction):
    """Keep seven/all statin columns and exactly one reaction; retain every row."""
    target = [n for n in names if n.startswith("DRUG_")] + ["REAC_" + reaction]
    keep = [names.index(n) for n in target]
    mapping = {old: new for new, old in enumerate(keep)}
    counts = [0] * len(target)
    rows, empty, joint = 0, 0, {}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        source.open(encoding="utf-8") as original,
        destination.open("x", encoding="utf-8", newline="\n") as out,
    ):
        header = []
        for line in original:
            if line.strip().lower() == "@data":
                break
            if line.strip().lower().startswith("@attribute"):
                header.append(line.rstrip("\r\n"))
        if len(header) != len(names):
            raise ValueError("Source attribute/header mismatch")
        out.write("@relation faersight_projection\n\n")
        for old in keep:
            out.write(header[old] + "\n")
        out.write("\n@data\n")
        for line in original:
            line = line.strip()
            if not line:
                continue
            if not (line.startswith("{") and line.endswith("}")):
                raise ValueError("Expected sparse report")
            indexes = set()
            for cell in line[1:-1].split(","):
                if not cell.strip():
                    continue
                index, value = cell.split()
                index = int(index)
                if value != "1" or index in indexes or not 0 <= index < len(names):
                    raise ValueError("Nonbinary/duplicate/out-of-range source cell")
                indexes.add(index)
            present = sorted(mapping[i] for i in indexes if i in mapping)
            out.write("{" + ",".join(f"{i} 1" for i in present) + "}\n")
            for i in present:
                counts[i] += 1
            if len(target) - 1 in present:
                for i in present:
                    if i < len(target) - 1:
                        joint[target[i]] = joint.get(target[i], 0) + 1
            empty += not present
            rows += 1
    return {
        "rows": rows,
        "attributes": len(target),
        "attribute_names": target,
        "source_column_indexes_zero_based": keep,
        "empty_reports": empty,
        "presence_counts": dict(zip(target, counts, strict=True)),
        "drug_reaction_joint_counts": joint,
        "sha256": sha256(destination),
        "selection": "all source rows in identical order; all statins and selected reaction only",
        "new_mining": False,
    }


def native_preflight(arff, output):
    cfg, (_, java, cp) = config(), pinned_runtime()
    output.mkdir(parents=True, exist_ok=False)
    classes = output / "classes"
    classes.mkdir()
    source = BASE / "java/ExplorerPreflight.java"
    compile_cmd = [
        str(java.with_name("javac.exe")),
        "-encoding",
        "UTF-8",
        "-cp",
        cp,
        "-d",
        str(classes.resolve()),
        str(source),
    ]
    command = [
        str(java),
        "-Xmx4g",
        "-XX:ActiveProcessorCount=2",
        "-cp",
        str(classes.resolve()) + os.pathsep + cp,
        "faersight.explorerdemo.ExplorerPreflight",
        str(arff.resolve()),
        str((output / "preflight.json").resolve()),
        " ".join(cfg["primary_options"]),
        " ".join(cfg["apriori_unrestricted_options"]),
        " ".join(cfg["fpgrowth_unrestricted_options"]),
    ]
    with single_jvm():
        compile_result = subprocess.run(compile_cmd, capture_output=True, timeout=120, check=True)
        result = subprocess.run(command, capture_output=True, timeout=120, check=True)
    (output / "compile.txt").write_bytes(compile_result.stdout + compile_result.stderr)
    (output / "stdout.txt").write_bytes(result.stdout)
    (output / "stderr.txt").write_bytes(result.stderr)
    write_json(
        output / "invocation.json",
        {
            "compile_command": compile_cmd,
            "command": command,
            "exit_code": result.returncode,
            "association_builds": 0,
            "GUI_observed": False,
        },
    )
    return json.loads((output / "preflight.json").read_text())


def protect_prior():
    hashes = {}
    for name in git("ls-tree", "-r", "--name-only", "0fd1aef").splitlines():
        if name in {"README.md", "docs/decisions.md", "docs/roadmap.md"}:
            continue
        digest = hashlib.sha256(git("show", "0fd1aef:" + name, binary=True)).hexdigest()
        if sha256(ROOT / name) != digest:
            raise ValueError("Prior source/evidence changed: " + name)
        hashes[name] = digest
    return hashes


def prepare():
    cfg = config()
    protected, before = protect_prior(), mining_inventory()
    source = ROOT / cfg["full_arff"]
    if sha256(source) != cfg["full_arff_sha256"]:
        raise ValueError("Frozen primary input changed")
    GENERATED.mkdir(parents=True, exist_ok=False)
    EVIDENCE.mkdir(parents=True, exist_ok=False)
    selected = frozen_selection()
    names = json.loads((PRIMARY / "arff_manifest.json").read_text())["attributes"]
    projected = GENERATED / "primary_MYOPATHY_projection.arff"
    projection = project_arff(source, projected, names, selected["rule"]["reaction"])
    r = selected["rule"]
    if (projection["rows"], projection["attributes"]) != (cfg["rows"], 8):
        raise ValueError("Projection population changed")
    if (
        projection["presence_counts"]["DRUG_" + r["drug"]] != int(r["drug_count"])
        or projection["presence_counts"]["REAC_" + r["reaction"]] != int(r["reaction_count"])
        or projection["drug_reaction_joint_counts"]["DRUG_" + r["drug"]] != int(r["joint_count"])
    ):
        raise ValueError("Projection/frozen rule counts disagree")
    preflight = native_preflight(projected, GENERATED / "preflight")
    if (preflight["rows"], preflight["attributes"], preflight["empty_reports"]) != (
        projection["rows"],
        projection["attributes"],
        projection["empty_reports"],
    ) or preflight["association_builds"] != 0:
        raise ValueError("WEKA parser/projection mismatch")
    if {c["name"]: c["present"] for c in preflight["presence_counts"]} != projection[
        "presence_counts"
    ]:
        raise ValueError("WEKA presence count mismatch")
    paths = []
    primary_log = f"raw/1.0E-5/{r['projection']}.log"
    with zipfile.ZipFile(PRIMARY / "weka_raw_logs.zip") as zipped:
        (EVIDENCE / "frozen_primary_projected_result.log").write_bytes(zipped.read(primary_log))
        paths.append(
            {
                "source": "artifacts/manifests/2025Q4-statins-mining/weka_raw_logs.zip",
                "archive_member": primary_log,
                "source_sha256": sha256(PRIMARY / "weka_raw_logs.zip"),
            }
        )
    a1 = ROOT / "artifacts/manifests/weka-showcase-fallback-a1-0.004/run"
    with zipfile.ZipFile(a1 / "raw_output.zip") as zipped:
        for algorithm in ("apriori", "fpgrowth"):
            member = algorithm + "/" + algorithm + "_raw.txt"
            (EVIDENCE / f"frozen_A1_{algorithm}_result.log").write_bytes(zipped.read(member))
            paths.append(
                {
                    "source": (a1 / "raw_output.zip").relative_to(ROOT).as_posix(),
                    "archive_member": member,
                    "source_sha256": sha256(a1 / "raw_output.zip"),
                }
            )
    for p in (GENERATED / "preflight").rglob("*"):
        if p.is_file():
            target = EVIDENCE / "preflight" / p.relative_to(GENERATED / "preflight")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
    _, java, cp = pinned_runtime()
    java_version = subprocess.run(
        [str(java), "-version"], capture_output=True, check=True, timeout=30
    )
    (EVIDENCE / "java_version.txt").write_bytes(java_version.stdout + java_version.stderr)
    sources = [p for p in BASE.rglob("*") if p.suffix in {".py", ".java", ".json"}]
    sources += list((ROOT / "tests/showcase_explorer").glob("*.py"))
    own_hashes = {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(sources)}
    launch_command = [
        str(java),
        "-Xmx4g",
        "-XX:ActiveProcessorCount=2",
        "-cp",
        cp,
        "weka.gui.explorer.Explorer",
    ]
    write_json(EVIDENCE / "selection.json", selected)
    write_json(
        EVIDENCE / "projection_manifest.json",
        {
            "source": cfg["full_arff"],
            "source_sha256": cfg["full_arff_sha256"],
            "output": projected.relative_to(ROOT).as_posix(),
            **projection,
        },
    )
    report = {
        "status": "prepared_pending_GUI_connection",
        "framing": cfg["framing"],
        "code_commit": git("rev-parse", "HEAD").strip(),
        "source_hashes": own_hashes,
        "config": cfg,
        "protected_prior_files": protected,
        "primary_selection": selected,
        "projection": projection,
        "native_preflight": preflight,
        "frozen_result_provenance": paths,
        "GUI_load_time_seconds": None,
        "GUI_dimensions": None,
        "full_ARFF_Explorer_usability": "unverified_GUI_connection_unavailable",
        "GUI_result_vs_frozen_evidence": "not_observed",
        "screenshots": [],
        "fallback_10k_generated": False,
        "fallback_required": None,
        "Explorer_launch_command_not_executed": launch_command,
        "full_data_mining_invocations_before": before,
        "new_association_builds": 0,
        "GUI_helper_error": (
            "Computer Use native pipe is unavailable: failed to connect native pipe: "
            "The system cannot find the file specified. (os error 2)"
        ),
        "GUI_helper_attempts": [
            "list_apps",
            "delayed_list_windows",
            "list_windows_after_reset_and_reinitialize",
        ],
        "scientific_findings_validated": False,
    }
    if before != mining_inventory() or protected != protect_prior():
        raise ValueError("Prior evidence/mining inventory changed")
    write_json(EVIDENCE / "preparation_manifest.json", report)
    write_json(
        EVIDENCE / "evidence_index.json",
        {
            "artifacts": {
                p.relative_to(EVIDENCE).as_posix(): sha256(p)
                for p in sorted(EVIDENCE.rglob("*"))
                if p.is_file()
            },
            "scientific_findings_validated": False,
        },
    )
    return {
        "status": report["status"],
        "selected": [r["drug"], r["reaction"]],
        "projection_sha256": projection["sha256"],
        "GUI_observed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(prepare(), indent=2))
