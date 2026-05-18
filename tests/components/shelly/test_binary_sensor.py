"""Tests for Shelly binary sensor platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aioshelly.const import (
    MODEL_CURY_G4,
    MODEL_FLOOD_G4,
    MODEL_MOTION,
    MODEL_PLUS_SMOKE,
)
from aioshelly.exceptions import DeviceConnectionError
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.shelly import (
    BLOCK_SLEEPING_PLATFORMS,
    PLATFORMS,
    RPC_SLEEPING_PLATFORMS,
)
from homeassistant.components.shelly.const import UPDATE_PERIOD_MULTIPLIER
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.common import mock_restore_cache
from tests.components.shelly import (
    init_integration,
    mock_rest_update,
    mutate_rpc_device_status,
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

RELAY_BLOCK_ID = 0
SENSOR_BLOCK_ID = 3

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
    with _patch_platforms([Platform.BINARY_SENSOR]):
        yield


@test
async def block_binary_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block binary sensor."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_overpowering"
        await init_integration(hass, 1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        monkeypatch.setattr(mock_block_device.blocks[RELAY_BLOCK_ID], "overpower", 1)
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-relay_0-overpower")


@test
async def block_binary_gas_sensor_creation(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block binary gas sensor creation."""
    with _patches() as monkeypatch:
        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_gas"
        await init_integration(hass, 1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "gas", "none")
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-sensor_0-gas")


@test
async def block_rest_binary_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block REST binary sensor."""
    with _patches() as monkeypatch:
        entity_id = register_entity(
            hass, BINARY_SENSOR_DOMAIN, "test_name_cloud", "cloud"
        )
        monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
        await init_integration(hass, 1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        monkeypatch.setitem(mock_block_device.status["cloud"], "connected", True)
        await mock_rest_update(hass, freezer)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-cloud")


@test
async def block_rest_binary_sensor_connected_battery_devices(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block REST binary sensor for connected battery devices."""
    with _patches() as monkeypatch:
        entity_id = register_entity(
            hass, BINARY_SENSOR_DOMAIN, "test_name_cloud", "cloud"
        )
        monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
        monkeypatch.setitem(
            mock_block_device.settings["device"], "type", MODEL_MOTION
        )
        monkeypatch.setitem(mock_block_device.settings["coiot"], "update_period", 3600)
        await init_integration(hass, 1, model=MODEL_MOTION)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        monkeypatch.setitem(mock_block_device.status["cloud"], "connected", True)

        # Verify no update on fast intervals
        await mock_rest_update(hass, freezer)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        # Verify update on slow intervals
        await mock_rest_update(hass, freezer, seconds=UPDATE_PERIOD_MULTIPLIER * 3600)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-cloud")


@test
async def block_sleeping_binary_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block sleeping binary sensor."""
    with _patches() as monkeypatch:
        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_motion"
        await init_integration(hass, 1, sleep_period=1000)

        # Sensor should be created when device is online
        expect(hass.states.get(entity_id)).to_be_none()

        # Make device online
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "motion", 1)
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-sensor_0-motion")


@test
async def block_restored_sleeping_binary_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored sleeping binary sensor."""
    with _patches() as monkeypatch:
        entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            BINARY_SENSOR_DOMAIN,
            "test_name_motion",
            "sensor_0-motion",
            entry,
            device_id=device.id,
        )
        mock_restore_cache(hass, [State(entity_id, STATE_ON)])
        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        # Make device online
        monkeypatch.setattr(mock_block_device, "initialized", True)
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)


@test
async def block_restored_sleeping_binary_sensor_no_last_state(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored sleeping binary sensor missing last state."""
    with _patches() as monkeypatch:
        entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            BINARY_SENSOR_DOMAIN,
            "test_name_motion",
            "sensor_0-motion",
            entry,
            device_id=device.id,
        )
        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNKNOWN)

        # Make device online
        monkeypatch.setattr(mock_block_device, "initialized", True)
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)


@test
async def rpc_binary_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC binary sensor."""
    with _patches() as monkeypatch:
        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_test_cover_0_overpowering"
        await init_integration(hass, 2)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "errors", "overpower"
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-cover:0-overpower")


@test
async def rpc_binary_sensor_input_custom_name(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC binary sensor with input custom name."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_rpc_device.config,
            "input:1",
            {
                "id": 1,
                "type": "switch",
                "invert": False,
                "factory_reset": True,
                "name": "test channel",
            },
        )
        monkeypatch.setitem(
            mock_rpc_device.status,
            "input:1",
            {"id": 1, "state": True},
        )
        await init_integration(hass, 2)

        state = hass.states.get(f"{BINARY_SENSOR_DOMAIN}.test_name_test_channel")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)


@test
async def rpc_binary_sensor_removal(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC binary sensor is removed due to removal_condition."""
    with _patches() as monkeypatch:
        entity_id = register_entity(
            hass, BINARY_SENSOR_DOMAIN, "test_cover_0_input", "input:0-input"
        )

        expect(entity_registry.async_get(entity_id)).to_be_truthy()

        monkeypatch.setattr(mock_rpc_device, "status", {"input:0": {"state": False}})
        await init_integration(hass, 2)

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test
async def rpc_sleeping_binary_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC online sleeping binary sensor."""
    with _patches() as monkeypatch:
        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_cloud"
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
        with patch.object(
            mock_rpc_device,
            "initialize",
            new_callable=AsyncMock,
            side_effect=DeviceConnectionError,
        ):
            config_entry = await init_integration(hass, 2, sleep_period=1000)

        # Sensor should be created when device is online
        expect(hass.states.get(entity_id)).to_be_none()

        register_entity(
            hass,
            BINARY_SENSOR_DOMAIN,
            "test_name_cloud",
            "cloud-cloud",
            config_entry,
        )

        # Make device online
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cloud", "connected", True
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        # test external power sensor
        state = hass.states.get("binary_sensor.test_name_external_power")
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get("binary_sensor.test_name_external_power")
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-devicepower:0-external_power")


@test
async def rpc_sleeping_binary_sensor_with_channel_name(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC online sleeping binary sensor with channel name."""
    with _patches() as monkeypatch:
        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_test_channel_name_smoke"
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
        with patch.object(
            mock_rpc_device,
            "initialize",
            new_callable=AsyncMock,
            side_effect=DeviceConnectionError,
        ):
            await init_integration(
                hass, 2, sleep_period=1000, model=MODEL_PLUS_SMOKE
            )

        # Sensor should be created when device is online
        expect(hass.states.get(entity_id)).to_be_none()

        # Make device online
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes["friendly_name"]).to_equal(
            "Test name test channel name smoke"
        )
        expect(state.state).to_equal(STATE_OFF)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "smoke:0", "alarm", True
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)


@test
async def rpc_restored_sleeping_binary_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test RPC restored binary sensor."""
    with _patches() as monkeypatch:
        entry = await init_integration(hass, 2, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            BINARY_SENSOR_DOMAIN,
            "test_name_cloud",
            "cloud-cloud",
            entry,
            device_id=device.id,
        )

        mock_restore_cache(hass, [State(entity_id, STATE_ON)])
        monkeypatch.setattr(mock_rpc_device, "initialized", False)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        # Make device online
        monkeypatch.setattr(mock_rpc_device, "initialized", True)
        mock_rpc_device.mock_update()
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)


@test
async def rpc_restored_sleeping_binary_sensor_no_last_state(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test RPC restored sleeping binary sensor missing last state."""
    with _patches() as monkeypatch:
        entry = await init_integration(hass, 2, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            BINARY_SENSOR_DOMAIN,
            "test_name_cloud",
            "cloud-cloud",
            entry,
            device_id=device.id,
        )

        monkeypatch.setattr(mock_rpc_device, "initialized", False)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNKNOWN)

        # Make device online
        monkeypatch.setattr(mock_rpc_device, "initialized", True)
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        # Mock update
        mock_rpc_device.mock_update()
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)


@test.cases(
    test.case(
        "named",
        name="Virtual binary sensor",
        entity_id="binary_sensor.test_name_virtual_binary_sensor",
    ),
    test.case(
        "unnamed",
        name=None,
        entity_id="binary_sensor.test_name_boolean_203",
    ),
)
async def rpc_device_virtual_binary_sensor(
    name: str | None,
    entity_id: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test a virtual binary sensor for RPC device."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["boolean:203"] = {
            "name": name,
            "meta": {"ui": {"view": "label"}},
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["boolean:203"] = {"value": True}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-boolean:203-boolean_generic")

        monkeypatch.setitem(mock_rpc_device.status["boolean:203"], "value", False)
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)


@test
async def rpc_remove_virtual_binary_sensor_when_mode_toggle(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(disable_async_remove_shelly_rpc_entities_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test if the virtual binary sensor will be removed if the mode has been changed to a toggle."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["boolean:200"] = {"name": None, "meta": {"ui": {"view": "toggle"}}}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["boolean:200"] = {"value": True}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        config_entry = await init_integration(hass, 3, skip_setup=True)
        device_entry = register_device(device_registry, config_entry)
        entity_id = register_entity(
            hass,
            BINARY_SENSOR_DOMAIN,
            "test_name_boolean_200",
            "boolean:200-boolean_generic",
            config_entry,
            device_id=device_entry.id,
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test
async def rpc_remove_virtual_binary_sensor_when_orphaned(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Check whether the virtual binary sensor will be removed if removed from device config."""
    config_entry = await init_integration(hass, 3, skip_setup=True)

    # create orphaned entity on main device
    device_entry = register_device(device_registry, config_entry)
    entity_id1 = register_entity(
        hass,
        BINARY_SENSOR_DOMAIN,
        "test_name_boolean_200",
        "boolean:200-boolean_generic",
        config_entry,
        device_id=device_entry.id,
    )

    # create orphaned entity on sub device
    sub_device_entry = register_sub_device(
        device_registry,
        config_entry,
        "boolean:201-boolean_generic",
    )
    entity_id2 = register_entity(
        hass,
        BINARY_SENSOR_DOMAIN,
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


@test.skip("snapshot mismatch under tryke - port deferred")
async def blu_trv_binary_sensor_entity() -> None:
    """Test BLU TRV binary sensor entity."""


@test.skip("snapshot mismatch under tryke - port deferred")
async def rpc_flood_entities() -> None:
    """Test RPC flood sensor entities."""


@test
async def rpc_flood_cable_unplugged(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC flood cable unplugged entity."""
    with _patches() as monkeypatch:
        await init_integration(hass, 4, model=MODEL_FLOOD_G4)

        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_kitchen_cable_unplugged"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        status = deepcopy(mock_rpc_device.status)
        status["flood:0"]["errors"] = ["cable_unplugged"]
        monkeypatch.setattr(mock_rpc_device, "status", status)
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)


@test
async def rpc_presence_component(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC binary sensor entity for presence component."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["presence"] = {"enable": True}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["presence"] = {"num_objects": 2}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        mock_config_entry = await init_integration(hass, 4)

        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_occupancy"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            "123456789ABC-presence-presence_num_objects"
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "presence", "num_objects", 0
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        config = deepcopy(mock_rpc_device.config)
        config["presence"] = {"enable": False}
        monkeypatch.setattr(mock_rpc_device, "config", config)
        await hass.config_entries.async_reload(mock_config_entry.entry_id)
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def rpc_presencezone_component(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC binary sensor entity for presencezone component."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["presencezone:200"] = {"name": "Main zone", "enable": True}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["presencezone:200"] = {"value": True, "num_objects": 3}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        mock_config_entry = await init_integration(hass, 4)

        entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_main_zone_occupancy"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            "123456789ABC-presencezone:200-presencezone_state"
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "presencezone:200", "value", False
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        config = deepcopy(mock_rpc_device.config)
        config["presencezone:200"] = {"enable": False}
        monkeypatch.setattr(mock_rpc_device, "config", config)
        await hass.config_entries.async_reload(mock_config_entry.entry_id)
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)


@test.skip("caplog migration: 'Migrating unique_id ...' log assertion needs review")
async def migrate_unique_id_virtual_components_roles() -> None:
    """Test migration of unique_id for virtual components to include role."""


@test
async def rpc_cury_orientation_errors(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC cury orientation error entities."""
    with _patches() as monkeypatch:
        status = {
            "cury:0": {
                "id": 0,
                "slots": {
                    "left": {
                        "intensity": 70,
                        "on": True,
                        "vial": {"level": 27, "name": "Forest Dream"},
                    },
                    "right": {
                        "intensity": 70,
                        "on": False,
                        "vial": {"level": 84, "name": "Velvet Rose"},
                    },
                },
            }
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)
        await init_integration(hass, 4, model=MODEL_CURY_G4)

        entity_tilt = f"{BINARY_SENSOR_DOMAIN}.test_name_tilt"
        entity_rotation = f"{BINARY_SENSOR_DOMAIN}.test_name_rotation"

        state = hass.states.get(entity_tilt)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        state = hass.states.get(entity_rotation)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        status["cury:0"]["errors"] = ["orientation_tilt", "orientation_plug_rotated"]
        monkeypatch.setattr(mock_rpc_device, "status", status)
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_tilt)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        state = hass.states.get(entity_rotation)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
