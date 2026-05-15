"""Tests for the AsusWrt integration."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.asuswrt.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from ._fixtures import connect_legacy
from .common import CONFIG_DATA_TELNET, ROUTER_MAC_ADDR

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def disconnect_on_stop(
    hass: HomeAssistant = Depends(_trigger_executor),
    connect_legacy_mock: MagicMock = Depends(connect_legacy),
) -> None:
    """Test we close the connection with the router when Home Assistants stops."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA_TELNET,
        unique_id=ROUTER_MAC_ADDR,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    expect(connect_legacy_mock.return_value.async_disconnect.await_count).to_equal(1)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
