"""Verify historical source pins after a byte-recorded repository consolidation.

This is for historical audits only. New execution locks still hash current code.
Scientific inputs, configs and result artifacts are never redirected to the archive.
"""

import hashlib
import json
import zipfile
from pathlib import Path


def legacy_name(name: str) -> str:
    """Translate a tooling source path to its original manifest key."""
    parts = Path(name).parts
    if len(parts) > 1 and parts[0] == "tools" and parts[1].startswith("showcase"):
        return Path(*parts[1:]).as_posix()
    return Path(name).as_posix()


def historical_bytes(root: Path, name: str) -> bytes:
    """Read exact old bytes, checking both the archive and any current replacement."""
    root = Path(root).resolve()
    name = legacy_name(name)
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Historical source must be a repository-relative path")
    area = root / "tools/project_layout"
    catalog_path = area / "catalog.json"
    if not catalog_path.exists():
        return (root / relative).read_bytes()
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entry = catalog["entries"].get(name)
    if entry is None:
        return (root / relative).read_bytes()
    archive = area / "original_sources.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != catalog["archive_sha256"]:
        raise ValueError("Historical source archive changed")
    with zipfile.ZipFile(archive) as source:
        original = source.read(name)
    if hashlib.sha256(original).hexdigest() != entry["original_sha256"]:
        raise ValueError("Archived source changed: " + name)
    if entry["current_path"] is not None:
        current = root / entry["current_path"]
        if not current.resolve().is_relative_to(root):
            raise ValueError("Consolidated source escapes repository")
        if hashlib.sha256(current.read_bytes()).hexdigest() != entry["current_sha256"]:
            raise ValueError("Consolidated source changed: " + entry["current_path"])
    elif (root / relative).exists():
        raise ValueError("Retired source unexpectedly restored in active tree: " + name)
    return original


def historical_sha256(root: Path, name: str) -> str:
    """Digest historical bytes without weakening checks of the current replacement."""
    return hashlib.sha256(historical_bytes(root, name)).hexdigest()
