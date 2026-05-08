"""Tests for the deako component init."""

from unittest.mock import MagicMock

from pydeako import FindDevicesError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    pydeako_deako_mock,
    pydeako_discoverer_mock,
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
async def deako_async_setup_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    pydeako_deako_mock: MagicMock = Depends(pydeako_deako_mock),
    pydeako_discoverer_mock: MagicMock = Depends(pydeako_discoverer_mock),
) -> None:
    """Test successful setup entry."""
    pydeako_deako_mock.return_value.get_devices.return_value = {
        "id1": {},
        "id2": {},
    }
    pydeako_deako_mock.return_value.get_name.return_value = "some device"

    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    pydeako_deako_mock.assert_called_once_with(
        pydeako_discoverer_mock.return_value.get_address
    )
    pydeako_deako_mock.return_value.connect.assert_called_once()
    pydeako_deako_mock.return_value.find_devices.assert_called_once()
    pydeako_deako_mock.return_value.get_devices.assert_called()

    expect(mock_config_entry.runtime_data).to_equal(pydeako_deako_mock.return_value)


@test
async def deako_async_setup_entry_devices_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    pydeako_deako_mock: MagicMock = Depends(pydeako_deako_mock),
    pydeako_discoverer_mock: MagicMock = Depends(pydeako_discoverer_mock),
) -> None:
    """Test async_setup_entry raises ConfigEntryNotReady when pydeako raises DeviceListTimeout."""
    mock_config_entry.add_to_hass(hass)

    pydeako_deako_mock.return_value.find_devices.side_effect = FindDevicesError()

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    pydeako_deako_mock.assert_called_once_with(
        pydeako_discoverer_mock.return_value.get_address
    )
    pydeako_deako_mock.return_value.connect.assert_called_once()
    pydeako_deako_mock.return_value.find_devices.assert_called_once()
    pydeako_deako_mock.return_value.disconnect.assert_called_once()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
