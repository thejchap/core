"""Tests for Shelly event platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import Mock, patch

from aioshelly.const import MODEL_I3
from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components.event import (
    ATTR_EVENT_TYPE,
    ATTR_EVENT_TYPES,
    DOMAIN as EVENT_DOMAIN,
    EventDeviceClass,
)
from homeassistant.components.shelly import (
    BLOCK_SLEEPING_PLATFORMS,
    PLATFORMS,
    RPC_SLEEPING_PLATFORMS,
)
from homeassistant.const import ATTR_DEVICE_CLASS, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.components.shelly import (
    init_integration,
    inject_rpc_device_event,
    register_entity,
)
from tests.components.shelly._fixtures import (
    MOCK_BLOCKS,
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

_MISSING = object()

DEVICE_BLOCK_ID = 4

UNORDERED_EVENT_TYPES = unordered(
    ["double", "long", "long_single", "single", "single_long", "triple"]
)


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/setitem/delattr/delitem."""

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
    with _patch_platforms([Platform.EVENT]):
        yield


@test
async def rpc_button(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device event."""
    await init_integration(hass, 2)
    entity_id = "event.test_name_test_input_0"

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_EVENT_TYPES)).to_equal(
        unordered(
            [
                "btn_down",
                "btn_up",
                "double_push",
                "long_push",
                "single_push",
                "triple_push",
            ]
        )
    )
    expect(state.attributes.get(ATTR_EVENT_TYPE)).to_be_none()
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(EventDeviceClass.BUTTON)

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-input:0")

    with _patches() as monkeypatch:
        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "event": "single_push",
                        "id": 0,
                        "ts": 1668522399.2,
                    }
                ],
                "ts": 1668522399.2,
            },
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes.get(ATTR_EVENT_TYPE)).to_equal("single_push")


@test.skip("snapshot test - port deferred")
async def rpc_script_1_event() -> None:
    """Stub for test_rpc_script_1_event (port deferred)."""


@test.skip("snapshot test - port deferred")
async def rpc_script_2_event() -> None:
    """Stub for test_rpc_script_2_event (port deferred)."""


@test.skip("snapshot test - port deferred")
async def rpc_script_ble_event() -> None:
    """Stub for test_rpc_script_ble_event (port deferred)."""


@test
async def rpc_event_removal(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC event entity is removed due to removal_condition."""
    entity_id = register_entity(hass, EVENT_DOMAIN, "test_name_input_0", "input:0")

    expect(entity_registry.async_get(entity_id)).to_be_truthy()

    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_rpc_device.config, "input:0", {"id": 0, "type": "switch"}
        )
        await init_integration(hass, 2)

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test
async def block_event(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device event."""
    await init_integration(hass, 1)
    # num_outputs is 2, device name and channel name is used
    entity_id = "event.test_name_channel_1_input"

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_EVENT_TYPES)).to_equal(
        unordered(["single", "long"])
    )
    expect(state.attributes.get(ATTR_EVENT_TYPE)).to_be_none()
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(EventDeviceClass.BUTTON)

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-relay_0-1")

    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID],
            "sensor_ids",
            {"inputEvent": "L", "inputEventCnt": 0},
        )
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "inputEvent", "L"
        )
        mock_block_device.mock_update()
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes.get(ATTR_EVENT_TYPE)).to_equal("long")


@test
async def block_event_single_output(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device event when num_outputs is 1."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
        await init_integration(hass, 1)

        expect(hass.states.get("event.test_name_input")).to_be_truthy()


@test
async def block_event_custom_name(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device event with custom name."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "relays",
            [
                {"name": "test channel", "btn_type": "momentary"},
                {"btn_type": "toggle"},
            ],
        )
        await init_integration(hass, 1)
        # num_outputs is 2, device name and custom name is used
        expect(hass.states.get("event.test_channel_input")).to_be_truthy()


@test
async def block_event_custom_name_single_output(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device event with custom name when num_outputs is 1."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
        monkeypatch.setitem(
            mock_block_device.settings,
            "relays",
            [
                {"name": "test channel", "btn_type": "momentary"},
                {"btn_type": "toggle"},
            ],
        )
        await init_integration(hass, 1)

        expect(hass.states.get("event.test_name_input")).to_be_truthy()


@test
async def block_event_shix3_1(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device event for SHIX3-1."""
    blocks = deepcopy(MOCK_BLOCKS)
    blocks[0] = Mock(
        sensor_ids={
            "inputEvent": "S",
            "inputEventCnt": 2,
        },
        channel="0",
        type="input",
        description="input_0",
    )
    blocks[1] = Mock(
        sensor_ids={
            "inputEvent": "S",
            "inputEventCnt": 2,
        },
        channel="1",
        type="input",
        description="input_1",
    )
    blocks[2] = Mock(
        sensor_ids={
            "inputEvent": "S",
            "inputEventCnt": 2,
        },
        channel="2",
        type="input",
        description="input_2",
    )
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device, "blocks", blocks)
        monkeypatch.delitem(mock_block_device.settings, "relays")
        await init_integration(hass, 1, model=MODEL_I3)

        state = hass.states.get("event.test_name_tv_leds")
        expect(state).to_be_truthy()
        expect(state.attributes.get(ATTR_EVENT_TYPES)).to_equal(UNORDERED_EVENT_TYPES)

        state = hass.states.get("event.test_name_tv_spots")
        expect(state).to_be_truthy()
        expect(state.attributes.get(ATTR_EVENT_TYPES)).to_equal(UNORDERED_EVENT_TYPES)

        state = hass.states.get("event.test_name_input_3")
        expect(state).to_be_truthy()
        expect(state.attributes.get(ATTR_EVENT_TYPES)).to_equal(UNORDERED_EVENT_TYPES)
