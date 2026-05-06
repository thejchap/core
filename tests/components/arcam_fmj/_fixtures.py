"""Tryke fixtures for Arcam FMJ."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from .conftest import MOCK_CONFIG_ENTRY, MOCK_NAME, MOCK_UUID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass


@fixture
def dummy_client() -> Generator[MagicMock]:
    """Mock out the real client."""
    with patch("homeassistant.components.arcam_fmj.config_flow.Client") as client:
        client.return_value.start.side_effect = AsyncMock(return_value=None)
        client.return_value.stop.side_effect = AsyncMock(return_value=None)
        yield client.return_value


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.arcam_fmj.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass),
) -> MockConfigEntry:
    """Get a mock config entry."""
    config_entry = MockConfigEntry(
        domain="arcam_fmj",
        data=MOCK_CONFIG_ENTRY,
        title=MOCK_NAME,
        unique_id=MOCK_UUID,
    )
    config_entry.add_to_hass(hass)
    return config_entry
