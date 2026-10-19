"""Publish aggregate evidence and exact raw logs, excluding report-level inputs."""

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from faersight.audit import sha256, write_json


def export(source: Path, output: Path) -> dict:
    manifest = json.loads((source / "experiment_manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("status") != "computational_gates_passed"
        or manifest.get("scientific_findings_validated") is not False
        or not all(manifest.get("checks", {}).values())
    ):
        raise ValueError(
            "Only computationally complete, explicitly provisional runs can be exported"
        )
    for name, digest in manifest["artifacts"].items():
        path = (source / name).resolve()
        if not path.is_relative_to(source.resolve()) or sha256(path) != digest:
            raise ValueError(f"Experiment artifact changed: {name}")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Evidence snapshot exists; choose a new output directory")
    selected = {
        "experiment_manifest.json": "experiment_manifest.json",
        "arff_manifest.json": "input/manifest.json",
        "weka_manifest.json": "weka/manifest.json",
        **{
            name: "weka/" + name
            for name in [
                "java_version.log",
                "javac_version.log",
                "compile.log",
                "progress.log",
                "complete.txt",
                "weka_runs.csv",
                "weka_rules.csv",
            ]
        },
        **{
            p.name: str(p.relative_to(source))
            for p in sorted((source / "evaluation").iterdir())
            if p.suffix in {".csv", ".json"}
        },
    }
    for name in (
        "reproduction_check.json",
        "test_results.json",
        "reproduction_run_manifest.json",
        "reproduction_weka_manifest.json",
    ):
        if (source / name).is_file():
            selected[name] = name
    output.mkdir(parents=True, exist_ok=True)
    for target, origin in selected.items():
        shutil.copyfile(source / origin, output / target)
    logs = sorted((source / "weka/raw").rglob("*.log"))
    with zipfile.ZipFile(
        output / "weka_raw_logs.zip", "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for path in logs:
            name = path.relative_to(source / "weka").as_posix()
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    # Verify the published archive against the original experiment hash index.
    with zipfile.ZipFile(output / "weka_raw_logs.zip") as archive:
        import hashlib

        for name in archive.namelist():
            if (
                hashlib.sha256(archive.read(name)).hexdigest()
                != manifest["artifacts"]["weka/" + name]
            ):
                raise ValueError("Archived WEKA log checksum mismatch")
    index = {
        "status": "provisional_computational_evidence",
        "scientific_findings_validated": False,
        "source_git_commit": manifest["git_commit"],
        "raw_weka_logs": len(logs),
        "report_level_inputs_included": False,
        "artifacts": {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    write_json(output / "evidence_index.json", index)
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.source, args.output), indent=2))
