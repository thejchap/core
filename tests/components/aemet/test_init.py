"""Define tests for the AEMET OpenData init."""

from unittest.mock import patch

from aemet_opendata.exceptions import AemetTimeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.aemet.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .util import mock_api_call

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

CONFIG = {
    CONF_NAME: "aemet",
    CONF_API_KEY: "foo",
    CONF_LATITUDE: 40.30403754,
    CONF_LONGITUDE: -3.72935236,
}


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def unload_entry(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test (un)loading the AEMET integration."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    with patch(
        "homeassistant.components.aemet.AEMET.api_call",
        side_effect=mock_api_call,
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN, unique_id="aemet_unique_id", data=CONFIG
        )
        config_entry.add_to_hass(hass)

        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

        await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

        expect(await hass.config_entries.async_remove(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

        expect(hass.states.get("weather.aemet")).to_be(None)
        expect(entity_registry.async_get("weather.aemet")).to_be(None)


@test
async def init_town_not_found(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test TownNotFound when loading the AEMET integration."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    with patch(
        "homeassistant.components.aemet.AEMET.api_call",
        side_effect=mock_api_call,
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_API_KEY: "api-key",
                CONF_LATITUDE: "0.0",
                CONF_LONGITUDE: "0.0",
                CONF_NAME: "AEMET",
            },
        )
        config_entry.add_to_hass(hass)

        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(
            False
        )


@test
async def init_api_timeout(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test API timeouts when loading the AEMET integration."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    with patch(
        "homeassistant.components.aemet.AEMET.api_call",
        side_effect=AemetTimeout,
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_API_KEY: "api-key",
                CONF_LATITUDE: "0.0",
                CONF_LONGITUDE: "0.0",
                CONF_NAME: "AEMET",
            },
        )
        config_entry.add_to_hass(hass)

        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(
            False
        )
