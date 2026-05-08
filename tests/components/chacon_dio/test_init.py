"""Test the Dio Chacon Cover init."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_dio_chacon_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def cover_unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_dio_chacon_client: AsyncMock = Depends(mock_dio_chacon_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test the creation and values of the Dio Chacon covers."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    mock_dio_chacon_client.disconnect.assert_called()


@test
async def cover_shutdown_event(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_dio_chacon_client: AsyncMock = Depends(mock_dio_chacon_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test the creation and values of the Dio Chacon covers."""
    await setup_integration(hass, mock_config_entry)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    mock_dio_chacon_client.disconnect.assert_called()
