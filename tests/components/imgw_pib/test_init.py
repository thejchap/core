"""Test init of IMGW-PIB integration."""

from unittest.mock import AsyncMock, patch

from imgw_pib import ApiError
from tryke import Depends, expect, fixture, test

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.imgw_pib.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import init_integration
from ._fixtures import mock_config_entry, mock_imgw_pib_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def config_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test for setup failure if the connection to the service fails."""
    with patch(
        "homeassistant.components.imgw_pib.ImgwPib.create",
        side_effect=ApiError("API Error"),
    ):
        await init_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_imgw_pib_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful unload of entry."""
    await init_integration(hass, config_entry)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def remove_binary_sensor_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_imgw_pib_client),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test removing a binary_sensor entity."""
    entity_id = "binary_sensor.river_name_station_name_flood_alarm"
    config_entry.add_to_hass(hass)

    entity_registry.async_get_or_create(
        BINARY_SENSOR_DOMAIN,
        DOMAIN,
        "123_flood_alarm",
        suggested_object_id=entity_id.rsplit(".", maxsplit=1)[-1],
        config_entry=config_entry,
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(hass.states.get(entity_id)).to_be(None)
