"""BleBox cover entities tests."""

import logging
from typing import Any
from unittest.mock import AsyncMock

import blebox_uniapi
from tryke import Depends, expect, fixture, test

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntityFeature,
    CoverState,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_CLOSE_COVER,
    SERVICE_CLOSE_COVER_TILT,
    SERVICE_OPEN_COVER,
    SERVICE_OPEN_COVER_TILT,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
    SERVICE_STOP_COVER,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    _make_gatebox,
    _make_gatecontroller,
    _make_shutterbox,
    gatebox as gatebox_fixture,
    gatecontroller as gatecontroller_fixture,
    shutterbox as shutterbox_fixture,
)
from .conftest import async_setup_entity

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def init_gatecontroller(
    hass: HomeAssistant = Depends(_trigger_executor),
    gatecontroller: tuple[Any, str] = Depends(gatecontroller_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test gateController default state."""
    _, entity_id = gatecontroller
    entry = await async_setup_entity(hass, entity_id)
    expect(entry.unique_id).to_equal("BleBox-gateController-2bee34e750b8-position")

    state = hass.states.get(entity_id)
    expect(state.name).to_equal("My gate controller gateController-position")
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(CoverDeviceClass.GATE)

    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    expect(bool(supported_features & CoverEntityFeature.OPEN)).to_be(True)
    expect(bool(supported_features & CoverEntityFeature.CLOSE)).to_be(True)
    expect(bool(supported_features & CoverEntityFeature.STOP)).to_be(True)

    expect(bool(supported_features & CoverEntityFeature.SET_POSITION)).to_be(True)
    expect(ATTR_CURRENT_POSITION not in state.attributes).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)

    device = device_registry.async_get(entry.device_id)

    expect(device.name).to_equal("My gate controller")
    expect(device.identifiers).to_equal({("blebox", "abcd0123ef5678")})
    expect(device.manufacturer).to_equal("BleBox")
    expect(device.model).to_equal("gateController")
    expect(device.sw_version).to_equal("1.23")


@test
async def init_shutterbox(
    hass: HomeAssistant = Depends(_trigger_executor),
    shutterbox: tuple[Any, str] = Depends(shutterbox_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test gateBox default state."""
    _, entity_id = shutterbox
    entry = await async_setup_entity(hass, entity_id)
    expect(entry.unique_id).to_equal("BleBox-shutterBox-2bee34e750b8-position")

    state = hass.states.get(entity_id)
    expect(state.name).to_equal("My shutter shutterBox-position")
    expect(entry.original_device_class).to_equal(CoverDeviceClass.SHUTTER)

    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    expect(bool(supported_features & CoverEntityFeature.OPEN)).to_be(True)
    expect(bool(supported_features & CoverEntityFeature.CLOSE)).to_be(True)
    expect(bool(supported_features & CoverEntityFeature.STOP)).to_be(True)

    expect(bool(supported_features & CoverEntityFeature.SET_POSITION)).to_be(True)
    expect(ATTR_CURRENT_POSITION not in state.attributes).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)

    device = device_registry.async_get(entry.device_id)

    expect(device.name).to_equal("My shutter")
    expect(device.identifiers).to_equal({("blebox", "abcd0123ef5678")})
    expect(device.manufacturer).to_equal("BleBox")
    expect(device.model).to_equal("shutterBox")
    expect(device.sw_version).to_equal("1.23")


@test
async def init_gatebox(
    hass: HomeAssistant = Depends(_trigger_executor),
    gatebox: tuple[Any, str] = Depends(gatebox_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test cover default state."""
    _, entity_id = gatebox
    entry = await async_setup_entity(hass, entity_id)
    expect(entry.unique_id).to_equal("BleBox-gateBox-1afe34db9437-position")

    state = hass.states.get(entity_id)
    expect(state.name).to_equal("My gatebox gateBox-position")
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(CoverDeviceClass.DOOR)

    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    expect(bool(supported_features & CoverEntityFeature.OPEN)).to_be(True)
    expect(bool(supported_features & CoverEntityFeature.CLOSE)).to_be(True)

    # Not available during init since requires fetching state to detect
    expect(bool(supported_features & CoverEntityFeature.STOP)).to_be(False)

    expect(bool(supported_features & CoverEntityFeature.SET_POSITION)).to_be(False)
    expect(ATTR_CURRENT_POSITION not in state.attributes).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)

    device = device_registry.async_get(entry.device_id)

    expect(device.name).to_equal("My gatebox")
    expect(device.identifiers).to_equal({("blebox", "abcd0123ef5678")})
    expect(device.manufacturer).to_equal("BleBox")
    expect(device.model).to_equal("gateBox")
    expect(device.sw_version).to_equal("1.23")


@test.cases(
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
    test.case("gatebox", factory=_make_gatebox),
)
async def open(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test cover opening."""
    feature_mock, entity_id = factory()

    def initial_update():
        feature_mock.state = 3  # manually stopped

    def open_gate():
        feature_mock.state = 1  # opening

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    feature_mock.async_open = AsyncMock(side_effect=open_gate)

    await async_setup_entity(hass, entity_id)
    expect(hass.states.get(entity_id).state).to_equal(CoverState.CLOSED)

    feature_mock.async_update = AsyncMock()
    await hass.services.async_call(
        "cover",
        SERVICE_OPEN_COVER,
        {"entity_id": entity_id},
        blocking=True,
    )
    expect(hass.states.get(entity_id).state).to_equal(CoverState.OPENING)


@test.cases(
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
    test.case("gatebox", factory=_make_gatebox),
)
async def close(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test cover closing."""
    feature_mock, entity_id = factory()

    def initial_update():
        feature_mock.state = 4  # open

    def close_cover():
        feature_mock.state = 0  # closing

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    feature_mock.async_close = AsyncMock(side_effect=close_cover)

    await async_setup_entity(hass, entity_id)
    expect(hass.states.get(entity_id).state).to_equal(CoverState.OPEN)

    feature_mock.async_update = AsyncMock()
    await hass.services.async_call(
        "cover", SERVICE_CLOSE_COVER, {"entity_id": entity_id}, blocking=True
    )
    expect(hass.states.get(entity_id).state).to_equal(CoverState.CLOSING)


def opening_to_stop_feature_mock(feature_mock):
    """Return an mocked feature which can be updated and stopped."""

    def initial_update():
        feature_mock.state = 1  # opening

    def stop():
        feature_mock.state = 2  # manually stopped

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    feature_mock.async_stop = AsyncMock(side_effect=stop)


@test.cases(
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
)
async def stop(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test cover stopping."""
    feature_mock, entity_id = factory()
    opening_to_stop_feature_mock(feature_mock)

    await async_setup_entity(hass, entity_id)
    expect(hass.states.get(entity_id).state).to_equal(CoverState.OPENING)

    feature_mock.async_update = AsyncMock()
    await hass.services.async_call(
        "cover", SERVICE_STOP_COVER, {"entity_id": entity_id}, blocking=True
    )
    expect(hass.states.get(entity_id).state).to_equal(CoverState.OPEN)


@test.cases(
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
)
async def update_inverted(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test cover position is inverted for shutterBox and gateController."""
    feature_mock, entity_id = factory()

    def initial_update():
        feature_mock.current = 29  # device: 29% closed = 71% open
        feature_mock.state = 2  # manually stopped

    feature_mock.async_update = AsyncMock(side_effect=initial_update)

    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(71)  # 100 - 29
    expect(state.state).to_equal(CoverState.OPEN)


@test
async def update_not_inverted(
    hass: HomeAssistant = Depends(_trigger_executor),
    gatebox: tuple[Any, str] = Depends(gatebox_fixture),
) -> None:
    """Test cover position is not inverted for gateBox."""
    feature_mock, entity_id = gatebox

    def initial_update():
        feature_mock.current = 100  # fully open
        feature_mock.state = 4  # open

    feature_mock.async_update = AsyncMock(side_effect=initial_update)

    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(100)
    expect(state.state).to_equal(CoverState.OPEN)


@test.cases(
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
)
async def set_position(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test cover position setting."""
    feature_mock, entity_id = factory()

    def initial_update():
        feature_mock.state = 3  # closed

    def set_position_impl(position):
        expect(position).to_equal(99)  # inverted
        feature_mock.state = 1  # opening

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    feature_mock.async_set_position = AsyncMock(side_effect=set_position_impl)

    await async_setup_entity(hass, entity_id)
    expect(hass.states.get(entity_id).state).to_equal(CoverState.CLOSED)

    feature_mock.async_update = AsyncMock()
    await hass.services.async_call(
        "cover",
        SERVICE_SET_COVER_POSITION,
        {"entity_id": entity_id, ATTR_POSITION: 1},
        blocking=True,
    )  # almost closed
    expect(hass.states.get(entity_id).state).to_equal(CoverState.OPENING)


@test
async def unknown_position(
    hass: HomeAssistant = Depends(_trigger_executor),
    shutterbox: tuple[Any, str] = Depends(shutterbox_fixture),
) -> None:
    """Test cover position setting."""
    feature_mock, entity_id = shutterbox

    def initial_update():
        feature_mock.state = 4  # opening
        feature_mock.current = -1

    feature_mock.async_update = AsyncMock(side_effect=initial_update)

    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(CoverState.OPEN)
    expect(ATTR_CURRENT_POSITION not in state.attributes).to_be(True)


@test
async def with_stop(
    hass: HomeAssistant = Depends(_trigger_executor),
    gatebox: tuple[Any, str] = Depends(gatebox_fixture),
) -> None:
    """Test stop capability is available."""
    feature_mock, entity_id = gatebox
    opening_to_stop_feature_mock(feature_mock)
    feature_mock.has_stop = True

    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    expect(bool(supported_features & CoverEntityFeature.STOP)).to_be(True)


@test
async def with_no_stop(
    hass: HomeAssistant = Depends(_trigger_executor),
    gatebox: tuple[Any, str] = Depends(gatebox_fixture),
) -> None:
    """Test stop capability is not available."""
    feature_mock, entity_id = gatebox
    opening_to_stop_feature_mock(feature_mock)
    feature_mock.has_stop = False

    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    expect(bool(supported_features & CoverEntityFeature.STOP)).to_be(False)


@test.cases(
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
    test.case("gatebox", factory=_make_gatebox),
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
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
    test.case("gatebox", factory=_make_gatebox),
)
async def opening_state(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that entity properties work."""
    feature_mock, entity_id = factory()

    def initial_update():
        feature_mock.state = 1  # opening

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    expect(hass.states.get(entity_id).state).to_equal(CoverState.OPENING)


@test.cases(
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
    test.case("gatebox", factory=_make_gatebox),
)
async def closing_state(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that entity properties work."""
    feature_mock, entity_id = factory()

    def initial_update():
        feature_mock.state = 0  # closing

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    expect(hass.states.get(entity_id).state).to_equal(CoverState.CLOSING)


@test.cases(
    test.case("gatecontroller", factory=_make_gatecontroller),
    test.case("shutterbox", factory=_make_shutterbox),
    test.case("gatebox", factory=_make_gatebox),
)
async def closed_state(
    factory: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that entity properties work."""
    feature_mock, entity_id = factory()

    def initial_update():
        feature_mock.state = 3  # closed

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    await async_setup_entity(hass, entity_id)
    expect(hass.states.get(entity_id).state).to_equal(CoverState.CLOSED)


@test
async def tilt_position(
    hass: HomeAssistant = Depends(_trigger_executor),
    shutterbox: tuple[Any, str] = Depends(shutterbox_fixture),
) -> None:
    """Test tilt capability is available."""
    feature_mock, entity_id = shutterbox

    def tilt_update():
        feature_mock.tilt_current = 90

    feature_mock.async_update = AsyncMock(side_effect=tilt_update)

    await async_setup_entity(hass, entity_id)

    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(10)


@test
async def set_tilt_position(
    hass: HomeAssistant = Depends(_trigger_executor),
    shutterbox: tuple[Any, str] = Depends(shutterbox_fixture),
) -> None:
    """Test tilt position setting."""
    feature_mock, entity_id = shutterbox

    def initial_update():
        feature_mock.state = 3

    def set_tilt(tilt_position):
        expect(tilt_position).to_equal(20)
        feature_mock.state = 1

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    feature_mock.async_set_tilt_position = AsyncMock(side_effect=set_tilt)

    await async_setup_entity(hass, entity_id)
    expect(hass.states.get(entity_id).state).to_equal(CoverState.CLOSED)

    feature_mock.async_update = AsyncMock()
    await hass.services.async_call(
        "cover",
        SERVICE_SET_COVER_TILT_POSITION,
        {"entity_id": entity_id, ATTR_TILT_POSITION: 80},
        blocking=True,
    )
    expect(hass.states.get(entity_id).state).to_equal(CoverState.OPENING)


@test
async def open_tilt(
    hass: HomeAssistant = Depends(_trigger_executor),
    shutterbox: tuple[Any, str] = Depends(shutterbox_fixture),
) -> None:
    """Test closing tilt."""
    feature_mock, entity_id = shutterbox

    def initial_update():
        feature_mock.tilt_current = 100

    def set_tilt_position_impl(tilt_position):
        expect(tilt_position).to_equal(0)
        feature_mock.tilt_current = tilt_position

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    feature_mock.async_set_tilt_position = AsyncMock(side_effect=set_tilt_position_impl)

    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    await hass.services.async_call(
        "cover",
        SERVICE_OPEN_COVER_TILT,
        {"entity_id": entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(100)  # inverted


@test
async def close_tilt(
    hass: HomeAssistant = Depends(_trigger_executor),
    shutterbox: tuple[Any, str] = Depends(shutterbox_fixture),
) -> None:
    """Test closing tilt."""
    feature_mock, entity_id = shutterbox

    def initial_update():
        feature_mock.tilt_current = 0

    def set_tilt_position_impl(tilt_position):
        expect(tilt_position).to_equal(100)
        feature_mock.tilt_current = tilt_position

    feature_mock.async_update = AsyncMock(side_effect=initial_update)
    feature_mock.async_set_tilt_position = AsyncMock(side_effect=set_tilt_position_impl)

    await async_setup_entity(hass, entity_id)
    feature_mock.async_update = AsyncMock()

    await hass.services.async_call(
        "cover",
        SERVICE_CLOSE_COVER_TILT,
        {"entity_id": entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(0)  # inverted
