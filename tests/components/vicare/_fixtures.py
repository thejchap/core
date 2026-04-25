"""Tryke fixtures for the ViCare integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.vicare.const import DOMAIN

from . import ENTRY_CONFIG, MODULE

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(f"{MODULE}.async_setup_entry", return_value=True) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="ViCare",
        entry_id="1234",
        data=ENTRY_CONFIG,
        minor_version=2,
    )
