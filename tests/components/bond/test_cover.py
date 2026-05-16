"""Tests for the Bond cover device."""

from datetime import timedelta

from bond_async import Action, DeviceType
from tryke import Depends, expect, fixture, test

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    CoverState,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_CLOSE_COVER_TILT,
    SERVICE_OPEN_COVER,
    SERVICE_OPEN_COVER_TILT,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    SERVICE_STOP_COVER_TILT,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import utcnow

from .common import (
    help_test_entity_available,
    patch_bond_action,
    patch_bond_device_state,
    setup_platform,
)

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Anchor module-level fixtures."""
    return 0


def shades(name: str):
    """Create motorized shades with given name."""
    return {
        "name": name,
        "type": DeviceType.MOTORIZED_SHADES,
        "actions": ["Open", "Close", "Hold"],
    }


def shades_with_position(name: str):
    """Create motorized shades that supports set position."""
    return {
        "name": name,
        "type": DeviceType.MOTORIZED_SHADES,
        "actions": [Action.OPEN, Action.CLOSE, Action.HOLD, Action.SET_POSITION],
    }


def tilt_only_shades(name: str):
    """Create motorized shades that only tilt."""
    return {
        "name": name,
        "type": DeviceType.MOTORIZED_SHADES,
        "actions": ["TiltOpen", "TiltClose", "Hold"],
    }


def tilt_shades(name: str):
    """Create motorized shades with given name that can also tilt."""
    return {
        "name": name,
        "type": DeviceType.MOTORIZED_SHADES,
        "actions": ["Open", "Close", "Hold", "TiltOpen", "TiltClose", "Hold"],
    }


@test
async def entity_registry_test(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(
        hass,
        COVER_DOMAIN,
        shades("name-1"),
        bond_version={"bondid": "test-hub-id"},
        bond_device_id="test-device-id",
    )

    entity = entity_registry.entities["cover.name_1"]
    expect(entity.unique_id).to_equal("test-hub-id_test-device-id")


@test
async def open_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that open cover command delegates to API."""
    await setup_platform(
        hass, COVER_DOMAIN, shades("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_open, patch_bond_device_state():
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_open.assert_called_once_with("test-device-id", Action.open())


@test
async def close_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that close cover command delegates to API."""
    await setup_platform(
        hass, COVER_DOMAIN, shades("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_close, patch_bond_device_state():
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_close.assert_called_once_with("test-device-id", Action.close())


@test
async def stop_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that stop cover command delegates to API."""
    await setup_platform(
        hass, COVER_DOMAIN, shades("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_hold, patch_bond_device_state():
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_hold.assert_called_once_with("test-device-id", Action.hold())


@test
async def tilt_open_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that tilt open cover command delegates to API."""
    await setup_platform(
        hass, COVER_DOMAIN, tilt_only_shades("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_open, patch_bond_device_state():
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER_TILT,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_open.assert_called_once_with("test-device-id", Action.tilt_open())
    expect(hass.states.get("cover.name_1").state).to_be(STATE_UNKNOWN)


@test
async def tilt_close_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that tilt close cover command delegates to API."""
    await setup_platform(
        hass, COVER_DOMAIN, tilt_only_shades("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_close, patch_bond_device_state():
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER_TILT,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_close.assert_called_once_with("test-device-id", Action.tilt_close())
    expect(hass.states.get("cover.name_1").state).to_be(STATE_UNKNOWN)


@test
async def tilt_stop_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that tilt stop cover command delegates to API."""
    await setup_platform(
        hass,
        COVER_DOMAIN,
        tilt_only_shades("name-1"),
        bond_device_id="test-device-id",
        state={"counter1": 123},
    )

    with patch_bond_action() as mock_hold, patch_bond_device_state():
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER_TILT,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_hold.assert_called_once_with("test-device-id", Action.hold())
    expect(hass.states.get("cover.name_1").state).to_be(STATE_UNKNOWN)


@test
async def tilt_and_open(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that supports both tilt and open."""
    await setup_platform(
        hass,
        COVER_DOMAIN,
        tilt_shades("name-1"),
        bond_device_id="test-device-id",
        state={"open": False},
    )

    with patch_bond_action() as mock_open, patch_bond_device_state():
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER_TILT,
            {ATTR_ENTITY_ID: "cover.name_1"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_open.assert_called_once_with("test-device-id", Action.tilt_open())
    expect(hass.states.get("cover.name_1").state).to_equal(CoverState.CLOSED)


@test
async def update_reports_open_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that update command sets correct state when Bond API reports cover is open."""
    await setup_platform(hass, COVER_DOMAIN, shades("name-1"))

    with patch_bond_device_state(return_value={"open": 1}):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    expect(hass.states.get("cover.name_1").state).to_equal("open")


@test
async def update_reports_closed_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that update command sets correct state when Bond API reports cover is closed."""
    await setup_platform(hass, COVER_DOMAIN, shades("name-1"))

    with patch_bond_device_state(return_value={"open": 0}):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    expect(hass.states.get("cover.name_1").state).to_equal("closed")


@test
async def cover_available(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that available state is updated based on API errors."""
    await help_test_entity_available(
        hass, COVER_DOMAIN, shades("name-1"), "cover.name_1"
    )


@test
async def set_position_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Tests that set position cover command delegates to API."""
    await setup_platform(
        hass,
        COVER_DOMAIN,
        shades_with_position("name-1"),
        bond_device_id="test-device-id",
    )

    with (
        patch_bond_action() as mock_hold,
        patch_bond_device_state(return_value={"position": 0, "open": 1}),
    ):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: "cover.name_1", ATTR_POSITION: 100},
            blocking=True,
        )
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    mock_hold.assert_called_once_with("test-device-id", Action.set_position(0))
    entity_state = hass.states.get("cover.name_1")
    expect(entity_state.state).to_equal(CoverState.OPEN)
    expect(entity_state.attributes[ATTR_CURRENT_POSITION]).to_equal(100)

    with (
        patch_bond_action() as mock_hold,
        patch_bond_device_state(return_value={"position": 100, "open": 0}),
    ):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: "cover.name_1", ATTR_POSITION: 0},
            blocking=True,
        )
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    mock_hold.assert_called_once_with("test-device-id", Action.set_position(100))
    entity_state = hass.states.get("cover.name_1")
    expect(entity_state.state).to_equal(CoverState.CLOSED)
    expect(entity_state.attributes[ATTR_CURRENT_POSITION]).to_equal(0)

    with (
        patch_bond_action() as mock_hold,
        patch_bond_device_state(return_value={"position": 40, "open": 1}),
    ):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: "cover.name_1", ATTR_POSITION: 60},
            blocking=True,
        )
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    mock_hold.assert_called_once_with("test-device-id", Action.set_position(40))
    entity_state = hass.states.get("cover.name_1")
    expect(entity_state.state).to_equal(CoverState.OPEN)
    expect(entity_state.attributes[ATTR_CURRENT_POSITION]).to_equal(60)
