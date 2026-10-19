"""Bounded-memory official-archive retrieval, inventory and selective extraction."""

import json
import re
import shutil
import time
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from faersight.audit import sha256, write_json

FDA_INDEX = "https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html"
CHUNK_BYTES = 1024 * 1024


def official_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"fis.fda.gov", "www.fda.gov"}:
        raise ValueError("Source must be an official FDA HTTPS URL")
    return url


def archive_inventory(path: Path, quarter: str) -> dict:
    """Read ZIP metadata without loading members or trusting their paths."""
    if not re.fullmatch(r"20\d{2}Q[1-4]", quarter):
        raise ValueError("quarter must be YYYYQ1..YYYYQ4")
    suffix = quarter[2:]  # 2025Q4 -> 25Q4
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise ValueError("Archive contains duplicate member names")
        tables = {}
        documents = []
        deletions = []
        for entry in entries:
            name = PurePosixPath(entry.filename)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in entry.orig_filename
                or ":" in entry.filename
            ):
                raise ValueError(f"Unsafe archive member: {entry.filename}")
            for table in ("DEMO", "DRUG", "REAC"):
                if name.name.upper() == f"{table}{suffix}.TXT":
                    if table in tables:
                        raise ValueError(f"Multiple {table} members in archive")
                    tables[table] = entry.filename
            if name.suffix.lower() in {".pdf", ".doc", ".docx", ".rtf"} or (
                "readme" in name.name.lower()
            ):
                documents.append(entry.filename)
            if name.name.upper() == f"DELETE{suffix}.TXT":
                deletions.append(entry.filename)
        if set(tables) != {"DEMO", "DRUG", "REAC"}:
            raise ValueError("Quarter archive must contain exactly one DEMO, DRUG and REAC file")
        if not documents:
            raise ValueError("Quarter archive has no retained source documentation")
        return {
            "quarter": quarter,
            "archive_bytes": path.stat().st_size,
            "uncompressed_bytes": sum(entry.file_size for entry in entries),
            "tables": tables,
            "documents": sorted(documents),
            "deletions": sorted(deletions),
            "members": [
                {
                    "name": e.filename,
                    "bytes": e.file_size,
                    "compressed_bytes": e.compress_size,
                    "crc32": f"{e.CRC:08x}",
                }
                for e in entries
                if not e.is_dir()
            ],
        }


def download_archive(
    url: str,
    quarter: str,
    destination: Path,
    *,
    expected_sha256: str | None = None,
    source_page: str = FDA_INDEX,
    retries: int = 3,
) -> dict:
    """Atomic, streaming download with content pinning on every reuse.

    HEAD Content-Length is unreliable on the FDA server; only a positive GET
    length is enforced. The computed checksum is provenance, not an FDA signature.
    """
    official_url(url)
    official_url(source_page)
    if expected_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("expected_sha256 must be a lowercase SHA-256 digest")
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = destination.with_suffix(".manifest.json")
    if destination.exists():
        digest = sha256(destination)
        if expected_sha256 is not None and digest != expected_sha256:
            raise ValueError(f"Cached archive checksum mismatch: {destination}")
        if not manifest_path.is_file():
            raise ValueError("Cached archive has no download provenance; refuse to invent it")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["sha256"] != digest or manifest["url"] != url or manifest["quarter"] != quarter:
            raise ValueError("Cached source does not match its provenance")
        archive_inventory(destination, quarter)
        return manifest
    partial = destination.with_suffix(destination.suffix + ".part")
    response_metadata = {}
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "FAERSight/0.1 research"})
            with urllib.request.urlopen(request, timeout=120) as response:
                official_url(response.url)
                response_metadata = {
                    "final_url": response.url,
                    "http_status": response.status,
                    "headers": {
                        key: response.headers.get(key)
                        for key in ("Content-Type", "Content-Length", "Last-Modified", "ETag")
                    },
                }
                with partial.open("wb") as stream:
                    shutil.copyfileobj(response, stream, CHUNK_BYTES)
            stated = int(response_metadata["headers"].get("Content-Length") or 0)
            if stated > 0 and stated != partial.stat().st_size:
                raise OSError("Incomplete FDA archive transfer")
            break
        except (OSError, urllib.error.URLError):
            if attempt + 1 == retries:
                raise
            time.sleep(min(2**attempt, 4))
    inventory = archive_inventory(partial, quarter)
    digest = sha256(partial)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("Downloaded FDA archive differs from the frozen checksum")
    partial.replace(destination)
    manifest = {
        "schema_version": 1,
        "dataset": "FDA FAERS/AEMS quarterly ASCII",
        "url": url,
        "source_page": source_page,
        "quarter": quarter,
        "retrieved_utc": datetime.now(UTC).isoformat(),
        "sha256": digest,
        **response_metadata,
        "inventory": inventory,
    }
    write_json(manifest_path, manifest)
    return manifest


def extract_required(archive_path: Path, quarter: str, directory: Path) -> dict:
    """Stream only required relations and source docs; CRC is verified by ZipFile."""
    inventory = archive_inventory(archive_path, quarter)
    directory.mkdir(parents=True, exist_ok=True)
    selected = sorted(
        set(inventory["tables"].values())
        | set(inventory["documents"])
        | set(inventory["deletions"])
    )
    files = {}
    with zipfile.ZipFile(archive_path) as archive:
        for name in selected:
            target = directory / PurePosixPath(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_suffix(target.suffix + ".part")
            with archive.open(name) as source, partial.open("wb") as destination:
                shutil.copyfileobj(source, destination, CHUNK_BYTES)
            partial.replace(target)
            files[name] = {
                "path": str(target),
                "sha256": sha256(target),
                "bytes": target.stat().st_size,
            }
    write_json(
        directory / "extraction_manifest.json",
        {
            "archive_sha256": sha256(archive_path),
            "quarter": quarter,
            "files": files,
        },
    )
    result = {table: Path(files[name]["path"]) for table, name in inventory["tables"].items()}
    if len(inventory["deletions"]) > 1:
        raise ValueError("Multiple deleted-case lists in archive")
    if inventory["deletions"]:
        result["DELETE"] = Path(files[inventory["deletions"][0]]["path"])
    return result
