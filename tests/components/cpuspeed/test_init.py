"""Tests for the CPU Speed integration."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.cpuspeed.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_cpuinfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    caplog as caplog_fixture,
    hass as hass_fixture,
    LogCapture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload_config_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_cpuinfo: MagicMock = Depends(mock_cpuinfo),
) -> None:
    """Test the CPU Speed configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(mock_cpuinfo.mock_calls)).to_equal(2)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_compatible(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_cpuinfo: MagicMock = Depends(mock_cpuinfo),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the CPU Speed configuration entry loading on an unsupported system."""
    mock_config_entry.add_to_hass(hass)
    mock_cpuinfo.return_value = {}

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(len(mock_cpuinfo.mock_calls)).to_equal(1)
    expect("is not compatible with your system" in caplog.text).to_be(True)
