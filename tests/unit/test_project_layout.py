import hashlib
import json
import zipfile

import pytest

from project_layout import historical_bytes, historical_sha256, legacy_name


@pytest.fixture
def archive(tmp_path):
    area = tmp_path / "tools/project_layout"
    area.mkdir(parents=True)
    source = b"original pinned source\n"
    live = tmp_path / "tools/showcase/runner.py"
    live.parent.mkdir(parents=True)
    live.write_bytes(b"source with relocated paths\n")
    path = area / "original_sources.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("showcase/runner.py", source)
        z.writestr("scripts/old_capture.py", source)
    sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
    catalog = {
        "archive_sha256": sha(path.read_bytes()),
        "entries": {
            "showcase/runner.py": {
                "original_sha256": sha(source),
                "current_path": "tools/showcase/runner.py",
                "current_sha256": sha(live.read_bytes()),
            },
            "scripts/old_capture.py": {
                "original_sha256": sha(source),
                "current_path": None,
                "current_sha256": None,
            },
        },
    }
    (area / "catalog.json").write_text(json.dumps(catalog))
    return tmp_path, live, path, source


def test_historical_pin_checks_the_relocated_current_file(archive):
    root, live, _, source = archive
    assert historical_bytes(root, "showcase/runner.py") == source
    assert historical_sha256(root, "tools/showcase/runner.py") == hashlib.sha256(source).hexdigest()
    live.write_bytes(b"unapproved scientific change")
    with pytest.raises(ValueError, match="Consolidated source changed"):
        historical_bytes(root, "showcase/runner.py")


def test_archive_corruption_and_retired_file_reappearance_fail_closed(archive):
    root, _, path, source = archive
    assert historical_bytes(root, "scripts/old_capture.py") == source
    restored = root / "scripts/old_capture.py"
    restored.parent.mkdir()
    restored.write_bytes(source)
    with pytest.raises(ValueError, match="unexpectedly restored"):
        historical_bytes(root, "scripts/old_capture.py")
    path.write_bytes(b"corrupt archive")
    with pytest.raises(ValueError, match="archive changed"):
        historical_bytes(root, "showcase/runner.py")


def test_unarchived_files_are_checked_directly_and_paths_cannot_escape(tmp_path):
    (tmp_path / "source.txt").write_bytes(b"actual bytes")
    assert historical_bytes(tmp_path, "source.txt") == b"actual bytes"
    assert legacy_name("tools/showcase_metrics/analysis.py") == "showcase_metrics/analysis.py"
    with pytest.raises(ValueError, match="repository-relative"):
        historical_bytes(tmp_path, "../outside.txt")
