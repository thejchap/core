"""Tests for the diagnostics data provided by the AsusWRT integration."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.asuswrt.const import DOMAIN
from homeassistant.components.asuswrt.diagnostics import TO_REDACT
from homeassistant.components.device_tracker import CONF_CONSIDER_HOME
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import connect_legacy
from .common import CONFIG_DATA_TELNET, ROUTER_MAC_ADDR

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client,
)


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def diagnostics(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_client_session: ClientSessionGenerator = Depends(hass_client),
    connect_legacy_mock: MagicMock = Depends(connect_legacy),
) -> None:
    """Test diagnostics."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA_TELNET,
        options={CONF_CONSIDER_HOME: 60},
        unique_id=ROUTER_MAC_ADDR,
    )
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    entry_dict = async_redact_data(mock_config_entry.as_dict(), TO_REDACT)

    result = await get_diagnostics_for_config_entry(
        hass, hass_client_session, mock_config_entry
    )

    expect(result["entry"]).to_equal(entry_dict | {"discovery_keys": {}})
