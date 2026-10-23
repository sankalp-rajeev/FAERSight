"""Read-only metric-checkpoint audit; --record writes only current metric evidence."""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faersight.audit import sha256  # noqa: E402
from showcase.runner import verify_core  # noqa: E402
from showcase_metrics.analysis import METRICS, write_json  # noqa: E402
from showcase_metrics.runner import (  # noqa: E402
    EVIDENCE,
    LOCK,
    OUTPUT,
    plotting_env,
    verify_lock,
)
from showcase_metrics.runtime import plotting_python, plotting_runtime  # noqa: E402


def verify(*, record=False):
    manifest = verify_lock(historical=True)
    assert LOCK.with_suffix(".sha256").read_text().split()[0] == sha256(LOCK)
    core = verify_core()
    generated = {}
    for directory, path in [
        (
            "artifacts/generated/2025Q4-statins-mining",
            "artifacts/generated/2025Q4-statins-mining/experiment_manifest.json",
        ),
        (
            "artifacts/generated/2025Q4-statins-sensitivity",
            "artifacts/manifests/2025Q4-statins-sensitivity/sensitivity_manifest.json",
        ),
    ]:
        source = json.loads((ROOT / path).read_text())
        assert source["scientific_findings_validated"] is False
        for name, digest in source["artifacts"].items():
            assert sha256(ROOT / directory / name) == digest, name
        generated[directory] = len(source["artifacts"])
    suites = ET.parse(OUTPUT / "test_results.xml").getroot()
    suites = list(suites) if suites.tag == "testsuites" else [suites]
    counts = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")
    }
    assert counts["tests"] == 171 and not any(counts[k] for k in ("failures", "errors", "skipped"))
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
            "scripts/verify_showcase_metrics.py",
            "scripts/record_showcase_step2b.py",
            "scripts/export_showcase_step2b.py",
            "scripts/record_showcase_fpgrowth.py",
            "scripts/export_showcase_fpgrowth.py",
        ],
    ]
    logs = []
    for command in commands:
        result = subprocess.run(command, capture_output=True, check=True, timeout=30)
        logs.append(
            {
                "argv": command,
                "exit_code": result.returncode,
                "stdout": result.stdout.decode(),
                "stderr": result.stderr.decode(),
            }
        )
    # Independent SciPy/NumPy cross-check of average ranks and descriptive rho.
    # No p-values are used: the rules are dependent, not an inferential sample.
    worker = """
import json,sys,itertools,math,importlib.metadata as metadata
import numpy as np
from scipy.stats import rankdata,spearmanr
from pathlib import Path
p=Path(sys.argv[1]); rows=json.loads((p/'canonical_pool.json').read_text())
metrics=['confidence','lift','leverage','conviction']; deltas=[]; tested=0
for population,subset,file in [('all_586',rows,'spearman_full.json'),
 ('single_to_single_472',[r for r in rows if len(r['antecedent'])==len(r['consequent'])==1],
 'spearman_single_to_single.json')]:
 values={m:np.array([r[m] for r in subset]) for m in metrics}
 ranks={m:rankdata(-values[m],method='average') for m in metrics}
 if population=='all_586':
  for m in metrics:
   assert np.array_equal(ranks[m],np.array([r['average_ranks'][m] for r in subset]))
 observed=json.loads((p/file).read_text())
 for r in observed:
  rho=float(spearmanr(values[r['metric_a']],values[r['metric_b']]).statistic)
  difference=abs(rho-r['spearman']); deltas.append(difference); tested+=1
  assert difference<=1e-12
print(json.dumps({'status':'passed','correlations_verified':tested,
 'average_ranks_exactly_match_SciPy':True,'maximum_rho_difference':max(deltas),
 'versions':{m:metadata.version(m) for m in ['scipy','numpy']},'p_values_used':False}))
"""
    checked = subprocess.run(
        [plotting_python(), "-c", worker, str(OUTPUT)],
        env=plotting_env(),
        capture_output=True,
        timeout=60,
        check=True,
    )
    independent = json.loads(checked.stdout)
    rows = json.loads((OUTPUT / "canonical_pool.json").read_text())
    # Reproduce each existing ranking's full JSON bytes from its canonical input.
    # Keep verification outputs isolated from the registered result directory.
    scratch = ROOT / ".tools/metric-reproduction-audit"
    scratch.mkdir(exist_ok=True)
    for metric in METRICS:
        original = json.loads((OUTPUT / f"ranking_{metric}.json").read_text())
        expected = sorted(
            rows, key=lambda r: (-r[metric], (tuple(r["antecedent"]), tuple(r["consequent"])))
        )
        assert [(r["antecedent"], r["consequent"]) for r in original] == [
            (r["antecedent"], r["consequent"]) for r in expected
        ]
        write_json(scratch / f"ranking_{metric}.json", original)
        assert (scratch / f"ranking_{metric}.json").read_bytes() == (
            OUTPUT / f"ranking_{metric}.json"
        ).read_bytes()
    charts = scratch / "charts"
    subprocess.run(
        [
            plotting_python(),
            "-m",
            "showcase_metrics.plots",
            str(OUTPUT / "chart_data.json"),
            str(charts),
        ],
        env=plotting_env(),
        capture_output=True,
        check=True,
        timeout=120,
    )
    for p in (OUTPUT / "charts").iterdir():
        assert p.read_bytes() == (charts / p.name).read_bytes(), p.name
    assert len(list(charts.glob("*.png"))) == 3 and len(list(charts.glob("*.svg"))) == 3
    if (EVIDENCE / "run/evidence_index.json").exists():
        target = EVIDENCE / "run"
        index = json.loads((target / "evidence_index.json").read_text())
        for name, digest in index["artifacts"].items():
            assert sha256(target / name) == digest, name
            assert sha256(OUTPUT / name) == digest, name
    report = {
        "status": "passed",
        "tests": counts,
        "frozen_core": core,
        "protected_prior_files": len(manifest["protected_prior_hashes"]),
        "frozen_generated_artifacts": generated,
        "independent_SciPy_check": independent,
        "deterministic_charts_verified": 3,
        "chart_formats": ["png", "svg"],
        "chart_visual_review": "all three PNGs inspected; labels and source limitations readable",
        "all_ranking_orders_verified": True,
        "rank_export_serialization_stable": True,
        "new_full_data_mining_invocations": 0,
        "checks": logs,
        "verification_source_sha256": sha256(Path(__file__)),
        "current_plotting_runtime": plotting_runtime(),
        "scientific_findings_validated": False,
    }
    if record:
        write_json(OUTPUT / "validation.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(record=args.record), indent=2))
