"""Test the Home Knocki init module."""

from unittest.mock import AsyncMock

from knocki import KnockiConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_knocki_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def load_unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_knocki_client: AsyncMock = Depends(mock_knocki_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def initialization_failure(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_knocki_client: AsyncMock = Depends(mock_knocki_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test initialization failure."""
    mock_knocki_client.get_triggers.side_effect = KnockiConnectionError

    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
