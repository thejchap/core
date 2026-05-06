"""Tryke fixtures for the EnergyZero integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.energyzero.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.energyzero.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="energy",
        domain=DOMAIN,
        data={},
        unique_id=DOMAIN,
        entry_id="12345",
    )
