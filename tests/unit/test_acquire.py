import io
import json
import zipfile
from pathlib import Path

import pytest

from faersight.acquire import archive_inventory, download_archive, extract_required, official_url
from faersight.audit import sha256


def make_archive(path: Path, *, extra: str | None = None) -> bytes:
    with zipfile.ZipFile(path, "w") as archive:
        for name in ("DEMO", "DRUG", "REAC"):
            archive.writestr(f"ASCII/{name}25Q4.txt", f"{name} source\n")
        archive.writestr("Readme.pdf", b"retained documentation")
        archive.writestr("ASCII/OUTC25Q4.txt", b"out of scope")
        if extra:
            info = zipfile.ZipInfo("placeholder")
            info.filename = extra  # Avoid ZipInfo's platform-specific path normalization.
            archive.writestr(info, b"unsafe")
    return path.read_bytes()


def test_inventory_and_selective_extraction(tmp_path):
    archive = tmp_path / "source.zip"
    make_archive(archive)
    inventory = archive_inventory(archive, "2025Q4")
    assert inventory["archive_bytes"] == archive.stat().st_size
    assert set(inventory["tables"]) == {"DEMO", "DRUG", "REAC"}
    paths = extract_required(archive, "2025Q4", tmp_path / "extracted")
    assert paths["DEMO"].read_text() == "DEMO source\n"
    assert not (tmp_path / "extracted/ASCII/OUTC25Q4.txt").exists()
    manifest = json.loads((tmp_path / "extracted/extraction_manifest.json").read_text())
    assert manifest["archive_sha256"] == sha256(archive)
    assert manifest["files"]["Readme.pdf"]["sha256"]


@pytest.mark.parametrize("member", ["../escaped.txt", "/absolute", "C:/escaped", "bad\\path"])
def test_unsafe_member_rejected_before_extraction(tmp_path, member):
    archive = tmp_path / "source.zip"
    make_archive(archive, extra=member)
    with pytest.raises(ValueError, match="Unsafe"):
        extract_required(archive, "2025Q4", tmp_path / "extracted")
    assert not (tmp_path / "extracted").exists()


def test_wrong_quarter_rejected(tmp_path):
    archive = tmp_path / "source.zip"
    make_archive(archive)
    with pytest.raises(ValueError, match="DEMO"):
        archive_inventory(archive, "2025Q3")


@pytest.mark.parametrize(
    "url",
    [
        "http://fis.fda.gov/file.zip",
        "https://example.org/data.zip",
        "https://fis.fda.gov.evil.example/file.zip",
    ],
)
def test_nonofficial_source_rejected(url):
    with pytest.raises(ValueError, match="official FDA"):
        official_url(url)


def test_streamed_download_cache_and_checksum_enforcement(tmp_path, monkeypatch):
    data = make_archive(tmp_path / "origin.zip")
    url = "https://fis.fda.gov/content/Exports/source.zip"
    calls = []

    class Response(io.BytesIO):
        status = 200
        headers = {"Content-Type": "application/zip", "Content-Length": str(len(data))}

        def __init__(self):
            super().__init__(data)
            self.url = url

    def open_request(*args, **kwargs):
        calls.append(args)
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", open_request)
    target = tmp_path / "download.zip"
    first = download_archive(url, "2025Q4", target)
    cached = download_archive(url, "2025Q4", target, expected_sha256=sha256(target))
    assert first == cached and len(calls) == 1
    target.write_bytes(b"corrupt cache")
    with pytest.raises(ValueError, match="checksum"):
        download_archive(url, "2025Q4", target, expected_sha256=first["sha256"])


def test_unpinned_replacement_rejected(tmp_path, monkeypatch):
    make_archive(tmp_path / "origin.zip")
    url = "https://fis.fda.gov/content/Exports/source.zip"
    with pytest.raises(ValueError, match="provenance"):
        download_archive(url, "2025Q4", tmp_path / "origin.zip")
