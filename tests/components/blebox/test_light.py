"""BleBox light entities tests."""

import logging
import re
from typing import Any
from unittest.mock import AsyncMock

import blebox_uniapi
from tryke import Depends, expect, fixture, test

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGBW_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    ColorMode,
)
from homeassistant.const import (
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    _make_dimmer,
    _make_wlightbox,
    _make_wlightbox_s,
    dimmer as dimmer_fixture,
    wlightbox as wlightbox_fixture,
    wlightbox_s as wlightbox_s_fixture,
)
from .conftest import async_setup_entity

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def dimmer_init(
    hass: HomeAssistant = Depends(_trigger_executor),
    dimmer: tuple[Any, str] = Depends(dimmer_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test cover default state."""
    _, entity_id = dimmer
    entry = await async_setup_entity(hass, entity_id)
    expect(entry.unique_id).to_equal("BleBox-dimmerBox-1afe34e750b8-brightness")

    state = hass.states.get(entity_id)
    expect(state.name).to_equal("My dimmer dimmerBox-brightness")

    color_modes = state.attributes[ATTR_SUPPORTED_COLOR_MODES]
    expect(color_modes).to_equal([ColorMode.BRIGHTNESS])

    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(65)
    expect(state.state).to_equal(STATE_ON)

    device = device_registry.async_get(entry.device_id)

    expect(device.name).to_equal("My dimmer")
    expect(device.identifiers).to_equal({("blebox", "abcd0123ef5678")})
    expect(device.manufacturer).to_equal("BleBox")
    expect(device.model).to_equal("dimmerBox")
    expect(device.sw_version).to_equal("1.23")


@test
async def dimmer_update(
    hass: HomeAssistant = Depends(_trigger_executor),
    dimmer: tuple[Any, str] = Depends(dimmer_fixture),
) -> None:
    """Test light updating."""
    feature_mock, entity_id = dimmer

    def initial_update():
        feature_mock.brightness = 53

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(53)
    expect(state.state).to_equal(STATE_ON)


@test
async def dimmer_on(
    hass: HomeAssistant = Depends(_trigger_executor),
    dimmer: tuple[Any, str] = Depends(dimmer_fixture),
) -> None:
    """Test light on."""
    feature_mock, entity_id = dimmer

    def initial_update():
        feature_mock.is_on = False
        feature_mock.brightness = 0  # off
        feature_mock.sensible_on_value = 254

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_OFF)

    def turn_on(brightness):
        expect(brightness).to_equal(254)
        feature_mock.brightness = 254  # on
        feature_mock.is_on = True  # on

    feature_mock.async_on = AsyncMock(side_effect=turn_on)
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(254)


@test
async def dimmer_on_with_brightness(
    hass: HomeAssistant = Depends(_trigger_executor),
    dimmer: tuple[Any, str] = Depends(dimmer_fixture),
) -> None:
    """Test light on with a brightness value."""
    feature_mock, entity_id = dimmer

    def initial_update():
        feature_mock.is_on = False
        feature_mock.brightness = 0  # off
        feature_mock.sensible_on_value = 254

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_OFF)

    def turn_on(brightness):
        expect(brightness).to_equal(202)
        feature_mock.brightness = 202  # on
        feature_mock.is_on = True  # on

    feature_mock.async_on = AsyncMock(side_effect=turn_on)

    def apply(value, brightness):
        expect(value).to_equal(254)
        return brightness

    feature_mock.apply_brightness = apply
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {"entity_id": entity_id, ATTR_BRIGHTNESS: 202},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(202)
    expect(state.state).to_equal(STATE_ON)


@test
async def dimmer_off(
    hass: HomeAssistant = Depends(_trigger_executor),
    dimmer: tuple[Any, str] = Depends(dimmer_fixture),
) -> None:
    """Test light off."""
    feature_mock, entity_id = dimmer

    def initial_update():
        feature_mock.is_on = True

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)

    def turn_off():
        feature_mock.is_on = False
        feature_mock.brightness = 0  # off

    feature_mock.async_off = AsyncMock(side_effect=turn_off)
    await hass.services.async_call(
        "light",
        SERVICE_TURN_OFF,
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_be_none()


@test
async def wlightbox_s_init(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox_s: tuple[Any, str] = Depends(wlightbox_s_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test cover default state."""
    _, entity_id = wlightbox_s
    entry = await async_setup_entity(hass, entity_id)
    expect(entry.unique_id).to_equal("BleBox-wLightBoxS-1afe34e750b8-color")

    state = hass.states.get(entity_id)
    expect(state.name).to_equal("My wLightBoxS wLightBoxS-color")

    color_modes = state.attributes[ATTR_SUPPORTED_COLOR_MODES]
    expect(color_modes).to_equal([ColorMode.BRIGHTNESS])

    expect(state.attributes[ATTR_BRIGHTNESS]).to_be_none()
    expect(state.state).to_equal(STATE_UNKNOWN)

    device = device_registry.async_get(entry.device_id)

    expect(device.name).to_equal("My wLightBoxS")
    expect(device.identifiers).to_equal({("blebox", "abcd0123ef5678")})
    expect(device.manufacturer).to_equal("BleBox")
    expect(device.model).to_equal("wLightBoxS")
    expect(device.sw_version).to_equal("1.23")


@test
async def wlightbox_s_update(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox_s: tuple[Any, str] = Depends(wlightbox_s_fixture),
) -> None:
    """Test light updating."""
    feature_mock, entity_id = wlightbox_s

    def initial_update():
        feature_mock.brightness = 0xAB
        feature_mock.is_on = True

    feature_mock.async_update = AsyncMock(side_effect=initial_update)

    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(0xAB)


@test
async def wlightbox_s_on(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox_s: tuple[Any, str] = Depends(wlightbox_s_fixture),
) -> None:
    """Test light on."""
    feature_mock, entity_id = wlightbox_s

    def initial_update():
        feature_mock.is_on = False
        feature_mock.sensible_on_value = 254

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_OFF)

    def turn_on(brightness):
        expect(brightness).to_equal(254)
        feature_mock.brightness = 254  # on
        feature_mock.is_on = True  # on

    feature_mock.async_on = AsyncMock(side_effect=turn_on)
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(254)
    expect(state.state).to_equal(STATE_ON)


@test
async def wlightbox_init(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox: tuple[Any, str] = Depends(wlightbox_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test cover default state."""
    _, entity_id = wlightbox
    entry = await async_setup_entity(hass, entity_id)
    expect(entry.unique_id).to_equal("BleBox-wLightBox-1afe34e750b8-color")

    state = hass.states.get(entity_id)
    expect(state.name).to_equal("My wLightBox wLightBox-color")

    color_modes = state.attributes[ATTR_SUPPORTED_COLOR_MODES]
    expect(color_modes).to_equal([ColorMode.RGBW])

    expect(state.attributes[ATTR_BRIGHTNESS]).to_be_none()
    expect(state.attributes[ATTR_RGBW_COLOR]).to_be_none()
    expect(state.state).to_equal(STATE_UNKNOWN)

    device = device_registry.async_get(entry.device_id)

    expect(device.name).to_equal("My wLightBox")
    expect(device.identifiers).to_equal({("blebox", "abcd0123ef5678")})
    expect(device.manufacturer).to_equal("BleBox")
    expect(device.model).to_equal("wLightBox")
    expect(device.sw_version).to_equal("1.23")


@test
async def wlightbox_update(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox: tuple[Any, str] = Depends(wlightbox_fixture),
) -> None:
    """Test light updating."""
    feature_mock, entity_id = wlightbox

    def initial_update():
        feature_mock.is_on = True
        feature_mock.rgbw_hex = "fa00203A"
        feature_mock.white_value = 0x3A

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_RGBW_COLOR]).to_equal((0xFA, 0x00, 0x20, 0x3A))
    expect(state.state).to_equal(STATE_ON)


@test
async def wlightbox_on_rgbw(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox: tuple[Any, str] = Depends(wlightbox_fixture),
) -> None:
    """Test light on."""
    feature_mock, entity_id = wlightbox

    def initial_update():
        feature_mock.is_on = False

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_OFF)

    def turn_on(value):
        feature_mock.is_on = True
        expect(value).to_equal([193, 210, 243, 199])
        feature_mock.white_value = 0xC7  # on
        feature_mock.rgbw_hex = "c1d2f3c7"

    feature_mock.async_on = AsyncMock(side_effect=turn_on)

    def apply_white(value, white):
        expect(value).to_equal("00010203")
        expect(white).to_equal(0xC7)
        return "000102c7"

    feature_mock.apply_white = apply_white

    def apply_color(value, color_value):
        expect(value).to_equal("000102c7")
        expect(color_value).to_equal("c1d2f3")
        return "c1d2f3c7"

    feature_mock.apply_color = apply_color
    feature_mock.sensible_on_value = "00010203"

    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {"entity_id": entity_id, ATTR_RGBW_COLOR: (0xC1, 0xD2, 0xF3, 0xC7)},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_RGBW_COLOR]).to_equal((0xC1, 0xD2, 0xF3, 0xC7))


@test
async def wlightbox_on_to_last_color(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox: tuple[Any, str] = Depends(wlightbox_fixture),
) -> None:
    """Test light on."""
    feature_mock, entity_id = wlightbox

    def initial_update():
        feature_mock.is_on = False

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_OFF)

    def turn_on(value):
        feature_mock.is_on = True
        expect(value).to_equal("f1e2d3e4")
        feature_mock.white_value = 0xE4
        feature_mock.rgbw_hex = value

    feature_mock.async_on = AsyncMock(side_effect=turn_on)
    feature_mock.sensible_on_value = "f1e2d3e4"

    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_RGBW_COLOR]).to_equal((0xF1, 0xE2, 0xD3, 0xE4))
    expect(state.state).to_equal(STATE_ON)


@test
async def wlightbox_off(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox: tuple[Any, str] = Depends(wlightbox_fixture),
) -> None:
    """Test light off."""
    feature_mock, entity_id = wlightbox

    def initial_update():
        feature_mock.is_on = True

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)

    def turn_off():
        feature_mock.is_on = False
        feature_mock.white_value = 0x0
        feature_mock.rgbw_hex = "00000000"

    feature_mock.async_off = AsyncMock(side_effect=turn_off)

    await hass.services.async_call(
        "light",
        SERVICE_TURN_OFF,
        {"entity_id": entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_RGBW_COLOR]).to_be_none()
    expect(state.state).to_equal(STATE_OFF)


@test.cases(
    test.case("dimmer", factory=_make_dimmer),
    test.case("wlightbox_s", factory=_make_wlightbox_s),
    test.case("wlightbox", factory=_make_wlightbox),
)
async def update_failure(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that update failures are logged."""
    caplog.set_level(logging.ERROR)

    feature_mock, entity_id = factory()
    feature_mock.async_update = AsyncMock(side_effect=blebox_uniapi.error.ClientError)
    await async_setup_entity(hass, entity_id)

    expect(f"Updating '{feature_mock.full_name}' failed: " in caplog.text).to_be(True)


@test.cases(
    test.case("dimmer", factory=_make_dimmer),
    test.case("wlightbox_s", factory=_make_wlightbox_s),
    test.case("wlightbox", factory=_make_wlightbox),
)
async def turn_on_failure(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that turn_on failures are logged."""
    caplog.set_level(logging.ERROR)

    feature_mock, entity_id = factory()
    feature_mock.async_on = AsyncMock(side_effect=ValueError)
    await async_setup_entity(hass, entity_id)

    feature_mock.sensible_on_value = 123
    async with expect_raises_async(
        ValueError,
        match=re.escape(f"Turning on '{feature_mock.full_name}' failed: Bad value 123"),
    ):
        await hass.services.async_call(
            "light",
            SERVICE_TURN_ON,
            {"entity_id": entity_id},
            blocking=True,
        )


@test
async def wlightbox_on_effect(
    hass: HomeAssistant = Depends(_trigger_executor),
    wlightbox: tuple[Any, str] = Depends(wlightbox_fixture),
) -> None:
    """Test light on."""
    feature_mock, entity_id = wlightbox

    def initial_update():
        feature_mock.is_on = False

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_OFF)

    def turn_on(value):
        feature_mock.is_on = True
        feature_mock.effect = "POLICE"

    feature_mock.async_on = AsyncMock(side_effect=turn_on)

    async with expect_raises_async(
        ValueError,
        match=re.escape(
            f"Turning on with effect '{feature_mock.full_name}' failed: "
            "NOT IN LIST not in effect list."
        ),
    ):
        await hass.services.async_call(
            "light",
            SERVICE_TURN_ON,
            {"entity_id": entity_id, ATTR_EFFECT: "NOT IN LIST"},
            blocking=True,
        )

    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {"entity_id": entity_id, ATTR_EFFECT: "POLICE"},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_EFFECT]).to_equal("POLICE")
