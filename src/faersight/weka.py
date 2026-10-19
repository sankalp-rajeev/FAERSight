"""Run the mandatory WEKA tool and validate presence-only single-pair rules."""

import csv
import math
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from faersight.audit import sha256, write_json

WEKA_VERSION = "3.8.6"


@dataclass(frozen=True)
class Rule:
    weka_rank: int
    drug: str
    reaction: str
    antecedent_count: int
    joint_count: int
    weka_confidence: float
    weka_lift: float


def find_java(explicit: str | None = None) -> str:
    if explicit:
        if Path(explicit).is_file():
            return str(Path(explicit).resolve())
        found = shutil.which(explicit)
        if found:
            return found
        raise ValueError(f"Java executable not found: {explicit}")
    candidates = [os.environ.get("JAVA_HOME", "")]
    for root in candidates:
        if root:
            path = Path(root) / "bin" / ("java.exe" if os.name == "nt" else "java")
            if path.is_file():
                return str(path)
    found = shutil.which("java")
    if found:
        return found
    bundled = Path("C:/Program Files/Android/Android Studio/jbr/bin/java.exe")
    if os.name == "nt" and bundled.is_file():
        return str(bundled)
    raise ValueError("Java not found. Set JAVA_HOME or pass --java PATH.")


def parse_rules(output: str) -> list[Rule]:
    """Keep exactly DRUG=1 -> REAC=1; reject zero-valued mined rules globally."""
    rules = []
    line_pattern = re.compile(r"^\s*(\d+)\.\s+(.*?)\s+(\d+)\s+==>\s+(.*?)\s+(\d+)\s+(.*)$")
    for line in output.splitlines():
        match = line_pattern.match(line)
        if not match:
            if re.match(r"^\s*\d+\.\s+.*==>", line):
                raise ValueError(f"Unrecognized WEKA rule format: {line}")
            continue
        rank, lhs, antecedent, rhs, joint, scores = match.groups()
        if re.search(r"=0(?:\s|$)", lhs + " " + rhs):
            raise ValueError("WEKA mined an absence rule; check nominal ordering and -Z")
        left = re.fullmatch(r"DRUG_(.+)=1", lhs)
        right = re.fullmatch(r"REAC_(.+)=1", rhs)
        if not left or not right or re.search(r"=1\s", lhs) or re.search(r"=1\s", rhs):
            continue
        confidence = re.search(r"conf:\(([^)]+)\)", scores)
        lift = re.search(r"lift:\(([^)]+)\)", scores)
        if not confidence or not lift:
            raise ValueError("WEKA rule is missing confidence or lift")
        rules.append(
            Rule(
                int(rank),
                left[1],
                right[1],
                int(antecedent),
                int(joint),
                float(confidence[1]),
                float(lift[1]),
            )
        )
    return rules


def write_csv(path: Path, rows: list[dict], *, fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and fieldnames is None:
        raise ValueError("Empty CSV requires explicit fieldnames")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_smoke(arff: Path, output_dir: Path, *, jar: Path, java: str | None = None) -> list[Rule]:
    """Persist raw logs and actual settings; fail if known toy metrics disagree."""
    java_path = find_java(java)
    if not jar.is_file():
        raise ValueError(f"WEKA_JAR does not exist: {jar}")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Include Maven runtime dependencies located next to the WEKA jar (e.g. bounce).
    classpath = str(jar.resolve()) + os.pathsep + str(jar.resolve().parent / "*")

    def invoke(args: list[str], log: str) -> str:
        result = subprocess.run(
            [java_path, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        (output_dir / log).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise ValueError(f"Java/WEKA command failed; inspect {output_dir / log}")
        return result.stdout

    started = datetime.now(UTC).isoformat()
    invoke(["-version"], "java_version.log")
    version = invoke(["-cp", classpath, "weka.core.Version"], "weka_version.log")
    actual_version = version.splitlines()[0].strip() if version.splitlines() else "(empty output)"
    if actual_version != WEKA_VERSION:
        raise ValueError(f"Expected WEKA {WEKA_VERSION}; got {actual_version}")
    validation = invoke(
        ["-cp", classpath, "weka.core.Instances", str(arff.resolve())], "arff_validation.log"
    )
    instances = re.search(r"Num Instances:\s+(\d+)", validation)
    if instances is None or int(instances[1]) != 10:
        raise ValueError("WEKA must retain all 10 toy cases, including empty background baskets")
    options = [
        "-t",
        str(arff.resolve()),
        "-N",
        "100",
        "-T",
        "1",
        "-C",
        "1.0",
        "-D",
        "0.05",
        "-U",
        "1.0",
        "-M",
        "0.1",
        "-Z",
    ]
    output = invoke(["-cp", classpath, "weka.associations.Apriori", *options], "apriori.log")
    rules = parse_rules(output)
    known = next(
        (rule for rule in rules if rule.drug == "alpha" and rule.reaction == "REACTION X"), None
    )
    if (
        known is None
        or known.antecedent_count != 4
        or known.joint_count != 3
        or not math.isclose(known.weka_confidence, 0.75, abs_tol=0.0051)
        or not math.isclose(known.weka_lift, 1.875, abs_tol=0.0051)
    ):
        raise ValueError("WEKA toy presence rule or independently expected metrics disagree")
    write_csv(output_dir / "rules.csv", [asdict(rule) for rule in rules])
    write_json(
        output_dir / "manifest.json",
        {
            "dataset": "synthetic_only",
            "weka_version": WEKA_VERSION,
            "java_executable": java_path,
            "arff_sha256": sha256(arff),
            "weka_jar_sha256": sha256(jar),
            "runtime_jars": {path.name: sha256(path) for path in sorted(jar.parent.glob("*.jar"))},
            "eligible_n": int(instances[1]),
            "options": options,
            "started_utc": started,
            "finished_utc": datetime.now(UTC).isoformat(),
            "accepted_rules": len(rules),
            "apriori_log_sha256": sha256(output_dir / "apriori.log"),
            "rules_sha256": sha256(output_dir / "rules.csv"),
        },
    )
    return rules
