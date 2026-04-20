"""Test Home Assistant file utility functions."""

import os
from pathlib import Path
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.util.file import WriteError, write_utf8_file, write_utf8_file_atomic

from tests.hass_fixtures import LogCapture, caplog, tmp_path


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported fixtures resolve via Depends()."""
    return 0


@test.cases(
    test.case("write_utf8_file", func=write_utf8_file),
    test.case("write_utf8_file_atomic", func=write_utf8_file_atomic),
)
def write_utf8_file_atomic_private(
    func: object,
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test files can be written as 0o600 or 0o644."""
    test_dir = tmp_path / "files"
    test_dir.mkdir()
    test_file = test_dir / "test.json"

    func(test_file, '{"some":"data"}', False)
    with open(test_file, encoding="utf8") as fh:
        expect(fh.read()).to_equal('{"some":"data"}')
    expect(os.stat(test_file).st_mode & 0o777).to_equal(0o644)

    func(test_file, '{"some":"data"}', True)
    with open(test_file, encoding="utf8") as fh:
        expect(fh.read()).to_equal('{"some":"data"}')
    expect(os.stat(test_file).st_mode & 0o777).to_equal(0o600)

    func(test_file, b'{"some":"data"}', True, mode="wb")
    with open(test_file, encoding="utf8") as fh:
        expect(fh.read()).to_equal('{"some":"data"}')
    expect(os.stat(test_file).st_mode & 0o777).to_equal(0o600)


@test
def write_utf8_file_fails_at_creation(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test that failed creation of the temp file does not create an empty file."""
    test_dir = tmp_path / "files"
    test_dir.mkdir()
    test_file = test_dir / "test.json"

    with patch(
        "homeassistant.util.file.tempfile.NamedTemporaryFile", side_effect=OSError
    ):
        expect(lambda: write_utf8_file(test_file, '{"some":"data"}', False)).to_raise(
            WriteError
        )

    expect(os.path.exists(test_file)).to_be(False)


@test
def write_utf8_file_fails_at_rename(
    tmp_path: Path = Depends(tmp_path),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that if rename fails not not remove, we do not log the failed cleanup."""
    test_dir = tmp_path / "files"
    test_dir.mkdir()
    test_file = test_dir / "test.json"

    with patch("homeassistant.util.file.os.replace", side_effect=OSError):
        expect(lambda: write_utf8_file(test_file, '{"some":"data"}', False)).to_raise(
            WriteError
        )

    expect(os.path.exists(test_file)).to_be(False)
    expect("File replacement cleanup failed" not in caplog.text).to_be(True)


@test
def write_utf8_file_fails_at_rename_and_remove(
    tmp_path: Path = Depends(tmp_path),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that if rename and remove both fail, we log the failed cleanup."""
    test_dir = tmp_path / "files"
    test_dir.mkdir()
    test_file = test_dir / "test.json"

    with (
        patch("homeassistant.util.file.os.remove", side_effect=OSError),
        patch("homeassistant.util.file.os.replace", side_effect=OSError),
    ):
        expect(lambda: write_utf8_file(test_file, '{"some":"data"}', False)).to_raise(
            WriteError
        )

    expect("File replacement cleanup failed" in caplog.text).to_be(True)


@test.cases(
    test.case("write_utf8_file", func=write_utf8_file),
    test.case("write_utf8_file_atomic", func=write_utf8_file_atomic),
)
def write_utf8_file_with_non_ascii_content(
    func: object,
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test files with non-ASCII content can be written even when locale is ASCII."""
    test_file = tmp_path / "test.json"
    non_ascii_data = '{"name":"自动化","emoji":"🏠"}'

    with patch("locale.getpreferredencoding", return_value="ascii"):
        func(test_file, non_ascii_data, False)

    file_text = test_file.read_text(encoding="utf-8")
    expect(file_text).to_equal(non_ascii_data)


@test
def write_utf8_file_atomic_fails(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test OSError from write_utf8_file_atomic is rethrown as WriteError."""
    test_dir = tmp_path / "files"
    test_dir.mkdir()
    test_file = test_dir / "test.json"

    with patch("homeassistant.util.file.AtomicWriter.open", side_effect=OSError):
        expect(
            lambda: write_utf8_file_atomic(test_file, '{"some":"data"}', False)
        ).to_raise(WriteError)

    expect(os.path.exists(test_file)).to_be(False)
