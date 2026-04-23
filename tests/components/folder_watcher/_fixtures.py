"""Tryke fixtures for Folder Watcher."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import tempfile
from unittest.mock import patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.folder_watcher.async_setup_entry", return_value=True
    ):
        yield


@fixture
def tmp_path() -> Generator[Path]:
    """Provide a temp directory path, replacing pytest's tmp_path."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)
