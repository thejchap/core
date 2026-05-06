"""Tryke fixtures for Uptime integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

from homeassistant.components.uptime.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Uptime",
        domain=DOMAIN,
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.uptime.async_setup_entry", return_value=True):
        yield
