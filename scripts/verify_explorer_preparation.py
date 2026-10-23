"""Audit prepared Explorer material; never label API observations as GUI evidence."""

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faersight.audit import sha256, write_json  # noqa: E402
from showcase.runner import verify_core  # noqa: E402
from showcase_explorer.prepare import EVIDENCE, frozen_selection  # noqa: E402
from showcase_fpgrowth.runner import git  # noqa: E402
from showcase_metrics.runner import mining_inventory  # noqa: E402
from showcase_metrics.runtime import PORTABILITY_FILES  # noqa: E402


def verify(*, record=False):
    manifest = json.loads((EVIDENCE / "preparation_manifest.json").read_text())
    for name, digest in manifest["protected_prior_files"].items():
        if name in PORTABILITY_FILES:
            # Keep old execution provenance exact, without imposing its host path
            # on the separately amended portable code/configuration.
            archived = git("show", manifest["code_commit"] + ":" + name, binary=True)
            assert hashlib.sha256(archived).hexdigest() == digest, name
        else:
            assert sha256(ROOT / name) == digest, name
    for name, digest in manifest["source_hashes"].items():
        assert sha256(ROOT / name) == digest, name
        assert (
            hashlib.sha256(
                git("show", manifest["code_commit"] + ":" + name, binary=True)
            ).hexdigest()
            == digest
        ), name
    assert mining_inventory() == manifest["full_data_mining_invocations_before"]
    assert manifest["status"] == "prepared_pending_GUI_connection"
    assert manifest["screenshots"] == [] and manifest["GUI_load_time_seconds"] is None
    assert manifest["GUI_dimensions"] is None and manifest["fallback_required"] is None
    assert manifest["fallback_10k_generated"] is False and manifest["new_association_builds"] == 0
    selected = frozen_selection()
    assert selected["rule"] == manifest["primary_selection"]["rule"]
    projection = json.loads((EVIDENCE / "projection_manifest.json").read_text())
    assert sha256(ROOT / projection["source"]) == projection["source_sha256"]
    assert sha256(ROOT / projection["output"]) == projection["sha256"]
    assert (projection["rows"], projection["attributes"], projection["empty_reports"]) == (
        385288,
        8,
        382855,
    )
    for reference in manifest["frozen_result_provenance"]:
        archive = ROOT / reference["source"]
        assert sha256(archive) == reference["source_sha256"]
        if "2025Q4-statins-mining" in reference["source"]:
            dest = EVIDENCE / "frozen_primary_projected_result.log"
        else:
            algorithm = reference["archive_member"].split("/")[0]
            dest = EVIDENCE / f"frozen_A1_{algorithm}_result.log"
        with zipfile.ZipFile(archive) as zipped:
            assert zipped.read(reference["archive_member"]) == dest.read_bytes()
    core = verify_core()
    generated = {}
    for directory, record_path in [
        (
            "artifacts/generated/2025Q4-statins-mining",
            "artifacts/generated/2025Q4-statins-mining/experiment_manifest.json",
        ),
        (
            "artifacts/generated/2025Q4-statins-sensitivity",
            "artifacts/manifests/2025Q4-statins-sensitivity/sensitivity_manifest.json",
        ),
    ]:
        source = json.loads((ROOT / record_path).read_text())
        assert source["scientific_findings_validated"] is False
        for name, digest in source["artifacts"].items():
            assert sha256(ROOT / directory / name) == digest, name
        generated[directory] = len(source["artifacts"])
    suites = ET.parse(EVIDENCE / "test_results.xml").getroot()
    suites = list(suites) if suites.tag == "testsuites" else [suites]
    tests = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")
    }
    assert tests == {"tests": 180, "failures": 0, "errors": 0, "skipped": 0}
    commands = [
        [str(ROOT / ".venv/Scripts/ruff.exe"), "check", "."],
        [
            str(ROOT / ".venv/Scripts/ruff.exe"),
            "format",
            "--check",
            "src",
            "tests",
            "showcase",
            "showcase_fpgrowth",
            "showcase_fallback_a1",
            "showcase_fallback_a2",
            "showcase_fallback_a3",
            "showcase_metrics",
            "showcase_explorer",
            "scripts/verify_explorer_preparation.py",
            "scripts/verify_showcase_metrics.py",
            "scripts/record_showcase_step2b.py",
            "scripts/export_showcase_step2b.py",
            "scripts/record_showcase_fpgrowth.py",
            "scripts/export_showcase_fpgrowth.py",
        ],
        [str(ROOT / ".venv/Scripts/python.exe"), "scripts/verify_showcase_metrics.py"],
    ]
    results = []
    for command in commands:
        r = subprocess.run(command, capture_output=True, timeout=120, check=True)
        results.append(
            {
                "command": command,
                "exit_code": r.returncode,
                "stdout": r.stdout.decode(),
                "stderr": r.stderr.decode(),
            }
        )
    index_path = EVIDENCE / "evidence_index.json"
    index = json.loads(index_path.read_text())
    for name, digest in index["artifacts"].items():
        assert sha256(EVIDENCE / name) == digest, name
    report = {
        "status": "preparation_validation_passed_GUI_pending",
        "tests": tests,
        "frozen_core": core,
        "protected_prior_files": len(manifest["protected_prior_files"]),
        "frozen_generated_artifacts": generated,
        "commands": results,
        "projection_counts_and_provenance_verified": True,
        "GUI_verified": False,
        "screenshots_verified": 0,
        "new_mining_experiments": 0,
        "verification_source_sha256": sha256(Path(__file__)),
        "scientific_findings_validated": False,
    }
    if record:
        write_json(EVIDENCE / "validation.json", report)
        write_json(
            index_path,
            {
                "artifacts": {
                    p.relative_to(EVIDENCE).as_posix(): sha256(p)
                    for p in sorted(EVIDENCE.rglob("*"))
                    if p.is_file() and p != index_path
                },
                "scientific_findings_validated": False,
            },
        )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(record=args.record), indent=2))
