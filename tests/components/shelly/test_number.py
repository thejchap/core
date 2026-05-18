"""Tests for Shelly number platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, Mock

from aioshelly.const import MODEL_BLU_GATEWAY_G3
from aioshelly.exceptions import DeviceConnectionError, InvalidAuthError, RpcCallError
from syrupy.assertion import SnapshotAssertion
from tryke import Depends, expect, fixture, test

from homeassistant.components.number import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_STEP,
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
    NumberMode,
)
from homeassistant.components.shelly.const import DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.common import mock_restore_cache_with_extra_data
from tests.components.shelly import (
    init_integration,
    patch_platforms,
    register_device,
    register_entity,
)
from tests.components.shelly._fixtures import (
    disable_async_remove_shelly_rpc_entities as disable_async_remove_shelly_rpc_entities_fixture,
    mock_block_device as mock_block_device_fixture,
    mock_blu_trv as mock_blu_trv_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async, snapshot as snapshot_fixture

DEVICE_BLOCK_ID = 4

_MISSING = object()


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/setitem/delattr/delitem on Mocks."""

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
    with patch_platforms([Platform.NUMBER]):
        yield


@test
async def block_number_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device number update."""
    entity_id = "number.test_name_valve_position"
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "sleep_mode",
            {"period": 60, "unit": "m"},
        )
        await init_integration(hass, 1, sleep_period=3600)

        expect(hass.states.get(entity_id)).to_be_none()

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("50")

        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "valvePos", 30)
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("30")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-device_0-valvePos")


@test
async def block_restored_number(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored number."""
    entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
    device = register_device(device_registry, entry)
    capabilities = {
        "min": 0,
        "max": 100,
        "step": 1,
        "mode": "slider",
    }
    entity_id = register_entity(
        hass,
        NUMBER_DOMAIN,
        "test_name_valve_position",
        "device_0-valvePos",
        entry,
        capabilities,
        device_id=device.id,
    )
    extra_data = {
        "native_max_value": 100,
        "native_min_value": 0,
        "native_step": 1,
        "native_unit_of_measurement": "%",
        "native_value": "40",
    }
    mock_restore_cache_with_extra_data(hass, ((State(entity_id, ""), extra_data),))

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("40")

        monkeypatch.setattr(mock_block_device, "initialized", True)
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("50")


@test
async def block_restored_number_no_last_state(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored number missing last state."""
    entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
    device = register_device(device_registry, entry)
    capabilities = {
        "min": 0,
        "max": 100,
        "step": 1,
        "mode": "slider",
    }
    entity_id = register_entity(
        hass,
        NUMBER_DOMAIN,
        "test_name_valve_position",
        "device_0-valvePos",
        entry,
        capabilities,
        device_id=device.id,
    )
    with _patches() as monkeypatch:
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
        expect(state.state).to_equal("50")


@test
async def block_number_set_value(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device number set value."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "sleep_mode",
            {"period": 60, "unit": "m"},
        )
        await init_integration(hass, 1, sleep_period=3600)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        mock_block_device.reset_mock()
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: "number.test_name_valve_position", ATTR_VALUE: 30},
            blocking=True,
        )
        mock_block_device.set_thermostat_state.assert_called_once_with(0, pos=30.0)


@test
async def block_set_value_connection_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device set value connection error."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "sleep_mode",
            {"period": 60, "unit": "m"},
        )
        monkeypatch.setattr(
            mock_block_device,
            "set_thermostat_state",
            AsyncMock(side_effect=DeviceConnectionError),
        )
        await init_integration(hass, 1, sleep_period=3600)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        async with expect_raises_async(
            HomeAssistantError,
            match="Device communication error occurred while calling action for number.test_name_valve_position of Test name",
        ):
            await hass.services.async_call(
                NUMBER_DOMAIN,
                SERVICE_SET_VALUE,
                {ATTR_ENTITY_ID: "number.test_name_valve_position", ATTR_VALUE: 30},
                blocking=True,
            )


@test
async def block_set_value_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device set value authentication error."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "sleep_mode",
            {"period": 60, "unit": "m"},
        )
        monkeypatch.setattr(
            mock_block_device,
            "set_thermostat_state",
            AsyncMock(side_effect=InvalidAuthError),
        )
        entry = await init_integration(hass, 1, sleep_period=3600)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        expect(entry.state is ConfigEntryState.LOADED).to_be_truthy()

        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: "number.test_name_valve_position", ATTR_VALUE: 30},
            blocking=True,
        )

        expect(entry.state is ConfigEntryState.LOADED).to_be_truthy()

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(1)

        flow = flows[0]
        expect(flow.get("step_id")).to_equal("reauth_confirm")
        expect(flow.get("handler")).to_equal(DOMAIN)

        expect("context" in flow).to_be_truthy()
        expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
        expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)


@test.cases(
    test.case(
        "virtual_number",
        name="Virtual number",
        entity_id="number.test_name_virtual_number",
        original_unit="%",
        expected_unit="%",
        view="field",
        mode_name="BOX",
    ),
    test.case(
        "no_name",
        name=None,
        entity_id="number.test_name_number_203",
        original_unit="",
        expected_unit=None,
        view="field",
        mode_name="BOX",
    ),
    test.case(
        "virtual_slider",
        name="Virtual slider",
        entity_id="number.test_name_virtual_slider",
        original_unit="Hz",
        expected_unit="Hz",
        view="slider",
        mode_name="SLIDER",
    ),
)
async def rpc_device_virtual_number(
    name: str | None,
    entity_id: str,
    original_unit: str,
    expected_unit: str | None,
    view: str,
    mode_name: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test a virtual number for RPC device."""
    mode = NumberMode[mode_name]
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["number:203"] = {
            "name": name,
            "min": 0,
            "max": 100,
            "meta": {"ui": {"step": 0.1, "unit": original_unit, "view": view}},
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["number:203"] = {"value": 12.3}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("12.3")
        expect(state.attributes.get(ATTR_MIN)).to_equal(0)
        expect(state.attributes.get(ATTR_MAX)).to_equal(100)
        expect(state.attributes.get(ATTR_STEP)).to_equal(0.1)
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(expected_unit)
        expect(state.attributes.get(ATTR_MODE) is mode).to_be_truthy()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-number:203-number_generic")

        monkeypatch.setitem(mock_rpc_device.status["number:203"], "value", 78.9)
        mock_rpc_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("78.9")

        monkeypatch.setitem(mock_rpc_device.status["number:203"], "value", 56.7)
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 56.7},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        mock_rpc_device.number_set.assert_called_once_with(203, 56.7)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("56.7")


@test
async def rpc_remove_virtual_number_when_mode_label(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(disable_async_remove_shelly_rpc_entities_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test if the virtual number will be removed if the mode has been changed to a label."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["number:200"] = {
            "name": None,
            "min": -1000,
            "max": 1000,
            "meta": {"ui": {"step": 1, "unit": "", "view": "label"}},
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["number:200"] = {"value": 123}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        config_entry = await init_integration(hass, 3, skip_setup=True)
        device_entry = register_device(device_registry, config_entry)
        entity_id = register_entity(
            hass,
            NUMBER_DOMAIN,
            "test_name_number_200",
            "number:200-number_generic",
            config_entry,
            device_id=device_entry.id,
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test
async def rpc_remove_virtual_number_when_orphaned(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Check whether the virtual number will be removed if it has been removed from the device configuration."""
    config_entry = await init_integration(hass, 3, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)
    entity_id = register_entity(
        hass,
        NUMBER_DOMAIN,
        "test_name_number_200",
        "number:200-number_generic",
        config_entry,
        device_id=device_entry.id,
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(entity_registry.async_get(entity_id)).to_be_none()


@test.skip("snapshot test - port deferred")
async def blu_trv_number_entity(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test BLU TRV number entity."""


@test
async def blu_trv_ext_temp_set_value(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """Test the set value action for BLU TRV External Temperature number entity."""
    await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    entity_id = f"{NUMBER_DOMAIN}.trv_name_external_temperature"

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_VALUE: 22.2,
        },
        blocking=True,
    )
    mock_blu_trv.mock_update()
    mock_blu_trv.blu_trv_set_external_temperature.assert_called_once_with(200, 22.2)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("22.2")


@test
async def blu_trv_valve_pos_set_value(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """Test the set value action for BLU TRV Valve Position number entity."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_blu_trv.config["blutrv:200"], "enable", False)

        await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

        entity_id = f"{NUMBER_DOMAIN}.trv_name_valve_position"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("0")

        monkeypatch.setitem(mock_blu_trv.status["blutrv:200"], "pos", 20)
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_VALUE: 20.0,
            },
            blocking=True,
        )
        mock_blu_trv.mock_update()
        mock_blu_trv.blu_trv_set_valve_position.assert_called_once_with(200, 20.0)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("20")


@test.cases(
    test.case(
        "device_connection",
        exc_id="device_connection",
        error="Device communication error occurred while calling action for number.trv_name_external_temperature of Test name",
    ),
    test.case(
        "rpc_call",
        exc_id="rpc_call",
        error="RPC call error occurred while calling action for number.trv_name_external_temperature of Test name",
    ),
)
async def blu_trv_number_exc(
    exc_id: str,
    error: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """Test RPC/BLU TRV number with exception."""
    await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    if exc_id == "device_connection":
        exception: Exception | type[Exception] = DeviceConnectionError
    else:
        exception = RpcCallError(999)

    mock_blu_trv.blu_trv_set_external_temperature.side_effect = exception

    async with expect_raises_async(HomeAssistantError, match=error):
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: f"{NUMBER_DOMAIN}.trv_name_external_temperature",
                ATTR_VALUE: 20.0,
            },
            blocking=True,
        )


@test
async def blu_trv_number_reauth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """Test RPC/BLU TRV number with authentication error."""
    entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    mock_blu_trv.blu_trv_set_external_temperature.side_effect = InvalidAuthError

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: f"{NUMBER_DOMAIN}.trv_name_external_temperature",
            ATTR_VALUE: 20.0,
        },
        blocking=True,
    )

    expect(entry.state is ConfigEntryState.LOADED).to_be_truthy()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow.get("step_id")).to_equal("reauth_confirm")
    expect(flow.get("handler")).to_equal(DOMAIN)

    expect("context" in flow).to_be_truthy()
    expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
    expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)


@test.skip("snapshot test - port deferred")
async def cury_number_entity(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test number entities for cury component."""
