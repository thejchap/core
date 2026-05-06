"""Tests for the Abode light device."""

from unittest.mock import patch

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode import ATTR_DEVICE_ID
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    DOMAIN as LIGHT_DOMAIN,
    ColorMode,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import mock_light_profiles, requests_mock_fixture
from .common import setup_platform

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

DEVICE_ID = "light.living_room_lamp"


@fixture
def _abode_setup(
    _requests: requests_mock.Mocker = Depends(requests_mock_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Wire the autouse Abode HTTP and light-profile mocks for tryke."""


@test
async def entity_registry(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(hass, LIGHT_DOMAIN)

    entry = entity_registry.async_get(DEVICE_ID)
    expect(entry.unique_id).to_equal("741385f4388b2637df4c6b398fe50581")


@test
async def attributes(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the light attributes are correct."""
    await setup_platform(hass, LIGHT_DOMAIN)

    state = hass.states.get(DEVICE_ID)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get(ATTR_BRIGHTNESS)).to_equal(204)
    expect(state.attributes.get(ATTR_RGB_COLOR)).to_equal((0, 64, 255))
    expect(state.attributes.get(ATTR_COLOR_TEMP_KELVIN)).to_be(None)
    expect(state.attributes.get(ATTR_DEVICE_ID)).to_equal("ZB:db5b1a")
    expect(state.attributes.get("battery_low")).to_be_falsy()
    expect(state.attributes.get("no_response")).to_be_falsy()
    expect(state.attributes.get("device_type")).to_equal("RGB Dimmer")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Living Room Lamp")
    expect(state.attributes.get(ATTR_SUPPORTED_FEATURES)).to_equal(0)
    expect(state.attributes.get(ATTR_COLOR_MODE)).to_equal(ColorMode.HS)
    expect(state.attributes.get(ATTR_SUPPORTED_COLOR_MODES)).to_equal(
        [ColorMode.COLOR_TEMP, ColorMode.HS]
    )


@test
async def switch_off(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the light can be turned off."""
    await setup_platform(hass, LIGHT_DOMAIN)

    with patch("jaraco.abode.devices.light.Light.switch_off") as mock_switch_off:
        await hass.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: DEVICE_ID}, blocking=True
        )
        await hass.async_block_till_done()
        mock_switch_off.assert_called_once()


@test
async def switch_on(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the light can be turned on."""
    await setup_platform(hass, LIGHT_DOMAIN)

    with patch("jaraco.abode.devices.light.Light.switch_on") as mock_switch_on:
        await hass.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: DEVICE_ID}, blocking=True
        )
        await hass.async_block_till_done()
        mock_switch_on.assert_called_once()


@test
async def set_brightness(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the brightness can be set."""
    await setup_platform(hass, LIGHT_DOMAIN)

    with patch("jaraco.abode.devices.light.Light.set_level") as mock_set_level:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: DEVICE_ID, "brightness": 100},
            blocking=True,
        )
        await hass.async_block_till_done()
        # Brightness is converted in abode.light.AbodeLight.turn_on
        mock_set_level.assert_called_once_with(39)


@test
async def set_color(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the color can be set."""
    await setup_platform(hass, LIGHT_DOMAIN)

    with patch("jaraco.abode.devices.light.Light.set_color") as mock_set_color:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: DEVICE_ID, "hs_color": [240, 100]},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_set_color.assert_called_once_with((240.0, 100.0))


@test
async def set_color_temp(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the color temp can be set."""
    await setup_platform(hass, LIGHT_DOMAIN)

    with patch(
        "jaraco.abode.devices.light.Light.set_color_temp"
    ) as mock_set_color_temp:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: DEVICE_ID, "color_temp_kelvin": 3236},
            blocking=True,
        )
        await hass.async_block_till_done()
        # Color temp is converted in abode.light.AbodeLight.turn_on
        mock_set_color_temp.assert_called_once_with(3236)
