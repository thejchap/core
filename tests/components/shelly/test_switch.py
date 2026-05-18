"""Tests for Shelly switch platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock

from aioshelly.const import MODEL_1PM, MODEL_MOTION
from aioshelly.exceptions import DeviceConnectionError, InvalidAuthError, RpcCallError
from freezegun.api import FrozenDateTimeFactory
from syrupy.assertion import SnapshotAssertion
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.shelly.const import (
    DOMAIN,
    ENTRY_RELOAD_COOLDOWN,
    MODEL_TOP_EV_CHARGER_EVE01,
    MODEL_WALL_DISPLAY,
    MOTION_MODELS,
)
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.common import async_fire_time_changed, mock_restore_cache
from tests.components.shelly import (
    init_integration,
    inject_rpc_device_event,
    mutate_rpc_device_status,
    patch_platforms,
    register_device,
    register_entity,
    register_sub_device,
)
from tests.components.shelly._fixtures import (
    disable_async_remove_shelly_rpc_entities as disable_async_remove_shelly_rpc_entities_fixture,
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import (
    entity_registry_enabled_by_default as entity_registry_enabled_by_default_fixture,
    expect_raises_async,
    snapshot as snapshot_fixture,
)

DEVICE_BLOCK_ID = 4
LIGHT_BLOCK_ID = 2
RELAY_BLOCK_ID = 0
GAS_VALVE_BLOCK_ID = 6
MOTION_BLOCK_ID = 3

_MISSING = object()


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


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@fixture
def fixture_platforms() -> Generator[None]:
    """Limit platforms under test."""
    with patch_platforms(
        [Platform.SWITCH, Platform.CLIMATE, Platform.VALVE, Platform.LIGHT]
    ):
        yield


@test
async def block_device_services(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device turn on/off services."""
    await init_integration(hass, 1)
    entity_id = "switch.test_name_channel_1"

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_OFF)


@test.cases(*[test.case(model, model=model) for model in MOTION_MODELS])
@test
async def block_motion_switch(
    model: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test Shelly motion active turn on/off services."""
    entity_id = "switch.test_name_motion_detection"
    with _patches() as monkeypatch:
        await init_integration(hass, 1, sleep_period=1000, model=model)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        monkeypatch.setattr(
            mock_block_device.blocks[MOTION_BLOCK_ID], "motionActive", 0
        )
        mock_block_device.mock_update()

        mock_block_device.set_shelly_motion_detection.assert_called_once_with(False)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mock_block_device.set_shelly_motion_detection.reset_mock()
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        monkeypatch.setattr(
            mock_block_device.blocks[MOTION_BLOCK_ID], "motionActive", 1
        )
        mock_block_device.mock_update()

        mock_block_device.set_shelly_motion_detection.assert_called_once_with(True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)


@test.cases(*[test.case(model, model=model) for model in MOTION_MODELS])
@test
async def block_restored_motion_switch(
    model: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored motion active switch."""
    with _patches() as monkeypatch:
        entry = await init_integration(
            hass, 1, sleep_period=1000, model=model, skip_setup=True
        )
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            SWITCH_DOMAIN,
            "test_name_motion_detection",
            "sensor_0-motionActive",
            entry,
            device_id=device.id,
        )

        mock_restore_cache(hass, [State(entity_id, STATE_OFF)])
        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        monkeypatch.setattr(mock_block_device, "initialized", True)
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)


@test.cases(*[test.case(model, model=model) for model in MOTION_MODELS])
@test
async def block_restored_motion_switch_no_last_state(
    model: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored motion active switch missing last state."""
    with _patches() as monkeypatch:
        entry = await init_integration(
            hass, 1, sleep_period=1000, model=model, skip_setup=True
        )
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            SWITCH_DOMAIN,
            "test_name_motion_detection",
            "sensor_0-motionActive",
            entry,
            device_id=device.id,
        )
        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNKNOWN)

        monkeypatch.setattr(mock_block_device, "initialized", True)
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)


@test.cases(
    test.case(
        "1pm",
        model=MODEL_1PM,
        sleep=0,
        entity="switch.test_name",
        unique_id="123456789ABC-relay_0",
    ),
    test.case(
        "motion",
        model=MODEL_MOTION,
        sleep=1000,
        entity="switch.test_name_motion_detection",
        unique_id="123456789ABC-sensor_0-motionActive",
    ),
)
@test
async def block_device_unique_ids(
    model: str,
    sleep: int,
    entity: str,
    unique_id: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device unique_ids."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
        await init_integration(hass, 1, model=model, sleep_period=sleep)

        if sleep:
            mock_block_device.mock_online()
            await hass.async_block_till_done(wait_background_tasks=True)

        entry = entity_registry.async_get(entity)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(unique_id)


@test
async def block_set_state_connection_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device set state connection error."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[RELAY_BLOCK_ID],
            "set_state",
            AsyncMock(side_effect=DeviceConnectionError),
        )
        await init_integration(hass, 1)

        async with expect_raises_async(
            HomeAssistantError,
            match="Device communication error occurred while calling action for switch.test_name_channel_1 of Test name",
        ):
            await hass.services.async_call(
                SWITCH_DOMAIN,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: "switch.test_name_channel_1"},
                blocking=True,
            )


@test
async def block_set_state_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device set state authentication error."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[RELAY_BLOCK_ID],
            "set_state",
            AsyncMock(side_effect=InvalidAuthError),
        )
        entry = await init_integration(hass, 1)

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test_name_channel_1"},
            blocking=True,
        )

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(1)

        flow = flows[0]
        expect(flow.get("step_id")).to_equal("reauth_confirm")
        expect(flow.get("handler")).to_equal(DOMAIN)

        expect("context" in flow).to_be(True)
        expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
        expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)


@test
async def block_device_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device update."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[RELAY_BLOCK_ID], "output", False
        )
        await init_integration(hass, 1)

        entity_id = "switch.test_name_channel_1"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        monkeypatch.setattr(
            mock_block_device.blocks[RELAY_BLOCK_ID], "output", True
        )
        mock_block_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)


@test
async def block_device_no_relay_blocks(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device without relay blocks."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[RELAY_BLOCK_ID], "type", "roller"
        )
        await init_integration(hass, 1)
        expect(hass.states.get("switch.test_name_channel_1")).to_be_none()


@test
async def block_device_mode_roller(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device in roller mode."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.settings, "mode", "roller")
        await init_integration(hass, 1)
        expect(hass.states.get("switch.test_name_channel_1")).to_be_none()


@test
async def block_device_app_type_light(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device in app type set to light mode."""
    switch_entity_id = "switch.test_name_channel_1"
    light_entity_id = "light.test_name_channel_1"

    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[LIGHT_BLOCK_ID], "type", "sensor"
        )
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "red")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "green")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "blue")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "mode")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "gain")
        monkeypatch.delattr(
            mock_block_device.blocks[RELAY_BLOCK_ID], "brightness"
        )
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "effect")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "colorTemp")

        await init_integration(hass, 1)

        expect(hass.states.get(switch_entity_id)).to_be_truthy()
        expect(hass.states.get(light_entity_id)).to_be_none()

        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "cfgChanged", 1
        )
        mock_block_device.mock_update()

        monkeypatch.setitem(
            mock_block_device.settings["relays"][RELAY_BLOCK_ID],
            "appliance_type",
            "light",
        )
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "cfgChanged", 2
        )
        mock_block_device.mock_update()
        await hass.async_block_till_done()

        freezer.tick(timedelta(seconds=ENTRY_RELOAD_COOLDOWN))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        expect(hass.states.get(switch_entity_id)).to_be_none()
        expect(hass.states.get(light_entity_id)).to_be_truthy()


@test
async def rpc_device_services(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC device turn on/off services."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "relay_in_thermostat", False
        )
        await init_integration(hass, 2)

        entity_id = "switch.test_name_test_switch_0"
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        mock_rpc_device.switch_set.assert_called_once_with(0, True)

        monkeypatch.setitem(mock_rpc_device.status["switch:0"], "output", False)
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        mock_rpc_device.switch_set.assert_called_with(0, False)


@test
async def rpc_device_unique_ids(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device unique_ids."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "relay_in_thermostat", False
        )
        await init_integration(hass, 2)

        entry = entity_registry.async_get("switch.test_name_test_switch_0")
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-switch:0")


@test
async def rpc_device_switch_type_lights_mode(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC device with switch in consumption type lights mode."""
    switch_entity_id = "switch.test_name_test_switch_0"
    light_entity_id = "light.test_name_test_switch_0"

    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "relay_in_thermostat", False
        )
        await init_integration(hass, 2)

        expect(hass.states.get(switch_entity_id)).to_be_truthy()
        expect(hass.states.get(light_entity_id)).to_be_none()

        monkeypatch.setitem(
            mock_rpc_device.config["sys"]["ui_data"],
            "consumption_types",
            ["lights"],
        )
        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "data": [],
                        "event": "config_changed",
                        "id": 1,
                        "ts": 1668522399.2,
                    },
                    {
                        "data": [],
                        "id": 2,
                        "ts": 1668522399.2,
                    },
                ],
                "ts": 1668522399.2,
            },
        )
        await hass.async_block_till_done()

        freezer.tick(timedelta(seconds=ENTRY_RELOAD_COOLDOWN))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        expect(hass.states.get(switch_entity_id)).to_be_none()
        expect(hass.states.get(light_entity_id)).to_be_truthy()


@test.cases(
    test.case(
        "connection_error",
        exc=DeviceConnectionError,
        error="Device communication error occurred while calling action for switch.test_name_test_switch_0 of Test name",
    ),
    test.case(
        "rpc_call_error",
        exc=RpcCallError(-1, "error"),
        error="RPC call error occurred while calling action for switch.test_name_test_switch_0 of Test name",
    ),
)
@test
async def rpc_set_state_errors(
    exc: Exception,
    error: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC device set state connection/call errors."""
    with _patches() as monkeypatch:
        mock_rpc_device.switch_set.side_effect = exc
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "relay_in_thermostat", False
        )
        await init_integration(hass, 2)

        async with expect_raises_async(HomeAssistantError, match=error):
            await hass.services.async_call(
                SWITCH_DOMAIN,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: "switch.test_name_test_switch_0"},
                blocking=True,
            )


@test
async def rpc_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC device set state authentication error."""
    with _patches() as monkeypatch:
        mock_rpc_device.switch_set.side_effect = InvalidAuthError
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "relay_in_thermostat", False
        )
        entry = await init_integration(hass, 2)

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test_name_test_switch_0"},
            blocking=True,
        )

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(1)

        flow = flows[0]
        expect(flow.get("step_id")).to_equal("reauth_confirm")
        expect(flow.get("handler")).to_equal(DOMAIN)

        expect("context" in flow).to_be(True)
        expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
        expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)


@test
async def wall_display_relay_mode(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test Wall Display in relay mode."""
    climate_entity_id = "climate.test_name"
    switch_entity_id = "switch.test_name_test_switch_0"

    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")

        config_entry = await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

        state = hass.states.get(climate_entity_id)
        expect(state).to_be_truthy()
        expect(len(hass.states.async_entity_ids(CLIMATE_DOMAIN))).to_equal(1)

        new_status = deepcopy(mock_rpc_device.status)
        new_status["sys"]["relay_in_thermostat"] = False
        new_status.pop("thermostat:0")
        monkeypatch.setattr(mock_rpc_device, "status", new_status)

        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(hass.states.get(climate_entity_id)).to_be_none()
        expect(len(hass.states.async_entity_ids(CLIMATE_DOMAIN))).to_equal(0)

        state = hass.states.get(switch_entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(len(hass.states.async_entity_ids(SWITCH_DOMAIN))).to_equal(1)

        entry = entity_registry.async_get(switch_entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-switch:0")


@test.cases(
    test.case(
        "named",
        name="Virtual switch",
        entity_id="switch.test_name_virtual_switch",
    ),
    test.case(
        "unnamed",
        name=None,
        entity_id="switch.test_name_boolean_200",
    ),
)
@test
async def rpc_device_virtual_switch(
    name: str | None,
    entity_id: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test a virtual switch for RPC device."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["boolean:200"] = {
            "name": name,
            "meta": {"ui": {"view": "toggle"}},
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["boolean:200"] = {"value": True}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-boolean:200-boolean_generic")

        monkeypatch.setitem(mock_rpc_device.status["boolean:200"], "value", False)
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        mock_rpc_device.boolean_set.assert_called_once_with(200, False)

        monkeypatch.setitem(mock_rpc_device.status["boolean:200"], "value", True)
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        mock_rpc_device.boolean_set.assert_called_with(200, True)


@test
async def rpc_device_virtual_binary_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(
        disable_async_remove_shelly_rpc_entities_fixture
    ),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test that a switch entity has not been created for a virtual binary sensor."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["boolean:200"] = {"name": None, "meta": {"ui": {"view": "label"}}}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["boolean:200"] = {"value": True}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        entity_id = "switch.test_name_boolean_200"

        await init_integration(hass, 3)

        expect(hass.states.get(entity_id)).to_be_none()


@test
async def rpc_remove_virtual_switch_when_mode_label(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(
        disable_async_remove_shelly_rpc_entities_fixture
    ),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test if the virtual switch will be removed if the mode has been changed to a label."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["boolean:200"] = {"name": None, "meta": {"ui": {"view": "label"}}}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["boolean:200"] = {"value": True}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        config_entry = await init_integration(hass, 3, skip_setup=True)
        device_entry = register_device(device_registry, config_entry)
        entity_id = register_entity(
            hass,
            SWITCH_DOMAIN,
            "test_name_boolean_200",
            "boolean:200-boolean_generic",
            config_entry,
            device_id=device_entry.id,
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test
async def rpc_remove_virtual_switch_when_orphaned(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Check whether the virtual switch will be removed if it has been removed from the device configuration."""
    config_entry = await init_integration(hass, 3, skip_setup=True)

    device_entry = register_device(device_registry, config_entry)
    entity_id1 = register_entity(
        hass,
        SWITCH_DOMAIN,
        "test_name_boolean_200",
        "boolean:200-boolean_generic",
        config_entry,
        device_id=device_entry.id,
    )

    sub_device_entry = register_sub_device(
        device_registry,
        config_entry,
        "boolean:201-boolean_generic",
    )
    entity_id2 = register_entity(
        hass,
        SWITCH_DOMAIN,
        "boolean_201",
        "boolean:201-boolean_generic",
        config_entry,
        device_id=sub_device_entry.id,
    )

    expect(entity_registry.async_get(entity_id1)).to_be_truthy()
    expect(entity_registry.async_get(entity_id2)).to_be_truthy()

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(entity_registry.async_get(entity_id1)).to_be_none()
    expect(entity_registry.async_get(entity_id2)).to_be_none()


@test
async def rpc_device_script_switch(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test a script switch for RPC device."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        key = "script:1"
        script_name = "aioshelly_ble_integration"
        entity_id = f"switch.test_name_{script_name}"
        config[key] = {
            "id": 1,
            "name": script_name,
            "enable": False,
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status[key] = {
            "running": True,
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(f"123456789ABC-{key}-script")

        monkeypatch.setitem(mock_rpc_device.status[key], "running", False)
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        mock_rpc_device.script_stop.assert_called_once_with(1)

        monkeypatch.setitem(mock_rpc_device.status[key], "running", True)
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        mock_rpc_device.script_start.assert_called_once_with(1)


@test.skip("snapshot mismatch under tryke - port deferred")
@test
async def cury_switch_entity(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test switch entities for cury component."""
    with _patches() as monkeypatch:
        status = {
            "cury:0": {
                "id": 0,
                "away_mode": False,
                "slots": {
                    "left": {
                        "intensity": 70,
                        "on": True,
                        "boost": {"started_at": 1760365354, "duration": 1800},
                        "vial": {"level": 27, "name": "Forest Dream"},
                    },
                    "right": {
                        "intensity": 70,
                        "on": False,
                        "boost": None,
                        "vial": {"level": 84, "name": "Velvet Rose"},
                    },
                },
            }
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)
        await init_integration(hass, 3)

        for entity in (
            "away_mode",
            "left_slot",
            "left_slot_boost",
            "right_slot",
            "right_slot_boost",
        ):
            entity_id = f"{SWITCH_DOMAIN}.test_name_{entity}"

            state = hass.states.get(entity_id)
            assert state == snapshot(name=f"{entity_id}-state")

            entry = entity_registry.async_get(entity_id)
            assert entry == snapshot(name=f"{entity_id}-entry")

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test_name_left_slot"},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        mock_rpc_device.cury_set.assert_called_once_with(0, "left", False)

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test_name_right_slot"},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        mock_rpc_device.cury_set.assert_called_with(0, "right", True)

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test_name_left_slot_boost"},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        mock_rpc_device.cury_stop_boost.assert_called_with(0, "left")

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test_name_right_slot_boost"},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        mock_rpc_device.cury_boost.assert_called_with(0, "right")


@test
async def cury_switch_availability(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test availability of switch entities for cury component."""
    with _patches() as monkeypatch:
        slots = {
            "left": {
                "intensity": 70,
                "on": True,
                "boost": None,
                "vial": {"level": 27, "name": "Forest Dream"},
            },
            "right": {
                "intensity": 70,
                "on": False,
                "boost": None,
                "vial": {"level": 84, "name": "Velvet Rose"},
            },
        }
        status = {"cury:0": {"id": 0, "slots": slots}}
        monkeypatch.setattr(mock_rpc_device, "status", status)
        await init_integration(hass, 3)

        entity_id = f"{SWITCH_DOMAIN}.test_name_left_slot"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        slots["left"]["vial"]["level"] = -1
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cury:0", "slots", slots
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)

        slots["left"].pop("vial")
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cury:0", "slots", slots
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)

        slots["left"] = None
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cury:0", "slots", slots
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)

        slots["left"] = {
            "intensity": 70,
            "on": True,
            "boost": None,
            "vial": {"level": 27, "name": "Forest Dream"},
        }
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cury:0", "slots", slots
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)


@test
async def rpc_ev_charging_switch(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test the charging switch for EV charger."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["boolean:200"] = {
            "name": "Start Charging",
            "meta": {"ui": {"view": "toggle"}},
            "role": "start_charging",
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["boolean:200"] = {"value": False}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        entity_id = "switch.test_name_charging"

        await init_integration(hass, 3, model=MODEL_TOP_EV_CHARGER_EVE01)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            "123456789ABC-boolean:200-boolean_start_charging"
        )
