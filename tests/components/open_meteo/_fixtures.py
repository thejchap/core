"""Tryke fixtures for the Open-Meteo integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.open_meteo.async_setup_entry", return_value=True
    ):
        yield
