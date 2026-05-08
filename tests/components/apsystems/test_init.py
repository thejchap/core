"""Test the APSystem setup."""

import datetime
from unittest.mock import AsyncMock

from APsystemsEZ1 import InverterReturnedError
from tryke import Depends, expect, fixture, test

from homeassistant.components.apsystems.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_apsystems, mock_config_entry

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    caplog as caplog_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    LogCapture,
    mock_network,
)

SCAN_INTERVAL = datetime.timedelta(seconds=12)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_apsystems),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, mock_config_entry)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def setup_failed(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_apsystems: AsyncMock = Depends(mock_apsystems),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test update failed."""
    mock_apsystems.get_device_info.side_effect = TimeoutError
    await setup_integration(hass, mock_config_entry)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def update(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_apsystems: AsyncMock = Depends(mock_apsystems),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    caplog: LogCapture = Depends(caplog_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test update data with an inverter error and recover."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect("Inverter returned an error" not in caplog.text).to_be(True)
    mock_apsystems.get_output_data.side_effect = InverterReturnedError
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect("Error fetching APSystems Data data:" in caplog.text).to_be(True)
    caplog.clear()
    mock_apsystems.get_output_data.side_effect = None
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect("Fetching APSystems Data data recovered" in caplog.text).to_be(True)
