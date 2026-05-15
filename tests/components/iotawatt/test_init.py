"""Test init."""

from unittest.mock import MagicMock

import httpx
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import INPUT_SENSOR
from ._fixtures import (
    entry as entry_fixture,
    mock_iotawatt as mock_iotawatt_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def setup_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_iotawatt: MagicMock = Depends(mock_iotawatt_fixture),
    entry: MockConfigEntry = Depends(entry_fixture),
) -> None:
    """Test we can setup and unload an entry."""
    mock_iotawatt.getSensors.return_value["sensors"]["my_sensor_key"] = INPUT_SENSOR
    expect(bool(await async_setup_component(hass, "iotawatt", {}))).to_be(True)
    await hass.async_block_till_done()
    expect(bool(await hass.config_entries.async_unload(entry.entry_id))).to_be(True)


@test
async def setup_connection_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_iotawatt: MagicMock = Depends(mock_iotawatt_fixture),
    entry: MockConfigEntry = Depends(entry_fixture),
) -> None:
    """Test connection error during startup."""
    mock_iotawatt.connect.side_effect = httpx.ConnectError("")
    expect(bool(await async_setup_component(hass, "iotawatt", {}))).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_auth_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_iotawatt: MagicMock = Depends(mock_iotawatt_fixture),
    entry: MockConfigEntry = Depends(entry_fixture),
) -> None:
    """Test auth error during startup."""
    mock_iotawatt.connect.return_value = False
    expect(bool(await async_setup_component(hass, "iotawatt", {}))).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
