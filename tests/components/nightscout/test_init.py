"""Test the Nightscout config flow."""

from unittest.mock import patch

from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.nightscout.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant

from . import init_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def unload_entry(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test successful unload of entry."""
    entry = await init_integration(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(
        await hass.config_entries.async_unload(entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(hass.data.get(DOMAIN)).to_be_falsy()


@test
async def async_setup_raises_entry_not_ready(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "https://some.url:1234"},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.nightscout.NightscoutAPI.get_server_status",
        side_effect=ClientError(),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
