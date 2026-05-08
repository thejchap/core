"""Tests for init methods."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_flipr_client as mock_flipr_client_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Tryke discovery anchor."""


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_flipr_client: AsyncMock = Depends(mock_flipr_client_fixture),
) -> None:
    """Test unload entry."""
    mock_flipr_client.search_all_ids.return_value = {
        "flipr": ["myfliprid"],
        "hub": ["hubid"],
    }

    await setup_integration(hass, mock_config_entry)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
