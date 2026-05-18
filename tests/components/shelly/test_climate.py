"""Tests for Shelly climate platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, Mock, PropertyMock

from aioshelly.const import (
    BLU_TRV_IDENTIFIER,
    MODEL_BLU_GATEWAY_G3,
    MODEL_VALVE,
    MODEL_WALL_DISPLAY,
)
from aioshelly.exceptions import DeviceConnectionError, InvalidAuthError, RpcCallError
from syrupy.assertion import SnapshotAssertion
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    PRESET_NONE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACAction,
    HVACMode,
)
from homeassistant.components.shelly.const import DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    STATE_ON,
    STATE_UNAVAILABLE,
    Platform,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from tests.common import mock_restore_cache, mock_restore_cache_with_extra_data
from tests.components.shelly import (
    MOCK_MAC,
    init_integration,
    patch_platforms,
    register_device,
    register_entity,
)
from tests.components.shelly._fixtures import (
    MOCK_STATUS_COAP,
    mock_block_device as mock_block_device_fixture,
    mock_blu_trv as mock_blu_trv_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async, snapshot as snapshot_fixture

SENSOR_BLOCK_ID = 3
DEVICE_BLOCK_ID = 4
EMETER_BLOCK_ID = 5
GAS_VALVE_BLOCK_ID = 6
ENTITY_ID = f"{CLIMATE_DOMAIN}.test_name"


_MISSING = object()
_builtin_delattr = delattr


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/setitem/delattr/delitem on Mocks."""

    undo: list[Any] = []

    class _Patcher:
        def setattr(self, target: Any, name: str, value: Any) -> None:
            original = target.__dict__.get(name, _MISSING)
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
            # Use builtin delattr so Mock blocks attribute auto-creation
            # afterwards; `del target.__dict__[name]` leaves Mock free to
            # synthesise a child Mock on next access.
            original = target.__dict__.get(name, _MISSING)
            undo.append(("attr", target, name, original))
            with suppress(AttributeError):
                _builtin_delattr(target, name)

    try:
        yield _Patcher()
    finally:
        for kind, obj, key, original in reversed(undo):
            if kind == "attr":
                if original is _MISSING:
                    with suppress(AttributeError, KeyError):
                        del obj.__dict__[key]
                else:
                    obj.__dict__[key] = original
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
    with patch_platforms([Platform.CLIMATE, Platform.SWITCH]):
        yield


@test.skip("snapshot test - port deferred")
async def climate_hvac_mode(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test climate hvac mode service."""


@test
async def climate_set_temperature(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test climate set temperature service."""
    with _patches() as monkeypatch:
        monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        monkeypatch.delattr(
            mock_block_device.blocks[GAS_VALVE_BLOCK_ID], "targetTemp"
        )
        await init_integration(hass, 1, sleep_period=1000)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(ENTITY_ID)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.OFF)
        expect(state.attributes[ATTR_TEMPERATURE]).to_equal(4)

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_TEMPERATURE: 23},
            blocking=True,
        )

        mock_block_device.set_thermostat_state.assert_called_once_with(
            0, target_t_enabled=1, target_t=23.0
        )
        mock_block_device.set_thermostat_state.reset_mock()

        # Test conversion from C to F
        monkeypatch.setattr(
            mock_block_device,
            "settings",
            {"thermostats": [{"target_t": {"units": "F"}}]},
        )

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_TEMPERATURE: 20},
            blocking=True,
        )

        mock_block_device.set_thermostat_state.assert_called_once_with(
            0, target_t_enabled=1, target_t=68.0
        )


@test
async def climate_set_preset_mode(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test climate set preset mode service."""
    with _patches() as monkeypatch:
        monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
        monkeypatch.delattr(
            mock_block_device.blocks[GAS_VALVE_BLOCK_ID], "targetTemp"
        )
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "mode", None)
        await init_integration(hass, 1, sleep_period=1000, model=MODEL_VALVE)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(ENTITY_ID)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_PRESET_MODE]).to_equal(PRESET_NONE)

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "Profile2"},
            blocking=True,
        )

        mock_block_device.set_thermostat_state.assert_called_once_with(
            0, schedule=1, schedule_profile=2
        )

        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "mode", 2)
        mock_block_device.mock_update()

        state = hass.states.get(ENTITY_ID)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_PRESET_MODE]).to_equal("Profile2")

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_NONE},
            blocking=True,
        )

        expect(len(mock_block_device.set_thermostat_state.mock_calls)).to_equal(2)
        mock_block_device.set_thermostat_state.assert_called_with(0, schedule=0)

        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "mode", 0)
        mock_block_device.mock_update()

        state = hass.states.get(ENTITY_ID)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_PRESET_MODE]).to_equal(PRESET_NONE)


@test
async def block_restored_climate(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored climate."""
    with _patches() as monkeypatch:
        monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
        monkeypatch.delattr(
            mock_block_device.blocks[GAS_VALVE_BLOCK_ID], "targetTemp"
        )
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        monkeypatch.delattr(mock_block_device.blocks[EMETER_BLOCK_ID], "targetTemp")
        entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            CLIMATE_DOMAIN,
            "test_name",
            "sensor_0",
            entry,
            device_id=device.id,
        )
        attrs = {"current_temperature": 20.5, "temperature": 4.0}
        extra_data = {"last_target_temp": 22.0}
        mock_restore_cache_with_extra_data(
            hass, ((State(entity_id, HVACMode.OFF, attributes=attrs), extra_data),)
        )

        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.OFF)
        expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(4.0)

        # Partial update, should not change state
        mock_block_device.mock_update()
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.OFF)
        expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(4.0)

        # Make device online
        monkeypatch.setattr(mock_block_device, "initialized", True)
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.OFF)
        expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(4.0)

        # Test set hvac mode heat, target temp should be set to last target temp (22)
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
        mock_block_device.set_thermostat_state.assert_called_once_with(
            0, target_t_enabled=1, target_t=22.0
        )

        monkeypatch.setattr(
            mock_block_device.blocks[SENSOR_BLOCK_ID], "targetTemp", 22.0
        )
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.HEAT)
        expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(22.0)


@test
async def block_restored_climate_us_customary(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored climate with US CUSTOMARY unit system."""
    with _patches() as monkeypatch:
        hass.config.units = US_CUSTOMARY_SYSTEM
        monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
        monkeypatch.delattr(
            mock_block_device.blocks[GAS_VALVE_BLOCK_ID], "targetTemp"
        )
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        monkeypatch.delattr(mock_block_device.blocks[EMETER_BLOCK_ID], "targetTemp")
        entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            CLIMATE_DOMAIN,
            "test_name",
            "sensor_0",
            entry,
            device_id=device.id,
        )
        attrs = {"current_temperature": 67, "temperature": 39}
        extra_data = {"last_target_temp": 10.0}
        mock_restore_cache_with_extra_data(
            hass, ((State(entity_id, HVACMode.OFF, attributes=attrs), extra_data),)
        )

        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.OFF)
        expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(39)
        expect(state.attributes.get(ATTR_CURRENT_TEMPERATURE)).to_equal(67)

        # Partial update, should not change state
        mock_block_device.mock_update()
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.OFF)
        expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(39)
        expect(state.attributes.get(ATTR_CURRENT_TEMPERATURE)).to_equal(67)

        # Make device online
        monkeypatch.setattr(mock_block_device, "initialized", True)
        monkeypatch.setattr(
            mock_block_device.blocks[SENSOR_BLOCK_ID], "targetTemp", 4.0
        )
        monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "temp", 18.2)
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.OFF)
        expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(39)
        expect(state.attributes.get(ATTR_CURRENT_TEMPERATURE)).to_equal(65)

        # Test set hvac mode heat, target temp should be set to last target temp (10.0/50)
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
        mock_block_device.set_thermostat_state.assert_called_once_with(
            0, target_t_enabled=1, target_t=10.0
        )

        monkeypatch.setattr(
            mock_block_device.blocks[SENSOR_BLOCK_ID], "targetTemp", 10.0
        )
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.HEAT)
        expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(50)


@test
async def block_restored_climate_unavailable(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored climate unavailable state."""
    with _patches() as monkeypatch:
        monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            CLIMATE_DOMAIN,
            "test_name",
            "sensor_0",
            entry,
            device_id=device.id,
        )
        mock_restore_cache(hass, [State(entity_id, STATE_UNAVAILABLE)])

        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.OFF)


@test
async def block_restored_climate_set_preset_before_online(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored climate set preset before device is online."""
    with _patches() as monkeypatch:
        monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            CLIMATE_DOMAIN,
            "test_name",
            "sensor_0",
            entry,
            device_id=device.id,
        )
        mock_restore_cache(hass, [State(entity_id, HVACMode.HEAT)])

        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.HEAT)

        async with expect_raises_async(ServiceValidationError):
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_PRESET_MODE,
                {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "Profile1"},
                blocking=True,
            )

        mock_block_device.http_request.assert_not_called()


@test
async def block_set_mode_connection_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device set mode connection error."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        monkeypatch.setattr(
            mock_block_device,
            "set_thermostat_state",
            AsyncMock(side_effect=DeviceConnectionError),
        )
        await init_integration(hass, 1, sleep_period=1000)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        async with expect_raises_async(
            HomeAssistantError,
            match="Device communication error occurred while calling action for climate.test_name of Test name",
        ):
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
                blocking=True,
            )


@test
async def block_set_mode_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device set mode authentication error."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        monkeypatch.setattr(
            mock_block_device,
            "set_thermostat_state",
            AsyncMock(side_effect=InvalidAuthError),
        )
        entry = await init_integration(hass, 1, sleep_period=1000)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        expect(entry.state is ConfigEntryState.LOADED).to_be_truthy()

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
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


@test
async def block_restored_climate_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test block restored climate with authentication error during init."""
    with _patches() as monkeypatch:
        monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0
        )
        entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            CLIMATE_DOMAIN,
            "test_name",
            "sensor_0",
            entry,
            device_id=device.id,
        )
        mock_restore_cache(hass, [State(entity_id, HVACMode.HEAT)])

        monkeypatch.setattr(mock_block_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.state is ConfigEntryState.LOADED).to_be_truthy()

        # Make device online with auth error
        monkeypatch.setattr(mock_block_device, "initialized", True)
        type(mock_block_device).settings = PropertyMock(
            return_value={}, side_effect=InvalidAuthError
        )
        try:
            mock_block_device.mock_online()
            await hass.async_block_till_done(wait_background_tasks=True)

            expect(entry.state is ConfigEntryState.LOADED).to_be_truthy()

            flows = hass.config_entries.flow.async_progress()
            expect(len(flows)).to_equal(1)

            flow = flows[0]
            expect(flow.get("step_id")).to_equal("reauth_confirm")
            expect(flow.get("handler")).to_equal(DOMAIN)

            expect("context" in flow).to_be_truthy()
            expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
            expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)
        finally:
            # Restore settings PropertyMock so subsequent tests reusing the
            # same Mock class don't inherit the auth-error behaviour.
            del type(mock_block_device).settings


@test
async def device_not_calibrated(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test to create an issue when the device is not calibrated."""
    with _patches() as monkeypatch:
        await init_integration(hass, 1, sleep_period=1000, model=MODEL_VALVE)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        mock_status = MOCK_STATUS_COAP.copy()
        mock_status["calibrated"] = False
        monkeypatch.setattr(mock_block_device, "status", mock_status)
        mock_block_device.mock_update()
        await hass.async_block_till_done()

        expect(
            issue_registry.async_get_issue(
                domain=DOMAIN, issue_id=f"not_calibrated_{MOCK_MAC}"
            )
        ).to_be_truthy()

        # The device has been calibrated
        monkeypatch.setattr(mock_block_device, "status", MOCK_STATUS_COAP)
        mock_block_device.mock_update()
        await hass.async_block_till_done()

        expect(
            issue_registry.async_get_issue(
                domain=DOMAIN, issue_id=f"not_calibrated_{MOCK_MAC}"
            )
        ).to_be_falsy()


@test.skip("snapshot test - port deferred")
async def rpc_climate_hvac_mode(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test climate hvac mode service."""


@test
async def rpc_climate_without_humidity(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test climate entity without the humidity value."""
    with _patches() as monkeypatch:
        entity_id = "climate.test_name"
        new_status = deepcopy(mock_rpc_device.status)
        new_status.pop("humidity:0")
        monkeypatch.setattr(mock_rpc_device, "status", new_status)

        await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.HEAT)
        expect(state.attributes[ATTR_TEMPERATURE]).to_equal(23)
        expect(state.attributes[ATTR_CURRENT_TEMPERATURE]).to_equal(12.3)
        expect(state.attributes[ATTR_HVAC_ACTION]).to_equal(HVACAction.HEATING)
        expect(ATTR_CURRENT_HUMIDITY not in state.attributes).to_be_truthy()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-thermostat:0")


@test
async def rpc_climate_set_temperature(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test climate set target temperature."""
    with _patches() as monkeypatch:
        entity_id = "climate.test_name"

        await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_TEMPERATURE]).to_equal(23)

        monkeypatch.setitem(mock_rpc_device.status["thermostat:0"], "target_C", 28)
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 28},
            blocking=True,
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.climate_set_target_temperature.assert_called_once_with(0, 28)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_TEMPERATURE]).to_equal(28)


@test
async def rpc_climate_hvac_mode_cool(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test climate with hvac mode cooling."""
    with _patches() as monkeypatch:
        entity_id = "climate.test_name"
        new_config = deepcopy(mock_rpc_device.config)
        new_config["thermostat:0"]["type"] = "cooling"
        monkeypatch.setattr(mock_rpc_device, "config", new_config)

        await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.COOL)
        expect(state.attributes[ATTR_HVAC_ACTION]).to_equal(HVACAction.COOLING)


@test.skip("snapshot test - port deferred")
async def wall_display_thermostat_mode(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test Wall Display in thermostat mode."""


@test
async def wall_display_thermostat_mode_external_actuator(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test Wall Display in thermostat mode with an external actuator."""
    with _patches() as monkeypatch:
        climate_entity_id = "climate.test_name"
        switch_entity_id = "switch.test_name_test_switch_0"

        new_status = deepcopy(mock_rpc_device.status)
        new_status["sys"]["relay_in_thermostat"] = False
        new_status.pop("cover:0")
        monkeypatch.setattr(mock_rpc_device, "status", new_status)

        await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

        state = hass.states.get(switch_entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(len(hass.states.async_entity_ids(SWITCH_DOMAIN))).to_equal(1)

        state = hass.states.get(climate_entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(HVACMode.HEAT)
        expect(len(hass.states.async_entity_ids(CLIMATE_DOMAIN))).to_equal(1)

        entry = entity_registry.async_get(climate_entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-thermostat:0")


@test.skip("snapshot test - port deferred")
async def blu_trv_climate_set_temperature(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test BLU TRV set target temperature."""


@test
async def blu_trv_climate_disabled(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """Test BLU TRV disabled."""
    with _patches() as monkeypatch:
        entity_id = "climate.trv_name"
        monkeypatch.delitem(mock_blu_trv.status, "thermostat:0")

        await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_TEMPERATURE]).to_equal(17.1)

        monkeypatch.setitem(
            mock_blu_trv.config[f"{BLU_TRV_IDENTIFIER}:200"], "enable", False
        )
        mock_blu_trv.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_TEMPERATURE]).to_equal(None)


@test
async def blu_trv_climate_hvac_action(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """Test BLU TRV is heating."""
    with _patches() as monkeypatch:
        entity_id = "climate.trv_name"
        monkeypatch.delitem(mock_blu_trv.status, "thermostat:0")

        await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_HVAC_ACTION]).to_equal(HVACAction.IDLE)

        monkeypatch.setitem(
            mock_blu_trv.status[f"{BLU_TRV_IDENTIFIER}:200"], "pos", 10
        )
        mock_blu_trv.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_HVAC_ACTION]).to_equal(HVACAction.HEATING)


@test.cases(
    test.case(
        "device_connection",
        exc_id="device_connection",
        error="Device communication error occurred while calling action for climate.trv_name of Test name",
    ),
    test.case(
        "rpc_call",
        exc_id="rpc_call",
        error="RPC call error occurred while calling action for climate.trv_name of Test name",
    ),
)
async def blu_trv_set_target_temp_exc(
    exc_id: str,
    error: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """BLU TRV target temperature setting test with excepton."""
    await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    if exc_id == "device_connection":
        exception: Exception | type[Exception] = DeviceConnectionError
    else:
        exception = RpcCallError(999)

    mock_blu_trv.blu_trv_set_target_temperature.side_effect = exception

    async with expect_raises_async(HomeAssistantError, match=error):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: "climate.trv_name", ATTR_TEMPERATURE: 28},
            blocking=True,
        )


@test
async def blu_trv_set_target_temp_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """BLU TRV target temperature setting test with authentication error."""
    entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    mock_blu_trv.blu_trv_set_target_temperature.side_effect = InvalidAuthError

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "climate.trv_name", ATTR_TEMPERATURE: 28},
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
async def rpc_linkedgo_st802_thermostat(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test LINKEDGO ST802 thermostat climate."""


@test.skip("snapshot test - port deferred")
async def rpc_linkedgo_st1820_thermostat(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test LINKEDGO ST1820 thermostat climate."""
