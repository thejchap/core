"""The sensor tests for the IPMA platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from . import ENTRY_CONFIG, MockLocation

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


_FAKE_TRANSLATIONS = {
    "component.ipma.entity.sensor.fire_risk.name": "Fire risk",
    "component.ipma.entity.sensor.uv_index.name": "UV index",
    "component.ipma.entity.sensor.weather_alert.name": "Weather alert",
}


async def _fake_get_translations(hass, language, category, integrations=None, config_flow=None):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


async def _setup_with_translations(hass: HomeAssistant) -> None:
    """Set up the IPMA integration with translation patches."""
    with (
        patch("pyipma.location.Location.get", return_value=MockLocation()),
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        entry = MockConfigEntry(domain="ipma", data=ENTRY_CONFIG)
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


@test
async def ipma_fire_risk_create_sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creation of fire risk sensors."""
    await _setup_with_translations(hass)

    state = hass.states.get("sensor.hometown_fire_risk")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("3")


@test
async def ipma_uv_index_create_sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creation of uv index sensors."""
    await _setup_with_translations(hass)

    state = hass.states.get("sensor.hometown_uv_index")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("6")


@test
async def ipma_warning_create_sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creation of warning sensors."""
    await _setup_with_translations(hass)

    state = hass.states.get("sensor.hometown_weather_alert")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("yellow")
    expect(state.attributes["awarenessTypeName"]).to_equal("Agitação Marítima")
