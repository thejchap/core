"""Test Discovergy component setup."""

from unittest.mock import AsyncMock

from pydiscovergy.error import DiscovergyClientError, HTTPError, InvalidLogin
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import config_entry, discovergy, setup_integration

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
async def config_setup(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _discovergy: AsyncMock = Depends(discovergy),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test for setup success."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test.cases(
    test.case(
        "invalid_login",
        error=InvalidLogin,
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "http_error",
        error=HTTPError,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "discovergy_client_error",
        error=DiscovergyClientError,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "exception",
        error=Exception,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def config_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
    discovergy: AsyncMock = Depends(discovergy),
    *,
    error: Exception,
    expected_state: ConfigEntryState,
) -> None:
    """Test for setup failure."""
    config_entry.add_to_hass(hass)

    discovergy.meters.side_effect = error

    await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(expected_state)


@test
async def reload_config_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_integration),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test config entry reload."""
    new_data = {"email": "abc@example.com", "password": "password"}

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(hass.config_entries.async_update_entry(config_entry, data=new_data)).to_be(True)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.data).to_equal(new_data)
