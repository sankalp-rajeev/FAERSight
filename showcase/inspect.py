"""Inspect the pinned binary/JDK without invoking mining on any data."""

import argparse
import json
import os
import subprocess
from pathlib import Path

import yaml

from faersight.audit import sha256, write_json

ROOT = Path(__file__).resolve().parent.parent


def pinned_runtime(config_path: Path = ROOT / "showcase/config.yaml") -> tuple[dict, Path, str]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    runtime = config["runtime"]
    java = Path(runtime["java"])
    jar, bounce = ROOT / runtime["jar"], ROOT / runtime["bounce"]
    for path, key in [(java, "java_sha256"), (jar, "jar_sha256"), (bounce, "bounce_sha256")]:
        if sha256(path) != runtime[key]:
            raise ValueError(f"Pinned runtime changed: {path}")
    return config, java, os.pathsep.join([str(jar), str(bounce)])


def collect(output: Path) -> dict:
    config, java, classpath = pinned_runtime()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Inspection snapshot exists")
    output.mkdir(parents=True, exist_ok=True)
    javap = java.with_name("javap.exe")
    commands = [
        ("java_version.txt", [str(java), "-version"]),
        ("javac_version.txt", [str(java.with_name("javac.exe")), "-version"]),
        (
            "jvm_flags.txt",
            [str(java), "-Xmx4g", "-XX:ActiveProcessorCount=2", "-XX:+PrintFlagsFinal", "-version"],
        ),
        ("apriori_help.txt", [str(java), "-cp", classpath, "weka.associations.Apriori", "-h"]),
    ]
    for name in (
        "Apriori",
        "AprioriItemSet",
        "ItemSet",
        "DefaultAssociationRule",
        "DefaultAssociationRule$METRIC_TYPE$1",
        "DefaultAssociationRule$METRIC_TYPE$2",
        "DefaultAssociationRule$METRIC_TYPE$3",
        "DefaultAssociationRule$METRIC_TYPE$4",
    ):
        commands.append(
            (
                name.replace("$", "_") + "_bytecode.txt",
                [str(javap), "-classpath", classpath, "-c", "-p", "weka.associations." + name],
            )
        )
    results = []
    for name, args in commands:
        result = subprocess.run(args, capture_output=True, timeout=60)
        (output / name).write_bytes(result.stdout + result.stderr)
        if result.returncode != 0:
            raise ValueError(f"Inspection failed: {name}; exit={result.returncode}")
        results.append({"file": name, "command": args, "exit_code": result.returncode})
    summary = {
        "status": "inspection_only_no_data_loaded",
        "full_data_mining_started": False,
        "runtime": config["runtime"],
        "javap_sha256": sha256(javap),
        "commands": results,
        "artifacts": {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
        "scientific_findings_validated": False,
    }
    write_json(output / "inspection_manifest.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    result = collect(parser.parse_args().output)
    print(
        json.dumps({k: v for k, v in result.items() if k in {"status", "full_data_mining_started"}})
    )
