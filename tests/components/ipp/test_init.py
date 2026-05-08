"""Tests for the IPP integration."""

from unittest.mock import MagicMock, patch

from pyipp import IPPConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.ipp.coordinator import IPPDataUpdateCoordinator
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_ipp

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
async def config_entry_not_ready(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the IPP configuration entry not ready."""
    with patch(
        "homeassistant.components.ipp.coordinator.IPP._request",
        side_effect=IPPConnectionError,
    ) as mock_request:
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        expect(mock_request.call_count).to_equal(1)
        expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_ipp: MagicMock = Depends(mock_ipp),
) -> None:
    """Test the IPP configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(isinstance(mock_config_entry.runtime_data, IPPDataUpdateCoordinator)).to_be(True)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
