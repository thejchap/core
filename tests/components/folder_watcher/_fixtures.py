"""Tryke fixtures for the folder_watcher integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.folder_watcher.async_setup_entry", return_value=True
    ):
        yield
