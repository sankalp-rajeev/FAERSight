"""Capture pinned FPGrowth implementation and marginal-only fallback evidence."""

import argparse
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

from faersight.audit import sha256, write_json
from showcase.inspect import ROOT, pinned_runtime
from showcase.runner import single_jvm


def collect(output: Path):
    config, java, cp = pinned_runtime()
    output.mkdir(parents=True, exist_ok=False)
    commands = [
        ("java_version.txt", [str(java), "-version"]),
        ("javac_version.txt", [str(java.with_name("javac.exe")), "-version"]),
        ("fpgrowth_help.txt", [str(java), "-cp", cp, "weka.associations.FPGrowth", "-h"]),
    ]
    for name in [
        "FPGrowth",
        "FPGrowth$AssociationRule",
        "FPGrowth$FrequentBinaryItemSet",
        "FPGrowth$FrequentItemSets",
        "FPGrowth$FPTreeRoot",
        "BinaryItem",
        "DefaultAssociationRule",
        "DefaultAssociationRule$METRIC_TYPE$4",
    ]:
        commands.append(
            (
                name.replace("$", "_") + "_bytecode.txt",
                [
                    str(java.with_name("javap.exe")),
                    "-classpath",
                    cp,
                    "-c",
                    "-p",
                    "weka.associations." + name,
                ],
            )
        )
    records = []
    with single_jvm():
        for name, command in commands:
            result = subprocess.run(command, capture_output=True, timeout=60)
            (output / name).write_bytes(result.stdout + result.stderr)
            # Missing guessed nested classes are retained as inspection evidence.
            records.append({"file": name, "argv": command, "exit_code": result.returncode})
    write_json(
        output / "inspection_manifest.json",
        {
            "commands": records,
            "runtime": config["runtime"],
            "new_full_data_run_started": False,
            "hashes": {p.name: sha256(p) for p in output.iterdir() if p.is_file()},
        },
    )


def marginals(output: Path):
    config, _, _ = pinned_runtime()
    source = ROOT / config["input"]["path"]
    assert sha256(source) == config["input"]["sha256"]
    names = json.loads(
        (ROOT / "artifacts/manifests/2025Q4-statins-mining/arff_manifest.json").read_text()
    )["attributes"]
    counts, rows, empty = Counter(), 0, 0
    with source.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip().lower() == "@data":
                break
        for line in stream:
            line = line.strip()
            if not line:
                continue
            assert line.startswith("{") and line.endswith("}")
            indexes = []
            for cell in line[1:-1].split(","):
                if cell.strip():
                    index, value = cell.split()
                    assert value == "1"
                    indexes.append(int(index))
            assert len(set(indexes)) == len(indexes)
            counts.update(indexes)
            rows += 1
            empty += not indexes
    assert rows == 385288 and len(names) == 366 and empty == 117325
    drugs = {name: counts[i] for i, name in enumerate(names) if name.startswith("DRUG_")}
    ladder = []
    for support in ("0.004", "0.003", "0.002"):
        # FPGrowth rounding is provisional until pinned-bytecode verification.
        a, f = int(float(support) * rows + 0.5), math.ceil(float(support) * rows)
        ladder.append(
            {
                "support": support,
                "apriori_count": a,
                "fpgrowth_ceil_count": f,
                "apriori_eligible_statins": [k for k, v in drugs.items() if v >= a],
                "fpgrowth_eligible_statins": [k for k, v in drugs.items() if v >= f],
            }
        )
    result = {
        "input": config["input"],
        "rows": rows,
        "empty_transactions": empty,
        "statin_presence_counts": drugs,
        "fallback_a_ladder": ladder,
        "basis": "Frozen PS single-item marginals only; no association rules mined",
        "eligibility_is_not_rule_existence": True,
    }
    write_json(output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["inspect", "marginals"])
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    (collect if args.mode == "inspect" else marginals)(args.output)
