"""Verify the cleanup ledger, immutable evidence, archived source pins and README links."""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from project_layout import historical_sha256  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_links(path):
    """Check local Markdown destinations, including anchors in linked documents."""
    links = re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))
    checked = 0
    for link in links:
        if link.startswith(("https:", "http:", "mailto:")):
            continue
        checked += 1
        name, _, anchor = link.partition("#")
        target = path.parent / name if name else path
        if not target.exists():
            raise ValueError(f"Missing link in {path.relative_to(ROOT)}: {link}")
        if anchor and target.suffix == ".md":
            headings = re.findall(r"^#{1,6} (.+)$", target.read_text(encoding="utf-8"), re.M)
            anchors = {re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-") for h in headings}
            if anchor not in anchors:
                raise ValueError(f"Missing heading in {path.relative_to(ROOT)}: {link}")
    return len(links), checked


def verify():
    inventory = json.loads((ROOT / "docs/repository_inventory.json").read_text())
    catalog = json.loads((ROOT / "tools/project_layout/catalog.json").read_text())
    counts = dict.fromkeys(("KEEP", "CONSOLIDATE", "REMOVE"), 0)
    for item in inventory["files"]:
        name = item["path"]
        counts[item["classification"]] += 1
        if name in catalog["entries"]:
            if historical_sha256(ROOT, name) != item["sha256"]:
                raise ValueError("Historical source pin mismatch: " + name)
        elif digest(ROOT / name) != item["sha256"]:
            raise ValueError("Retained file changed: " + name)
    # All original snapshots, including internal relative-path evidence indexes,
    # are byte-identical to the inventoried baseline. Validate every archive entry,
    # not just those reached by a particular historical auditor.
    for name, entry in catalog["entries"].items():
        if historical_sha256(ROOT, name) != entry["original_sha256"]:
            raise ValueError("Archived source pin mismatch: " + name)
    readme_links, _ = verify_links(ROOT / "README.md")
    markdown = [
        ROOT / "README.md",
        ROOT / "PRD.md",
        *(ROOT / "docs").rglob("*.md"),
        *(ROOT / "tools").rglob("*.md"),
    ]
    local_links = sum(verify_links(path)[1] for path in markdown)
    for directory in ("src/faersight", "config", "mappings", "benchmarks", "artifacts/manifests"):
        if any(
            item["classification"] != "KEEP"
            for item in inventory["files"]
            if item["path"].startswith(directory + "/")
        ):
            raise ValueError("Scientific tree was not retained: " + directory)
    return {
        "status": "passed",
        "baseline_commit": inventory["baseline_commit"],
        "baseline_files": len(inventory["files"]),
        "classifications": counts,
        "archived_source_pins": len(catalog["entries"]),
        "README_links": readme_links,
        "local_documentation_links": local_links,
        "scientific_behavior_or_result_changes": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
