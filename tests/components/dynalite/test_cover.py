"""Test Dynalite cover."""

from collections.abc import Callable
from unittest.mock import Mock

from dynalite_devices_lib.cover import DynaliteTimeCoverWithTiltDevice
from dynalite_devices_lib.dynalitebase import DynaliteBaseDevice
from tryke import Depends, expect, fixture, test

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverState,
)
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError

from .common import (
    ATTR_ARGS,
    ATTR_METHOD,
    ATTR_SERVICE,
    create_entity_from_device,
    create_mock_device,
    run_service_tests,
)

from tests.common import mock_restore_cache
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@fixture
def mock_device() -> Mock:
    """Mock a Dynalite device."""
    mock_dev = create_mock_device("cover", DynaliteTimeCoverWithTiltDevice)
    mock_dev.device_class = CoverDeviceClass.BLIND.value
    mock_dev.current_cover_position = 0
    mock_dev.current_cover_tilt_position = 0
    mock_dev.is_opening = False
    mock_dev.is_closing = False
    mock_dev.is_closed = True

    def mock_init_level(target):
        mock_dev.is_closed = target == 0

    type(mock_dev).init_level = Mock(side_effect=mock_init_level)

    return mock_dev


@test
async def cover_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device: Mock = Depends(mock_device),
) -> None:
    """Test a successful setup."""
    await create_entity_from_device(hass, mock_device)
    entity_state = hass.states.get("cover.name")
    expect(entity_state.attributes[ATTR_FRIENDLY_NAME]).to_equal(mock_device.name)
    expect(entity_state.attributes[ATTR_CURRENT_POSITION]).to_equal(
        mock_device.current_cover_position
    )
    expect(entity_state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(
        mock_device.current_cover_tilt_position
    )
    expect(entity_state.attributes[ATTR_DEVICE_CLASS]).to_equal(mock_device.device_class)
    await run_service_tests(
        hass,
        mock_device,
        "cover",
        [
            {ATTR_SERVICE: "open_cover", ATTR_METHOD: "async_open_cover"},
            {ATTR_SERVICE: "close_cover", ATTR_METHOD: "async_close_cover"},
            {ATTR_SERVICE: "stop_cover", ATTR_METHOD: "async_stop_cover"},
            {
                ATTR_SERVICE: "set_cover_position",
                ATTR_METHOD: "async_set_cover_position",
                ATTR_ARGS: {ATTR_POSITION: 50},
            },
            {ATTR_SERVICE: "open_cover_tilt", ATTR_METHOD: "async_open_cover_tilt"},
            {ATTR_SERVICE: "close_cover_tilt", ATTR_METHOD: "async_close_cover_tilt"},
            {ATTR_SERVICE: "stop_cover_tilt", ATTR_METHOD: "async_stop_cover_tilt"},
            {
                ATTR_SERVICE: "set_cover_tilt_position",
                ATTR_METHOD: "async_set_cover_tilt_position",
                ATTR_ARGS: {ATTR_TILT_POSITION: 50},
            },
        ],
    )


@test
async def cover_without_tilt(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device: Mock = Depends(mock_device),
) -> None:
    """Test a cover with no tilt."""
    mock_device.has_tilt = False
    await create_entity_from_device(hass, mock_device)
    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            "cover", "open_cover_tilt", {"entity_id": "cover.name"}, blocking=True
        )
    await hass.async_block_till_done()
    mock_device.async_open_cover_tilt.assert_not_called()


async def _check_cover_position(
    hass: HomeAssistant,
    update_func: Callable[[DynaliteBaseDevice | None], None],
    device: Mock,
    closing: bool,
    opening: bool,
    closed: bool,
    expected: str,
) -> None:
    """Check that a given position behaves correctly."""
    device.is_closing = closing
    device.is_opening = opening
    device.is_closed = closed
    update_func(device)
    await hass.async_block_till_done()
    entity_state = hass.states.get("cover.name")
    expect(entity_state.state).to_equal(expected)


@test
async def cover_positions(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device: Mock = Depends(mock_device),
) -> None:
    """Test that the state updates in the various positions."""
    update_func = await create_entity_from_device(hass, mock_device)
    await _check_cover_position(
        hass, update_func, mock_device, True, False, False, CoverState.CLOSING
    )
    await _check_cover_position(
        hass, update_func, mock_device, False, True, False, CoverState.OPENING
    )
    await _check_cover_position(
        hass, update_func, mock_device, False, False, True, CoverState.CLOSED
    )
    await _check_cover_position(
        hass, update_func, mock_device, False, False, False, CoverState.OPEN
    )


@test
async def cover_restore_state(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device: Mock = Depends(mock_device),
) -> None:
    """Test restore from cache."""
    mock_restore_cache(
        hass,
        [State("cover.name", CoverState.OPEN, attributes={ATTR_CURRENT_POSITION: 77})],
    )
    await create_entity_from_device(hass, mock_device)
    mock_device.init_level.assert_called_once_with(77)
    entity_state = hass.states.get("cover.name")
    expect(entity_state.state).to_equal(CoverState.OPEN)


@test
async def cover_restore_state_bad_cache(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device: Mock = Depends(mock_device),
) -> None:
    """Test restore from a cache without the attribute."""
    mock_restore_cache(
        hass,
        [State("cover.name", CoverState.OPEN, attributes={"bla bla": 77})],
    )
    await create_entity_from_device(hass, mock_device)
    mock_device.init_level.assert_not_called()
    entity_state = hass.states.get("cover.name")
    expect(entity_state.state).to_equal(CoverState.CLOSED)
