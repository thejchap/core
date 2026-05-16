"""Tests for Shelly cover platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import Mock, patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_CLOSE_COVER_TILT,
    SERVICE_OPEN_COVER,
    SERVICE_OPEN_COVER_TILT,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
    SERVICE_STOP_COVER,
    SERVICE_STOP_COVER_TILT,
    CoverState,
)
from homeassistant.components.shelly import (
    BLOCK_SLEEPING_PLATFORMS,
    PLATFORMS,
    RPC_SLEEPING_PLATFORMS,
)
from homeassistant.components.shelly.const import RPC_COVER_UPDATE_TIME_SEC
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.components.shelly import (
    init_integration,
    mock_polling_rpc_update,
    mutate_rpc_device_status,
)
from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

ROLLER_BLOCK_ID = 1

_MISSING = object()


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/setitem/delattr."""

    undo: list[Any] = []

    class _Patcher:
        def setattr(self, target: Any, name: str, value: Any) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            setattr(target, name, value)

        def setitem(self, mapping: Any, key: Any, value: Any) -> None:
            original = mapping.get(key, _MISSING)
            undo.append(("item", mapping, key, original))
            mapping[key] = value

        def delitem(self, mapping: Any, key: Any) -> None:
            original = mapping.get(key, _MISSING)
            undo.append(("item", mapping, key, original))
            mapping.pop(key, None)

        def delattr(self, target: Any, name: str) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            try:
                del target.__dict__[name]
            except (AttributeError, KeyError):
                with suppress(AttributeError):
                    delattr(target, name)

    try:
        yield _Patcher()
    finally:
        for kind, obj, key, original in reversed(undo):
            if kind == "attr":
                if original is _MISSING:
                    with suppress(AttributeError):
                        delattr(obj, key)
                else:
                    setattr(obj, key, original)
            elif original is _MISSING:
                obj.pop(key, None)
            else:
                obj[key] = original


@contextmanager
def _patch_platforms(platforms: list[Platform]) -> Generator[None]:
    """Only allow given platforms to be loaded."""
    with (
        patch(
            "homeassistant.components.shelly.PLATFORMS",
            list(set(PLATFORMS) & set(platforms)),
        ),
        patch(
            "homeassistant.components.shelly.BLOCK_SLEEPING_PLATFORMS",
            list(set(BLOCK_SLEEPING_PLATFORMS) & set(platforms)),
        ),
        patch(
            "homeassistant.components.shelly.RPC_SLEEPING_PLATFORMS",
            list(set(RPC_SLEEPING_PLATFORMS) & set(platforms)),
        ),
    ):
        yield


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@fixture
def fixture_platforms() -> Generator[None]:
    """Limit platforms under test."""
    with _patch_platforms([Platform.COVER]):
        yield


@test
async def block_device_services(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device cover services."""
    entity_id = "cover.test_name"
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.settings, "mode", "roller")
        await init_integration(hass, 1)

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 50},
            blocking=True,
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(50)

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.OPENING)

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.CLOSING)

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.CLOSED)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-roller_0")


@test
async def block_device_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device update."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device.blocks[ROLLER_BLOCK_ID], "rollerPos", 0)
        await init_integration(hass, 1)

        state = hass.states.get("cover.test_name")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.CLOSED)

        monkeypatch.setattr(
            mock_block_device.blocks[ROLLER_BLOCK_ID], "rollerPos", 100
        )
        mock_block_device.mock_update()
        state = hass.states.get("cover.test_name")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.OPEN)


@test
async def block_device_no_roller_blocks(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device without roller blocks."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device.blocks[ROLLER_BLOCK_ID], "type", None)
        await init_integration(hass, 1)

        expect(hass.states.get("cover.test_name")).to_be_none()


@test
async def rpc_device_services(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device cover services."""
    entity_id = "cover.test_name_test_cover_0"
    with _patches() as monkeypatch:
        await init_integration(hass, 2)

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 50},
            blocking=True,
        )

        mock_rpc_device.cover_set_position.assert_called_once_with(0, pos=50)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(50)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "state", "opening"
        )
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.cover_open.assert_called_once_with(0)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.OPENING)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "state", "closing"
        )
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.cover_close.assert_called_once_with(0)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.CLOSING)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "state", "closed"
        )
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.cover_stop.assert_called_once_with(0)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.CLOSED)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-cover:0")


@test
async def rpc_device_no_cover_keys(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC device without cover keys."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        await init_integration(hass, 2)

        expect(hass.states.get("cover.test_name_test_cover_0")).to_be_none()


@test
async def rpc_device_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC device update."""
    entity_id = "cover.test_name_test_cover_0"
    with _patches() as monkeypatch:
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "state", "closed"
        )
        await init_integration(hass, 2)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.CLOSED)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "state", "open"
        )
        mock_rpc_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.OPEN)


@test
async def rpc_device_no_position_control(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC device with no position control."""
    with _patches() as monkeypatch:
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "pos_control", False
        )
        await init_integration(hass, 2)

        state = hass.states.get("cover.test_name_test_cover_0")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.OPEN)


@test
async def rpc_cover_tilt(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC cover that supports tilt."""
    entity_id = "cover.test_name_test_cover_0"

    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["cover:0"]["slat"] = {"enable": True}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["cover:0"]["slat_pos"] = 0
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(0)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-cover:0")

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_TILT_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_TILT_POSITION: 50},
            blocking=True,
        )
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "slat_pos", 50
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.cover_set_position.assert_called_once_with(0, slat_pos=50)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(50)

        mock_rpc_device.cover_set_position.reset_mock()
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER_TILT,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "slat_pos", 100
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.cover_set_position.assert_called_once_with(0, slat_pos=100)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(100)

        mock_rpc_device.cover_set_position.reset_mock()
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER_TILT,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER_TILT,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "slat_pos", 10
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.cover_stop.assert_called_once_with(0)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_CURRENT_TILT_POSITION]).to_equal(10)


@test
async def rpc_cover_position_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC update_position while the cover is moving."""
    entity_id = "cover.test_name_test_cover_0"
    with _patches() as monkeypatch:
        await init_integration(hass, 2)

        # Set initial state to closing, position 50 set by update_cover_status mock
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "state", "closing"
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(CoverState.CLOSING)
        expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(50)

        # Simulate position updates during closing
        for position in range(40, -1, -10):
            mock_rpc_device.update_cover_status.reset_mock()
            await mock_polling_rpc_update(hass, freezer, RPC_COVER_UPDATE_TIME_SEC)

            mock_rpc_device.update_cover_status.assert_called_once_with(0)
            state = hass.states.get(entity_id)
            expect(state).to_be_truthy()
            expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(position)
            expect(state.state).to_equal(CoverState.CLOSING)

        # Simulate cover reaching final position
        mock_rpc_device.update_cover_status.reset_mock()
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "state", "closed"
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_CURRENT_POSITION]).to_equal(0)
        expect(state.state).to_equal(CoverState.CLOSED)

        # Ensure update_position does not call update_cover_status when the cover is not moving
        await mock_polling_rpc_update(hass, freezer, RPC_COVER_UPDATE_TIME_SEC)
        mock_rpc_device.update_cover_status.assert_not_called()


@test
async def rpc_not_initialized_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test update not called when device is not initialized."""
    entity_id = "cover.test_name_test_cover_0"
    with _patches() as monkeypatch:
        await init_integration(hass, 2)

        # Set initial state to closing
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "state", "closing"
        )
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "current_pos", 40
        )

        # mock device not initialized (e.g. disconnected)
        monkeypatch.setattr(mock_rpc_device, "initialized", False)
        mock_rpc_device.mock_update()

        # wait for update interval to allow update_position to call update_cover_status
        await mock_polling_rpc_update(hass, freezer, RPC_COVER_UPDATE_TIME_SEC)

        mock_rpc_device.update_cover_status.assert_not_called()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)
