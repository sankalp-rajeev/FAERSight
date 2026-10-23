"""Pinned metric API probe, not association mining."""

import csv
import io
import math
import os
import subprocess
from pathlib import Path

from faersight.audit import sha256
from showcase.inspect import ROOT, pinned_runtime
from showcase.runner import single_jvm
from showcase_metrics.analysis import VALUES, parse_metric, recompute, write_json


def run_probe(output: Path):
    output.mkdir(parents=True, exist_ok=False)
    _, java, cp = pinned_runtime()
    source = ROOT / "showcase_metrics/java/MetricProbe.java"
    classes = output / "classes"
    classes.mkdir()
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
        "faersight.metricstudy.MetricProbe",
    ]
    with single_jvm():
        compiled = subprocess.run(compile_cmd, capture_output=True, timeout=120, check=True)
        result = subprocess.run(command, capture_output=True, timeout=30, check=True)
    (output / "compile.txt").write_bytes(compiled.stdout + compiled.stderr)
    (output / "stdout.csv").write_bytes(result.stdout)
    (output / "stderr.txt").write_bytes(result.stderr)
    rows = []
    for raw in csv.DictReader(io.StringIO(result.stdout.decode())):
        n, lhs, rhs, joint = (int(raw[k]) for k in ("n", "lhs", "rhs", "joint"))
        expected = recompute(joint, lhs, rhs, n)
        parsed = {m: parse_metric(raw[m], m) for m in VALUES if m != "support"}
        for metric, value in parsed.items():
            if not math.isclose(value, expected[metric], rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("Native metric probe discrepancy")
        if float(raw["apriori_conviction"]) != parsed["conviction"]:
            raise ValueError("Apriori and general-rule conviction differ")
        rows.append(
            {
                "counts": {"n": n, "lhs": lhs, "rhs": rhs, "joint": joint},
                "raw_WEKA": raw,
                "parsed": parsed,
                "independent": expected,
                "confidence_one": parsed["confidence"] == 1.0,
                "ranking_treatment": "unchanged finite API value, descending; exact ties averaged",
            }
        )
    report = {
        "status": "passed",
        "weka_version": "3.8.6",
        "association_builds": 0,
        "formula": "(lhs*(N-rhs)/N)/(lhs-joint+1)",
        "cases": rows,
        "compile_command": compile_cmd,
        "command": command,
        "exit_code": result.returncode,
        "source_sha256": sha256(source),
    }
    write_json(output / "probe.json", report)
    return report
