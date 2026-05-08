"""Test entity availability."""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock

from aiohttp import ClientError
from pydrawise.schema import Controller
from tryke import Depends, expect, fixture, test

from homeassistant.components.hydrawise.const import WATER_USE_SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME, STATE_OFF, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import controller as controller_fx, mock_pydrawise

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    mock_network,
)

DOMAIN = "hydrawise"

_SPECIAL_ENTITIES = {"binary_sensor.home_controller_connectivity": STATE_OFF}


_FAKE_TRANSLATIONS = {
    "component.binary_sensor.entity_component.connectivity.name": "Connectivity",
    "component.binary_sensor.entity_component.moisture.name": "Moisture",
    "component.binary_sensor.entity_component.running.name": "Running",
}


async def _fake_get_translations(hass, language, category, integrations=None, config_flow=None):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


async def _add_config_entry(
    hass: HomeAssistant,
) -> MockConfigEntry:
    """Add a Hydrawise config entry to hass."""
    from unittest.mock import patch  # noqa: PLC0415

    entry = MockConfigEntry(
        title="Hydrawise",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "asfd@asdf.com",
            CONF_PASSWORD: "__password__",
            CONF_API_KEY: "abc123",
        },
        unique_id="hydrawise-customerid",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def _test_availability(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )
    expect(bool(entity_entries)).to_be(True)
    for entity_entry in entity_entries:
        state = hass.states.get(entity_entry.entity_id)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(
            _SPECIAL_ENTITIES.get(entity_entry.entity_id, STATE_UNAVAILABLE)
        )


@test
async def controller_offline(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pydrawise: AsyncMock = Depends(mock_pydrawise),
    controller: Controller = Depends(controller_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test availability for sensors when controller is offline."""
    controller.online = False
    config_entry = await _add_config_entry(hass)
    _test_availability(hass, config_entry, entity_registry)


@test
async def api_offline(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pydrawise: AsyncMock = Depends(mock_pydrawise),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    freezer: Any = Depends(freezer_fx),
) -> None:
    """Test availability of sensors when API call fails."""
    config_entry = await _add_config_entry(hass)
    pydrawise.get_user.reset_mock(return_value=True)
    pydrawise.get_user.side_effect = ClientError
    pydrawise.get_water_use_summary.side_effect = ClientError
    freezer.tick(WATER_USE_SCAN_INTERVAL + timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    _test_availability(hass, config_entry, entity_registry)
