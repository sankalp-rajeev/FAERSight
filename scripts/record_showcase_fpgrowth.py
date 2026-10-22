"""Capture exactly one separately locked FPGrowth 0.001 invocation."""

import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faersight.audit import sha256, write_json  # noqa: E402
from showcase.inspect import pinned_runtime  # noqa: E402
from showcase.runner import verify_core  # noqa: E402
from showcase_fpgrowth.runner import LOCK, git, verify_locked_apriori  # noqa: E402

COMMAND = [
    ".venv/Scripts/python",
    "-m",
    "showcase_fpgrowth.runner",
    "run",
    "--execution-manifest",
    "artifacts/manifests/weka-showcase-fpgrowth/locked/execution_manifest.json",
    "--authorize-full-data",
]


def record():
    output = ROOT / "artifacts/generated/weka-showcase-fpgrowth/full/0.001"
    capture = ROOT / "artifacts/generated/weka-showcase-fpgrowth/capture-0.001"
    if output.exists() or capture.exists():
        raise ValueError("Attempt already exists; no retry authorized")
    config, java, _ = pinned_runtime()
    verify_locked_apriori()
    manifest = json.loads(LOCK.read_text())
    core = verify_core()
    capture.mkdir(parents=True)
    for label, cmd in [
        ("java", [str(java), "-version"]),
        ("javac", [str(java.with_name("javac.exe")), "-version"]),
    ]:
        result = subprocess.run(cmd, capture_output=True, timeout=30, check=True)
        (capture / (label + "_version.txt")).write_bytes(result.stdout + result.stderr)
    result = {
        "status": "running",
        "argv": COMMAND,
        "command": subprocess.list2cmdline(COMMAND),
        "cwd": str(ROOT),
        "launch_commit": git("rev-parse", "HEAD"),
        "implementation_commit": manifest["code_commit"],
        "amendment_commit": "23a3a34",
        "execution_manifest_sha256": sha256(LOCK),
        "runtime": config["runtime"],
        "input": manifest["input"],
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "core_before": core,
        "started_utc": datetime.now(UTC).isoformat(),
        "scientific_findings_validated": False,
    }
    write_json(capture / "command_record.json", result)
    start = time.perf_counter()
    with (
        (capture / "runner_stdout.txt").open("wb") as stdout,
        (capture / "runner_stderr.txt").open("wb") as stderr,
    ):
        completed = subprocess.run(COMMAND, cwd=ROOT, stdout=stdout, stderr=stderr)
    result["total_command_wall_seconds"] = time.perf_counter() - start
    result["cli_exit_code"] = completed.returncode
    result["finished_utc"] = datetime.now(UTC).isoformat()
    invocation = output / "invocation.json"
    result["invocation_status"] = (
        json.loads(invocation.read_text()) if invocation.exists() else None
    )
    result["status"] = (
        "passed"
        if completed.returncode == 0
        and (result["invocation_status"] and result["invocation_status"]["status"] == "passed")
        else "stopped"
    )
    result["core_after"] = verify_core()
    verify_locked_apriori()
    result["raw_output_hashes"] = {
        p.relative_to(output).as_posix(): sha256(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    result["capture_hashes"] = {
        p.name: sha256(p)
        for p in sorted(capture.iterdir())
        if p.is_file() and p.name != "command_record.json"
    }
    write_json(capture / "command_record.json", result)
    print(
        json.dumps(
            {k: result[k] for k in ("status", "cli_exit_code", "total_command_wall_seconds")}
        )
    )


if __name__ == "__main__":
    record()
