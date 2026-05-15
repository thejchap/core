"""Tryke skip stub (pending port)."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.goalzero.const import DEFAULT_NAME
from homeassistant.const import ATTR_DEVICE_CLASS, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from . import async_init_integration

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

_FAKE_TRANSLATIONS = {
    "component.goalzero.entity.binary_sensor.backlight.name": "Backlight",
    "component.goalzero.entity.binary_sensor.app_online.name": "App online",
    "component.goalzero.entity.binary_sensor.input_detected.name": "Input detected",
    "component.binary_sensor.entity_component.battery_charging.name": "Charging",
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
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def binary_sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
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
        await async_init_integration(hass, aioclient_mock)

    state = hass.states.get(f"binary_sensor.{DEFAULT_NAME}_backlight")
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_be(None)
    state = hass.states.get(f"binary_sensor.{DEFAULT_NAME}_app_online")
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(
        BinarySensorDeviceClass.CONNECTIVITY
    )
    state = hass.states.get(f"binary_sensor.{DEFAULT_NAME}_charging")
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(
        BinarySensorDeviceClass.BATTERY_CHARGING
    )
    state = hass.states.get(f"binary_sensor.{DEFAULT_NAME}_input_detected")
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(
        BinarySensorDeviceClass.POWER
    )
