"""Tests for the Leviton Decora Wi-Fi __init__ (config entry setup/unload)."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_decora_wifi, mock_person

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
async def setup_unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_decora_wifi: MagicMock = Depends(mock_decora_wifi),
) -> None:
    """Test config entry setup and unload."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def setup_entry_auth_failed(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_decora_wifi: MagicMock = Depends(mock_decora_wifi),
) -> None:
    """Test config entry setup fails on auth error."""
    mock_decora_wifi.login.return_value = None

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_entry_cannot_connect(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_decora_wifi: MagicMock = Depends(mock_decora_wifi),
) -> None:
    """Test config entry setup retries on connection error."""
    mock_decora_wifi.login.side_effect = ValueError("Cannot connect")

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry_logout_failure(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_decora_wifi: MagicMock = Depends(mock_decora_wifi),
    mock_person: MagicMock = Depends(mock_person),
) -> None:
    """Test unload succeeds even if logout raises ValueError."""
    mock_person.logout.side_effect = ValueError("Logout failed")

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def stop_event_logs_out(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_decora_wifi: MagicMock = Depends(mock_decora_wifi),
    mock_person: MagicMock = Depends(mock_person),
) -> None:
    """Test that the HA stop event triggers a session logout."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    mock_person.logout.assert_called_once_with(mock_decora_wifi)
