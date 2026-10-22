"""Record the single authorized 0.001 invocation without changing its runner/config."""

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
from showcase.runner import code_hashes, config_checked, verify_core  # noqa: E402

COMMAND = [
    ".venv/Scripts/python",
    "-m",
    "showcase.runner",
    "run",
    "--execution-manifest",
    "artifacts/manifests/weka-showcase-step2a/locked/execution_manifest.json",
    "--support",
    "0.001",
    "--output",
    "artifacts/generated/weka-showcase/full/0.001",
    "--authorize-full-data",
]


def record() -> dict:
    folder = ROOT / "artifacts/generated/weka-showcase/step2b-0.001-capture"
    output = ROOT / "artifacts/generated/weka-showcase/full/0.001"
    if folder.exists() or output.exists():
        raise ValueError("A recorded attempt already exists; do not rerun/tune")
    config, java, _ = config_checked()
    execution = ROOT / COMMAND[5]
    manifest = json.loads(execution.read_text())
    if manifest["source_hashes"] != code_hashes():
        raise ValueError("Source differs from locked Step 2A manifest")
    if sha256(ROOT / config["input"]["path"]) != config["input"]["sha256"]:
        raise ValueError("Frozen primary input hash changed")
    git = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
    parent = subprocess.run(
        [*git, "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    original = subprocess.run(
        [*git, "show", "78dd8de:" + COMMAND[5]], cwd=ROOT, capture_output=True, check=True
    ).stdout
    if original != execution.read_bytes():
        raise ValueError("Execution manifest differs from authorized commit 78dd8de")
    core = verify_core()
    folder.mkdir(parents=True)
    for name, command in [
        ("java_version.txt", [str(java), "-version"]),
        ("javac_version.txt", [str(java.with_name("javac.exe")), "-version"]),
    ]:
        result = subprocess.run(command, capture_output=True, timeout=30, check=True)
        (folder / name).write_bytes(result.stdout + result.stderr)
    result = {
        "status": "running",
        "authorized_support_only": "0.001",
        "authorized_command": " ".join(COMMAND),
        "argv": COMMAND,
        "cwd": str(ROOT),
        "started_utc": datetime.now(UTC).isoformat(),
        "execution_manifest_sha256": sha256(execution),
        "locked_implementation_commit": manifest["code_commit"],
        "launch_git_commit": parent,
        "capture_script_sha256": sha256(Path(__file__)),
        "input": config["input"],
        "runtime": config["runtime"],
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "core_before": core,
        "scientific_findings_validated": False,
        "lower_supports_authorized": False,
        "later_steps_authorized": False,
    }
    write_json(folder / "command_record.json", result)
    started = time.perf_counter()
    with (folder / "runner_stdout_stderr.txt").open("wb") as stream:
        completed = subprocess.run(COMMAND, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    result["total_command_wall_seconds"] = time.perf_counter() - started
    result["exit_code"] = completed.returncode
    result["finished_utc"] = datetime.now(UTC).isoformat()
    invocation = output / "invocation.json"
    result["runner_status"] = (
        json.loads(invocation.read_text())["status"] if invocation.exists() else None
    )
    result["status"] = (
        "passed" if completed.returncode == 0 and result["runner_status"] == "passed" else "stopped"
    )
    result["core_after"] = verify_core()
    result["locked_sources_still_match"] = manifest["source_hashes"] == code_hashes()
    result["raw_output_hashes"] = {
        p.relative_to(output).as_posix(): sha256(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    result["capture_hashes"] = {
        p.name: sha256(p)
        for p in sorted(folder.iterdir())
        if p.is_file() and p.name != "command_record.json"
    }
    write_json(folder / "command_record.json", result)
    return result


if __name__ == "__main__":
    result = record()
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k in {"status", "exit_code", "runner_status", "total_command_wall_seconds"}
            },
            indent=2,
        )
    )
