"""The sensor tests for the Dexcom platform."""

from unittest.mock import patch

from pydexcom.errors import SessionError
from tryke import Depends, expect, fixture, test

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import async_update_entity

from . import GLUCOSE_READING, init_integration

from tests.hass_fixtures import hass as hass_fixture, mock_network


_FAKE_TRANSLATIONS = {
    "component.dexcom.entity.sensor.glucose_value.name": "Glucose value",
    "component.dexcom.entity.sensor.glucose_trend.name": "Glucose trend",
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def sensors(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get sensor data."""
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
        await init_integration(hass)

    test_username_glucose_value = hass.states.get("sensor.test_username_glucose_value")
    expect(test_username_glucose_value).not_.to_be(None)
    expect(test_username_glucose_value.state).to_equal(str(GLUCOSE_READING.value))
    test_username_glucose_trend = hass.states.get("sensor.test_username_glucose_trend")
    expect(test_username_glucose_trend).not_.to_be(None)
    expect(test_username_glucose_trend.state).to_equal(GLUCOSE_READING.trend_description)


@test
async def sensors_unknown(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle sensor state unknown."""
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
        await init_integration(hass)

        with patch(
            "homeassistant.components.dexcom.Dexcom.get_current_glucose_reading",
            return_value=None,
        ):
            await async_update_entity(hass, "sensor.test_username_glucose_value")
            await async_update_entity(hass, "sensor.test_username_glucose_trend")

    test_username_glucose_value = hass.states.get("sensor.test_username_glucose_value")
    expect(test_username_glucose_value).not_.to_be(None)
    expect(test_username_glucose_value.state).to_equal(STATE_UNKNOWN)
    test_username_glucose_trend = hass.states.get("sensor.test_username_glucose_trend")
    expect(test_username_glucose_trend).not_.to_be(None)
    expect(test_username_glucose_trend.state).to_equal(STATE_UNKNOWN)


@test
async def sensors_update_failed(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle sensor update failed."""
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
        await init_integration(hass)

        with patch(
            "homeassistant.components.dexcom.Dexcom.get_current_glucose_reading",
            side_effect=SessionError,
        ):
            await async_update_entity(hass, "sensor.test_username_glucose_value")
            await async_update_entity(hass, "sensor.test_username_glucose_trend")

    test_username_glucose_value = hass.states.get("sensor.test_username_glucose_value")
    expect(test_username_glucose_value).not_.to_be(None)
    expect(test_username_glucose_value.state).to_equal(STATE_UNAVAILABLE)
    test_username_glucose_trend = hass.states.get("sensor.test_username_glucose_trend")
    expect(test_username_glucose_trend).not_.to_be(None)
    expect(test_username_glucose_trend.state).to_equal(STATE_UNAVAILABLE)
