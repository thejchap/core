"""Test the IPMA integration."""

from unittest.mock import patch

from pyipma import IPMAException
from tryke import Depends, expect, fixture, test

from homeassistant.components.ipma.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_MODE
from homeassistant.core import HomeAssistant

from . import MockLocation

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def async_setup_raises_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    with patch(
        "pyipma.location.Location.get", side_effect=IPMAException("API unavailable")
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Home",
            data={CONF_LATITUDE: 0, CONF_LONGITUDE: 0, CONF_MODE: "daily"},
        )

        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)

        expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entry unloading."""
    with patch(
        "pyipma.location.Location.get",
        return_value=MockLocation(),
    ):
        config_entry = MockConfigEntry(
            domain="ipma",
            data={CONF_LATITUDE: 0, CONF_LONGITUDE: 0, CONF_MODE: "daily"},
        )
        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

        await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
