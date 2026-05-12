"""Tests for Glances integration."""

from unittest.mock import MagicMock

from glances_api.exceptions import (
    GlancesApiAuthorizationError,
    GlancesApiConnectionError,
    GlancesApiNoDataAvailable,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.glances.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import MOCK_USER_INPUT
from ._fixtures import mock_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def successful_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: MagicMock = Depends(mock_api),
) -> None:
    """Test that Glances is configured successfully."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test.cases(
    test.case(
        "auth_error",
        error=GlancesApiAuthorizationError,
        entry_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "connection_error",
        error=GlancesApiConnectionError,
        entry_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "no_data",
        error=GlancesApiNoDataAvailable,
        entry_state=ConfigEntryState.SETUP_ERROR,
    ),
)
async def setup_error(
    error: type[Exception],
    entry_state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test Glances failed due to api error."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT)
    entry.add_to_hass(hass)

    api.return_value.get_ha_sensor_data.side_effect = error
    await hass.config_entries.async_setup(entry.entry_id)
    expect(entry.state).to_be(entry_state)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: MagicMock = Depends(mock_api),
) -> None:
    """Test removing Glances."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(DOMAIN not in hass.data).to_be(True)
