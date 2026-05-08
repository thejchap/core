"""Tests for the Android TV Remote integration."""

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

from androidtvremote2 import CannotConnect, InvalidAuth
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from ._fixtures import mock_api, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def load_unload_config_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_api),
) -> None:
    """Test the Android TV Remote configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(mock_api.async_connect.call_count).to_equal(1)
    expect(mock_api.keep_reconnecting.call_count).to_equal(1)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(mock_api.disconnect.call_count).to_equal(1)


@test
async def config_entry_not_ready(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_api),
) -> None:
    """Test the Android TV Remote configuration entry not ready."""
    mock_api.async_connect = AsyncMock(side_effect=CannotConnect())

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(mock_api.async_connect.call_count).to_equal(1)
    expect(mock_api.keep_reconnecting.call_count).to_equal(0)


@test
async def config_entry_reauth_at_setup(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_api),
) -> None:
    """Test the Android TV Remote configuration entry needs reauth at setup."""
    mock_api.async_connect = AsyncMock(side_effect=InvalidAuth())

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(any(mock_config_entry.async_get_active_flows(hass, {"reauth"}))).to_be(True)
    expect(mock_api.async_connect.call_count).to_equal(1)
    expect(mock_api.keep_reconnecting.call_count).to_equal(0)


@test
async def config_entry_reauth_while_reconnecting(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_api),
) -> None:
    """Test the Android TV Remote configuration entry needs reauth while reconnecting."""
    invalid_auth_callback: Callable | None = None

    def mocked_keep_reconnecting(callback: Callable):
        nonlocal invalid_auth_callback
        invalid_auth_callback = callback

    mock_api.keep_reconnecting.side_effect = mocked_keep_reconnecting

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(any(mock_config_entry.async_get_active_flows(hass, {"reauth"}))).to_be(False)
    expect(mock_api.async_connect.call_count).to_equal(1)
    expect(mock_api.keep_reconnecting.call_count).to_equal(1)

    expect(invalid_auth_callback).not_.to_be(None)
    invalid_auth_callback()
    await hass.async_block_till_done()
    expect(any(mock_config_entry.async_get_active_flows(hass, {"reauth"}))).to_be(True)


@test
async def disconnect_on_stop(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_api),
) -> None:
    """Test we close the connection with the Android TV when Home Assistants stops."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(mock_api.async_connect.call_count).to_equal(1)
    expect(mock_api.keep_reconnecting.call_count).to_equal(1)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    expect(mock_api.disconnect.call_count).to_equal(1)
