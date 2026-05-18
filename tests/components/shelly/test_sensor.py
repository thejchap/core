"""Tests for Shelly sensor platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import Mock, patch

from aioshelly.const import MODEL_EM3
from tryke import Depends, expect, fixture, test

from homeassistant.components.homeassistant import (
    DOMAIN as HA_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from homeassistant.components.sensor import (
    ATTR_OPTIONS,
    ATTR_STATE_CLASS,
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.shelly import (
    BLOCK_SLEEPING_PLATFORMS,
    PLATFORMS,
    RPC_SLEEPING_PLATFORMS,
)
from homeassistant.components.shelly.const import DOMAIN
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    Platform,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.setup import async_setup_component

from tests.components.shelly import (
    MOCK_MAC,
    init_integration,
    mutate_rpc_device_status,
    register_device,
    register_entity,
)
from tests.components.shelly._fixtures import (
    disable_async_remove_shelly_rpc_entities as disable_async_remove_shelly_rpc_entities_fixture,
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

_MISSING = object()

RELAY_BLOCK_ID = 0
SENSOR_BLOCK_ID = 3
DEVICE_BLOCK_ID = 4


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
    with _patch_platforms([Platform.SENSOR]):
        yield


@fixture
def _registry_enabled_by_default() -> Generator[None]:
    """Force entity_registry_enabled_default to True for sensors."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
    ):
        yield


@test
async def block_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block sensor."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_channel_1_power"
    await init_integration(hass, 1)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("53.4")

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device.blocks[RELAY_BLOCK_ID], "power", 60.1)
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("60.1")

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-relay_0-power")


@test
async def block_sensor_em3(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block sensor of EM3."""
    from tests.components.shelly._fixtures import MOCK_BLOCKS

    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_emeters", 3)
        monkeypatch.setitem(mock_block_device.settings["device"], "type", MODEL_EM3)
        monkeypatch.setitem(
            mock_block_device.settings,
            "emeters",
            [
                {"name": "Grid L1", "appliance_type": "General", "max_power": 0},
                {"appliance_type": "General", "max_power": 0},
                {"appliance_type": "General", "max_power": 0},
            ],
        )
        blocks = deepcopy(MOCK_BLOCKS)
        blocks[5] = Mock(
            sensor_ids={"power": 20},
            channel="0",
            power=20,
            description="emeter_0",
            type="emeter",
        )
        blocks.append(
            Mock(
                sensor_ids={"power": 20},
                channel="1",
                power=20,
                description="emeter_1",
                type="emeter",
            )
        )
        blocks.append(
            Mock(
                sensor_ids={"power": 20},
                channel="2",
                power=20,
                description="emeter_2",
                type="emeter",
            )
        )
        monkeypatch.setattr(mock_block_device, "blocks", blocks)
        await init_integration(hass, 1, model=MODEL_EM3)

        expect(hass.states.get(f"{SENSOR_DOMAIN}.grid_l1_power")).to_be_truthy()
        expect(
            hass.states.get(f"{SENSOR_DOMAIN}.test_name_phase_b_power")
        ).to_be_truthy()
        expect(
            hass.states.get(f"{SENSOR_DOMAIN}.test_name_phase_c_power")
        ).to_be_truthy()


@test
async def energy_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test energy sensor."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_channel_1_energy"
    await init_integration(hass, 1)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("20.5761315")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfEnergy.KILO_WATT_HOUR
    )

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-relay_0-energy")


@test
async def power_factory_unit_migration(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test migration unit of the power factory sensor."""
    entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "123456789ABC-emeter_0-powerFactor",
        suggested_object_id="test_name_power_factor",
        unit_of_measurement="%",
    )

    entity_id = f"{SENSOR_DOMAIN}.test_name_power_factor"
    await init_integration(hass, 1)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("98.0")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(PERCENTAGE)

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-emeter_0-powerFactor")


@test
async def power_factory_without_unit_migration(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unit and value of the power factory sensor without unit migration."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_power_factor"
    await init_integration(hass, 1)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("0.98")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_be_none()

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-emeter_0-powerFactor")


@test.skip("requires freezer / REST update timing")
async def block_rest_sensor() -> None:
    """Stub for test_block_rest_sensor (freezer dependency)."""


@test
async def block_sleeping_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block sleeping sensor."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID], "sensor_ids", {"battery": 98}
        )
        entity_id = f"{SENSOR_DOMAIN}.test_name_temperature"
        await init_integration(hass, 1, sleep_period=1000)

        expect(hass.states.get(entity_id)).to_be_none()

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("22.1")

        monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "temp", 23.4)
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("23.4")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-sensor_0-temp")


@test.skip("requires mock_restore_cache_with_extra_data")
async def block_restored_sleeping_sensor() -> None:
    """Stub (restore cache dependency)."""


@test.skip("requires mock_restore_cache_with_extra_data")
async def block_restored_sleeping_sensor_no_last_state() -> None:
    """Stub (restore cache dependency)."""


@test
async def block_sensor_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block sensor unavailable on sensor error."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_battery"
    await init_integration(hass, 1)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("98")

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "battery", -1)
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-device_0-battery")


@test
async def block_sensor_removal(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block sensor is removed due to removal_condition."""
    entity_id = register_entity(
        hass, SENSOR_DOMAIN, "test_name_battery", "device_0-battery"
    )

    expect(entity_registry.async_get(entity_id)).to_be_truthy()

    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.settings, "external_power", 1)
        await init_integration(hass, 1)

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test.skip("requires mock_restore_cache_with_extra_data")
async def block_not_matched_restored_sleeping_sensor() -> None:
    """Stub (restore cache dependency)."""


@test
async def block_sensor_without_value(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block sensor without value is not created."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_battery"
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "battery", None)
        await init_integration(hass, 1)

        expect(hass.states.get(entity_id)).to_be_none()


@test.cases(
    test.case(
        "battery_none",
        entity="test_name_battery",
        initial_state="98",
        block_id=DEVICE_BLOCK_ID,
        attribute="battery",
        value=None,
        final_value=STATE_UNKNOWN,
    ),
    test.case(
        "sensorop_none",
        entity="test_name_operation",
        initial_state="normal",
        block_id=SENSOR_BLOCK_ID,
        attribute="sensorOp",
        value=None,
        final_value=STATE_UNKNOWN,
    ),
    test.case(
        "sensorop_normal",
        entity="test_name_operation",
        initial_state="normal",
        block_id=SENSOR_BLOCK_ID,
        attribute="sensorOp",
        value="normal",
        final_value="normal",
    ),
    test.case(
        "selftest_completed",
        entity="test_name_self_test",
        initial_state="pending",
        block_id=SENSOR_BLOCK_ID,
        attribute="selfTest",
        value="completed",
        final_value="completed",
    ),
    test.case(
        "gas_heavy",
        entity="test_name_gas_detected",
        initial_state="mild",
        block_id=SENSOR_BLOCK_ID,
        attribute="gas",
        value="heavy",
        final_value="heavy",
    ),
)
async def block_sensor_values(
    entity: str,
    initial_state: str,
    block_id: int,
    attribute: str,
    value: Any,
    final_value: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block sensor unknown value."""
    entity_id = f"{SENSOR_DOMAIN}.{entity}"
    await init_integration(hass, 1)

    expect(hass.states.get(entity_id).state).to_equal(initial_state)

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device.blocks[block_id], attribute, value)
        mock_block_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(final_value)


@test.cases(
    test.case("0_hours", lamp_life_seconds=0, percentage="100.0"),
    test.case("16_hours", lamp_life_seconds=57600, percentage="99.8222222222222"),
    test.case("4500_hours", lamp_life_seconds=16200000, percentage="50.0"),
    test.case("9000_hours", lamp_life_seconds=32400000, percentage="0.0"),
    test.case("over_9000_hours", lamp_life_seconds=36000000, percentage="0.0"),
)
async def block_shelly_air_lamp_life(
    lamp_life_seconds: int,
    percentage: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block Shelly Air lamp life percentage sensor."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
        entity_id = f"{SENSOR_DOMAIN}.test_name_lamp_life"
        monkeypatch.setattr(
            mock_block_device.blocks[RELAY_BLOCK_ID],
            "totalWorkTime",
            lamp_life_seconds,
        )
        await init_integration(hass, 1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(percentage)


@test
async def rpc_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC sensor."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_test_cover_0_power"
    await init_integration(hass, 2)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("85.3")

    with _patches() as monkeypatch:
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "apower", "88.2"
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("88.2")

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cover:0", "apower", None
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def rpc_rssi_sensor_removal(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: None = Depends(_registry_enabled_by_default),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC RSSI sensor removal if no WiFi stations enabled."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_signal_strength"
    entry = await init_integration(hass, 2)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("-63")

    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_rpc_device.config["wifi"]["sta"], "enable", False)
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        expect(hass.states.get(entity_id)).to_be_none()

        monkeypatch.setitem(mock_rpc_device.config["wifi"]["sta1"], "enable", True)
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("-63")


@test
async def rpc_illuminance_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC illuminance sensor."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_illuminance"
    await init_integration(hass, 2)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("345")

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-illuminance:0-illuminance")


@test
async def rpc_sensor_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC sensor unavailable on sensor error."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_voltmeter"
    await init_integration(hass, 2)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("4.321")

    with _patches() as monkeypatch:
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "voltmeter:100", "voltage", None
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-voltmeter:100-voltmeter")


@test.skip("requires freezer / polling RPC update timing")
async def rpc_polling_sensor() -> None:
    """Stub (freezer dependency)."""


@test
async def rpc_sleeping_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC online sleeping sensor."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_temperature"
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
        await init_integration(hass, 2, sleep_period=1000)

        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("22.9")

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "temperature:0", "tC", 23.4
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("23.4")


@test
async def rpc_sleeping_sensor_with_channel_name(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC online sleeping sensor with channel name."""
    name = "test channel name"
    entity_id = f"{SENSOR_DOMAIN}.test_name_test_channel_name_temperature"
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_rpc_device.config, "temperature:0", {"id": 0, "name": name}
        )
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
        await init_integration(hass, 2, sleep_period=1000)

        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes["friendly_name"]).to_equal(
            f"Test name {name} temperature"
        )
        expect(state.state).to_equal("22.9")

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "temperature:0", "tC", 23.4
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("23.4")


@test.skip("requires mock_restore_cache_with_extra_data")
async def rpc_restored_sleeping_sensor() -> None:
    """Stub (restore cache dependency)."""


@test
async def rpc_restored_sleeping_sensor_no_last_state(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test RPC restored sensor missing last state."""
    entry = await init_integration(hass, 2, sleep_period=1000, skip_setup=True)
    device = register_device(device_registry, entry)
    entity_id = register_entity(
        hass,
        SENSOR_DOMAIN,
        "test_name_temperature",
        "temperature:0-temperature_tc",
        entry,
        device_id=device.id,
    )

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "initialized", False)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNKNOWN)

        monkeypatch.setattr(mock_rpc_device, "initialized", True)
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        mock_rpc_device.mock_update()
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("22.9")


@test
async def rpc_energy_meter_1_sensors(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: None = Depends(_registry_enabled_by_default),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC sensors for EM1 component."""
    await init_integration(hass, 2)

    state = hass.states.get("sensor.test_name_energy_meter_0_power")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("85.3")

    entry = entity_registry.async_get("sensor.test_name_energy_meter_0_power")
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-em1:0-power_em1")

    state = hass.states.get("sensor.test_name_energy_meter_1_power")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("123.3")

    entry = entity_registry.async_get("sensor.test_name_energy_meter_1_power")
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-em1:1-power_em1")

    state = hass.states.get("sensor.test_name_energy_meter_0_energy")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("123.4564")

    entry = entity_registry.async_get("sensor.test_name_energy_meter_0_energy")
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-em1data:0-total_act_energy")

    state = hass.states.get("sensor.test_name_energy_meter_1_energy")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("987.6543")

    entry = entity_registry.async_get("sensor.test_name_energy_meter_1_energy")
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-em1data:1-total_act_energy")


@test
async def rpc_sleeping_update_entity_service(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test RPC sleeping device when the update_entity service is used."""
    await async_setup_component(hass, "homeassistant", {})

    entity_id = f"{SENSOR_DOMAIN}.test_name_temperature"
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
        await init_integration(hass, 2, sleep_period=1000)

        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("22.9")

        await hass.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            service_data={ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("22.9")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-temperature:0-temperature_tc")

        expect(
            "Entity sensor.test_name_temperature comes from a sleeping device"
            in caplog.text
        ).to_be_truthy()


@test
async def block_sleeping_update_entity_service(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test block sleeping device when the update_entity service is used."""
    await async_setup_component(hass, "homeassistant", {})

    entity_id = f"{SENSOR_DOMAIN}.test_name_temperature"
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
        expect(state.state).to_equal("22.1")

        await hass.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            service_data={ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("22.1")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-sensor_0-temp")

        expect(
            "Entity sensor.test_name_temperature comes from a sleeping device"
            in caplog.text
        ).to_be_truthy()


@test.cases(
    test.case("with_unit", original_unit="m/s", expected_unit="m/s"),
    test.case("none_unit", original_unit=None, expected_unit=None),
    test.case("empty_unit", original_unit="", expected_unit=None),
)
async def rpc_analog_input_sensors(
    original_unit: str | None,
    expected_unit: str | None,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC analog input xpercent sensor."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["input:1"]["xpercent"] = {"expr": "x*0.2995", "unit": original_unit}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        await init_integration(hass, 2)

        entity_id = f"{SENSOR_DOMAIN}.test_name_input_1_analog"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("89")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-input:1-analoginput")

        entity_id = f"{SENSOR_DOMAIN}.test_name_input_1_analog_value"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("8.9")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(expected_unit)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-input:1-analoginput_xpercent")


@test
async def rpc_disabled_analog_input_sensors(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC disabled counter sensor."""
    with _patches() as monkeypatch:
        new_config = deepcopy(mock_rpc_device.config)
        new_config["input:1"]["enable"] = False
        monkeypatch.setattr(mock_rpc_device, "config", new_config)

        await init_integration(hass, 2)

        expect(hass.states.get(f"{SENSOR_DOMAIN}.test_name_input_1_analog")).to_be_none()
        expect(
            hass.states.get(f"{SENSOR_DOMAIN}.test_name_input_1_analog_value")
        ).to_be_none()


@test
async def rpc_disabled_xpercent(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC empty xpercent value."""
    with _patches() as monkeypatch:
        mutate_rpc_device_status(
            monkeypatch,
            mock_rpc_device,
            "input:1",
            "xpercent",
            None,
        )
        await init_integration(hass, 2)

        state = hass.states.get(f"{SENSOR_DOMAIN}.test_name_input_1_analog")
        expect(state).to_be_truthy()
        expect(state.state).to_equal("89")

        expect(
            hass.states.get(f"{SENSOR_DOMAIN}.test_name_input_1_analog_value")
        ).to_be_none()


@test.cases(
    test.case("with_unit", original_unit="l/h", expected_unit="l/h"),
    test.case("none_unit", original_unit=None, expected_unit=None),
    test.case("empty_unit", original_unit="", expected_unit=None),
)
async def rpc_pulse_counter_sensors(
    original_unit: str | None,
    expected_unit: str | None,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC counter sensor."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["input:2"]["xcounts"] = {"expr": "x/10", "unit": original_unit}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        await init_integration(hass, 2)

        entity_id = f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("56174")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal("pulse")
        expect(state.attributes.get(ATTR_STATE_CLASS)).to_equal(SensorStateClass.TOTAL)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-input:2-pulse_counter")

        entity_id = f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter_value"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("561.74")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(expected_unit)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-input:2-counter_value")


@test
async def rpc_disabled_pulse_counter_sensors(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC disabled counter sensor."""
    with _patches() as monkeypatch:
        new_config = deepcopy(mock_rpc_device.config)
        new_config["input:2"]["enable"] = False
        monkeypatch.setattr(mock_rpc_device, "config", new_config)

        await init_integration(hass, 2)

        expect(hass.states.get(f"{SENSOR_DOMAIN}.gas_pulse_counter")).to_be_none()
        expect(hass.states.get(f"{SENSOR_DOMAIN}.gas_pulse_counter_value")).to_be_none()


@test
async def rpc_disabled_xtotal_counter(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC disabled xtotal counter."""
    with _patches() as monkeypatch:
        mutate_rpc_device_status(
            monkeypatch,
            mock_rpc_device,
            "input:2",
            "counts",
            {"total": 20635},
        )
        await init_integration(hass, 2)

        state = hass.states.get(f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter")
        expect(state).to_be_truthy()
        expect(state.state).to_equal("20635")

        expect(
            hass.states.get(f"{SENSOR_DOMAIN}.test_name_gas_counter_value")
        ).to_be_none()


@test.cases(
    test.case("with_unit", original_unit="W", expected_unit="W"),
    test.case("none_unit", original_unit=None, expected_unit=None),
    test.case("empty_unit", original_unit="", expected_unit=None),
)
async def rpc_pulse_counter_frequency_sensors(
    original_unit: str | None,
    expected_unit: str | None,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC counter sensor."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["input:2"]["xfreq"] = {"expr": "x**2", "unit": original_unit}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        await init_integration(hass, 2)

        entity_id = f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter_frequency"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("208.0")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfFrequency.HERTZ
        )
        expect(state.attributes.get(ATTR_STATE_CLASS)).to_equal(
            SensorStateClass.MEASUREMENT
        )

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-input:2-counter_frequency")

        entity_id = f"{SENSOR_DOMAIN}.test_name_gas_pulse_counter_frequency_value"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("6.11")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(expected_unit)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-input:2-counter_frequency_value")


@test
async def rpc_disabled_xfreq(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC input with the xfreq sensor disabled."""
    with _patches() as monkeypatch:
        status = deepcopy(mock_rpc_device.status)
        status["input:2"] = {
            "id": 2,
            "counts": {"total": 56174, "xtotal": 561.74},
            "freq": 208.00,
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 2)

        entity_id = f"{SENSOR_DOMAIN}.gas_pulse_counter_frequency_value"

        expect(hass.states.get(entity_id)).to_be_none()
        expect(entity_registry.async_get(entity_id)).to_be_none()


@test.cases(
    test.case(
        "with_name", name="Virtual sensor", entity_id="sensor.test_name_virtual_sensor"
    ),
    test.case("no_name", name=None, entity_id="sensor.test_name_text_203"),
)
async def rpc_device_virtual_text_sensor(
    name: str | None,
    entity_id: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test a virtual text sensor for RPC device."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["text:203"] = {
            "name": name,
            "meta": {"ui": {"view": "label"}},
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["text:203"] = {"value": "lorem ipsum"}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("lorem ipsum")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-text:203-text_generic")

        monkeypatch.setitem(
            mock_rpc_device.status["text:203"], "value", "dolor sit amet"
        )
        mock_rpc_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("dolor sit amet")


@test.cases(
    test.case(
        "enum_generic",
        old_id="enum",
        new_id="enum_generic",
        role=None,
    ),
    test.case(
        "number_generic",
        old_id="number",
        new_id="number_generic",
        role=None,
    ),
    test.case(
        "number_current_humidity",
        old_id="number",
        new_id="number_current_humidity",
        role="current_humidity",
    ),
    test.case(
        "number_current_temperature",
        old_id="number",
        new_id="number_current_temperature",
        role="current_temperature",
    ),
    test.case(
        "text_generic",
        old_id="text",
        new_id="text_generic",
        role=None,
    ),
)
async def migrate_unique_id_virtual_components_roles(
    old_id: str,
    new_id: str,
    role: str | None,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(disable_async_remove_shelly_rpc_entities_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test migration of unique_id for virtual components to include role."""
    entry = await init_integration(hass, 3, skip_setup=True)
    unique_base = f"{MOCK_MAC}-{old_id}:200"
    old_unique_id = f"{unique_base}-{old_id}"
    new_unique_id = f"{unique_base}-{new_id}"

    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        if role:
            config[f"{old_id}:200"] = {"role": role}
        else:
            config[f"{old_id}:200"] = {}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        entity = entity_registry.async_get_or_create(
            suggested_object_id="test_name_test_sensor",
            disabled_by=None,
            domain=SENSOR_DOMAIN,
            platform=DOMAIN,
            unique_id=old_unique_id,
            config_entry=entry,
        )
        expect(entity.unique_id).to_equal(old_unique_id)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_entry = entity_registry.async_get("sensor.test_name_test_sensor")
        expect(entity_entry).to_be_truthy()
        expect(entity_entry.unique_id).to_equal(new_unique_id)

        expect(
            "Migrating unique_id for sensor.test_name_test_sensor" in caplog.text
        ).to_be_truthy()


@test.cases(
    test.case(
        "temperature",
        old_unique_id="123456789ABC-temperature:0-temperature_0",
        new_unique_id="123456789ABC-temperature:0-temperature_tc",
        entity_id="sensor.test_name_temperature",
    ),
    test.case(
        "humidity",
        old_unique_id="123456789ABC-humidity:0-humidity_0",
        new_unique_id="123456789ABC-humidity:0-humidity_rh",
        entity_id="sensor.test_name_humidity",
    ),
)
async def migrate_unique_id_rpc_sensor_description_key_rename(
    old_unique_id: str,
    new_unique_id: str,
    entity_id: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(disable_async_remove_shelly_rpc_entities_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test migration of RPC sensor unique_id after description key rename."""
    entry = await init_integration(hass, 2, skip_setup=True)

    entity = entity_registry.async_get_or_create(
        suggested_object_id=entity_id.split(".")[1],
        disabled_by=None,
        domain=SENSOR_DOMAIN,
        platform=DOMAIN,
        unique_id=old_unique_id,
        config_entry=entry,
    )
    expect(entity.unique_id).to_equal(old_unique_id)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get(entity_id)
    expect(entity_entry).to_be_truthy()
    expect(entity_entry.unique_id).to_equal(new_unique_id)

    expect(
        f"Migrating unique_id for {entity_id} entity" in caplog.text
    ).to_be_truthy()


@test
async def rpc_remove_text_virtual_sensor_when_mode_field(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(disable_async_remove_shelly_rpc_entities_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test virtual text sensor removed when mode changed to a field."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["text:200"] = {"name": None, "meta": {"ui": {"view": "field"}}}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["text:200"] = {"value": "lorem ipsum"}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        config_entry = await init_integration(hass, 3, skip_setup=True)
        device_entry = register_device(device_registry, config_entry)
        entity_id = register_entity(
            hass,
            SENSOR_DOMAIN,
            "test_name_text_200",
            "text:200-text_generic",
            config_entry,
            device_id=device_entry.id,
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test
async def rpc_remove_text_virtual_sensor_when_orphaned(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Virtual text sensor removed if removed from device configuration."""
    config_entry = await init_integration(hass, 3, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)
    entity_id = register_entity(
        hass,
        SENSOR_DOMAIN,
        "test_name_text_200",
        "text:200-text_generic",
        config_entry,
        device_id=device_entry.id,
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(entity_registry.async_get(entity_id)).to_be_none()


@test.cases(
    test.case(
        "with_unit",
        name="Virtual number sensor",
        entity_id="sensor.test_name_virtual_number_sensor",
        original_unit="W",
        expected_unit="W",
    ),
    test.case(
        "unit_map",
        name="Unit map",
        entity_id="sensor.test_name_unit_map",
        original_unit="m3/min",
        expected_unit="m³/min",
    ),
    test.case(
        "no_name_empty_unit",
        name=None,
        entity_id="sensor.test_name_number_203",
        original_unit="",
        expected_unit=None,
    ),
)
async def rpc_device_virtual_number_sensor(
    name: str | None,
    entity_id: str,
    original_unit: str,
    expected_unit: str | None,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test a virtual number sensor for RPC device."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["number:203"] = {
            "name": name,
            "min": 0,
            "max": 100,
            "meta": {"ui": {"step": 0.1, "unit": original_unit, "view": "label"}},
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["number:203"] = {"value": 34.5}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("34.5")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(expected_unit)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-number:203-number_generic")

        monkeypatch.setitem(mock_rpc_device.status["number:203"], "value", 56.7)
        mock_rpc_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("56.7")


@test
async def rpc_remove_number_virtual_sensor_when_mode_field(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(disable_async_remove_shelly_rpc_entities_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Virtual number sensor removed when mode changed to a field."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["number:200"] = {
            "name": None,
            "min": 0,
            "max": 100,
            "meta": {"ui": {"step": 1, "unit": "", "view": "field"}},
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["number:200"] = {"value": 67.8}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        config_entry = await init_integration(hass, 3, skip_setup=True)
        device_entry = register_device(device_registry, config_entry)
        entity_id = register_entity(
            hass,
            SENSOR_DOMAIN,
            "test_name_number_200",
            "number:200-number_generic",
            config_entry,
            device_id=device_entry.id,
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test
async def rpc_remove_number_virtual_sensor_when_orphaned(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Virtual number sensor removed if removed from device configuration."""
    config_entry = await init_integration(hass, 3, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)
    entity_id = register_entity(
        hass,
        SENSOR_DOMAIN,
        "test_name_number_200",
        "number:200-number_generic",
        config_entry,
        device_id=device_entry.id,
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(entity_registry.async_get(entity_id)).to_be_none()


@test.cases(
    test.case(
        "with_name",
        name="Virtual enum sensor",
        entity_id="sensor.test_name_virtual_enum_sensor",
        value="one",
        expected_state="Title 1",
    ),
    test.case(
        "no_name_unknown",
        name=None,
        entity_id="sensor.test_name_enum_203",
        value=None,
        expected_state=STATE_UNKNOWN,
    ),
)
async def rpc_device_virtual_enum_sensor(
    name: str | None,
    entity_id: str,
    value: str | None,
    expected_state: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test a virtual enum sensor for RPC device."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["enum:203"] = {
            "name": name,
            "options": ["one", "two", "three"],
            "meta": {
                "ui": {"view": "label", "titles": {"one": "Title 1", "two": None}}
            },
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["enum:203"] = {"value": value}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(expected_state)
        expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(
            SensorDeviceClass.ENUM
        )
        expect(state.attributes.get(ATTR_OPTIONS)).to_equal(
            ["Title 1", "two", "three"]
        )

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-enum:203-enum_generic")

        monkeypatch.setitem(mock_rpc_device.status["enum:203"], "value", "two")
        mock_rpc_device.mock_update()
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("two")


@test
async def rpc_remove_enum_virtual_sensor_when_mode_dropdown(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _disable_remove: None = Depends(disable_async_remove_shelly_rpc_entities_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Virtual enum sensor removed when mode changed to a dropdown."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["enum:200"] = {
            "name": None,
            "options": ["option 1", "option 2", "option 3"],
            "meta": {
                "ui": {
                    "view": "dropdown",
                    "titles": {"option 1": "Title 1", "option 2": None},
                }
            },
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["enum:200"] = {"value": "option 2"}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        config_entry = await init_integration(hass, 3, skip_setup=True)
        device_entry = register_device(device_registry, config_entry)
        entity_id = register_entity(
            hass,
            SENSOR_DOMAIN,
            "test_name_enum_200",
            "enum:200-enum_generic",
            config_entry,
            device_id=device_entry.id,
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(entity_registry.async_get(entity_id)).to_be_none()


@test
async def rpc_remove_enum_virtual_sensor_when_orphaned(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Virtual enum sensor removed if removed from device configuration."""
    config_entry = await init_integration(hass, 3, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)
    entity_id = register_entity(
        hass,
        SENSOR_DOMAIN,
        "test_name_enum_200",
        "enum:200-enum_generic",
        config_entry,
        device_id=device_entry.id,
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(entity_registry.async_get(entity_id)).to_be_none()


@test.cases(
    test.case("rgb", light_type="rgb"),
    test.case("rgbw", light_type="rgbw"),
)
async def rpc_rgbw_sensors(
    light_type: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: None = Depends(_registry_enabled_by_default),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test sensors for RGB/RGBW light."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config[f"{light_type}:0"] = {"id": 0}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status[f"{light_type}:0"] = {
            "temperature": {"tC": 54.3, "tF": 129.7},
            "aenergy": {"total": 45.141},
            "apower": 12.2,
            "current": 0.23,
            "voltage": 12.4,
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 2)

        entity_id = f"sensor.test_name_{light_type}_light_0_power"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("12.2")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfPower.WATT
        )
        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            f"123456789ABC-{light_type}:0-power_{light_type}"
        )

        entity_id = f"sensor.test_name_{light_type}_light_0_energy"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("0.045141")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfEnergy.KILO_WATT_HOUR
        )
        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            f"123456789ABC-{light_type}:0-energy_{light_type}"
        )

        entity_id = f"sensor.test_name_{light_type}_light_0_current"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("0.23")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfElectricCurrent.AMPERE
        )
        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            f"123456789ABC-{light_type}:0-current_{light_type}"
        )

        entity_id = f"sensor.test_name_{light_type}_light_0_voltage"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("12.4")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfElectricPotential.VOLT
        )
        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            f"123456789ABC-{light_type}:0-voltage_{light_type}"
        )

        entity_id = f"sensor.test_name_{light_type}_light_0_temperature"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("54.3")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfTemperature.CELSIUS
        )
        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            f"123456789ABC-{light_type}:0-temperature_{light_type}"
        )


@test.skip("requires freezer for time-based unavailable check")
async def rpc_device_sensor_goes_unavailable_on_disconnect() -> None:
    """Stub (freezer dependency)."""


@test
async def rpc_voltmeter_value(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC voltmeter value sensor."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_voltmeter_value"

    await init_integration(hass, 2)

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("12.34")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal("ppm")

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-voltmeter:100-voltmeter_value")


@test.skip("snapshot test - port deferred")
async def blu_trv_sensor_entity() -> None:
    """Stub (snapshot dependency)."""


@test
async def rpc_device_virtual_number_sensor_with_device_class(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test a virtual number sensor with device class for RPC device."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_humidity"
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["number:203"] = {
            "name": "Current humidity",
            "min": 0,
            "max": 100,
            "meta": {"ui": {"step": 1, "unit": "%", "view": "label"}},
            "role": "current_humidity",
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status.pop("humidity:0")
        status["number:203"] = {"value": 34}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            "123456789ABC-number:203-number_current_humidity"
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("34")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(PERCENTAGE)
        expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(
            SensorDeviceClass.HUMIDITY
        )


@test
async def rpc_object_role_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test object role based sensor."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["object:200"] = {
            "name": "Water consumption",
            "meta": {"ui": {"unit": "m3"}},
            "role": "water_consumption",
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["object:200"] = {"value": {"counter": {"total": 5.4}}}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get("sensor.test_name_water_consumption")
        expect(state).to_be_truthy()
        expect(state.state).to_equal("5.4")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfVolume.CUBIC_METERS
        )
        expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(
            SensorDeviceClass.WATER
        )


@test.skip("snapshot test - port deferred")
async def rpc_switch_energy_sensors() -> None:
    """Stub (snapshot dependency)."""


@test
async def rpc_switch_no_energy_returned_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: None = Depends(_registry_enabled_by_default),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test switch component without energy returned sensor."""
    with _patches() as monkeypatch:
        status = {
            "sys": {},
            "switch:0": {
                "id": 0,
                "output": True,
                "apower": 85.3,
                "aenergy": {"total": 1234567.89},
            },
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)
        await init_integration(hass, 3)

        expect(
            hass.states.get("sensor.test_name_test_switch_0_energy_returned")
        ).to_be_none()
        expect(
            hass.states.get("sensor.test_name_test_switch_0_energy_consumed")
        ).to_be_none()


@test.skip("snapshot test - port deferred")
async def rpc_shelly_ev_sensors() -> None:
    """Stub (snapshot dependency)."""


@test
async def block_friendly_name_sleeping_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test friendly name for restored sleeping sensor."""
    entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
    device = register_device(device_registry, entry)

    entity = entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        f"{MOCK_MAC}-sensor_0-temp",
        suggested_object_id="test_name_temperature",
        original_name="Test name temperature",
        disabled_by=None,
        config_entry=entry,
        device_id=device.id,
    )

    expect(entity.original_name).to_equal("Test name temperature")

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    expect(state).to_be_truthy()
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("Test name Temperature")

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device, "initialized", True)
        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity.entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("Test name Temperature")


@test
async def rpc_presence_component(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC sensor entity for presence component."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["presence"] = {"enable": True}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["presence"] = {"num_objects": 2}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        mock_config_entry = await init_integration(hass, 4)

        entity_id = f"{SENSOR_DOMAIN}.test_name_detected_objects"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("2")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-presence-presence_num_objects")

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "presence", "num_objects", 0
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("0")

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
    """Test RPC sensor entity for presencezone component."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["presencezone:201"] = {"name": "Other zone", "enable": True}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["presencezone:201"] = {"state": True, "num_objects": 3}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        mock_config_entry = await init_integration(hass, 4)

        entity_id = f"{SENSOR_DOMAIN}.test_name_other_zone_detected_objects"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("3")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(
            "123456789ABC-presencezone:201-presencezone_num_objects"
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "presencezone:201", "num_objects", 2
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("2")

        config = deepcopy(mock_rpc_device.config)
        config["presencezone:201"] = {"enable": False}
        monkeypatch.setattr(mock_rpc_device, "config", config)
        await hass.config_entries.async_reload(mock_config_entry.entry_id)
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def rpc_pm1_energy_consumed_sensor(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: None = Depends(_registry_enabled_by_default),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test energy sensors for switch component."""
    with _patches() as monkeypatch:
        status = {
            "sys": {},
            "pm1:0": {
                "id": 0,
                "voltage": 235.0,
                "current": 0.957,
                "apower": -220.3,
                "freq": 50.0,
                "aenergy": {"total": 3000.000},
                "ret_aenergy": {"total": 1000.000},
            },
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)
        await init_integration(hass, 3)

        state = hass.states.get(f"{SENSOR_DOMAIN}.test_name_energy")
        expect(state).to_be_truthy()
        expect(state.state).to_equal("3.0")

        state = hass.states.get(f"{SENSOR_DOMAIN}.test_name_energy_returned")
        expect(state).to_be_truthy()
        expect(state.state).to_equal("1.0")

        entity_id = f"{SENSOR_DOMAIN}.test_name_energy_consumed"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("2.0")

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-pm1:0-consumed_energy_pm1")


@test.cases(
    test.case("aenergy", key="aenergy"),
    test.case("ret_aenergy", key="ret_aenergy"),
)
async def rpc_pm1_energy_consumed_sensor_non_float_value(
    key: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: None = Depends(_registry_enabled_by_default),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test energy sensors for switch component."""
    entity_id = f"{SENSOR_DOMAIN}.test_name_energy_consumed"
    with _patches() as monkeypatch:
        status = {
            "sys": {},
            "pm1:0": {
                "id": 0,
                "voltage": 235.0,
                "current": 0.957,
                "apower": -220.3,
                "freq": 50.0,
                "aenergy": {"total": 3000.000},
                "ret_aenergy": {"total": 1000.000},
            },
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)
        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("2.0")

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "pm1:0", key, {"total": None}
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNKNOWN)


@test.skip("snapshot test - port deferred")
async def cury_sensor_entity() -> None:
    """Stub (snapshot dependency)."""


@test.skip("snapshot test - port deferred")
async def shelly_irrigation_weather_sensors() -> None:
    """Stub (snapshot/json fixture dependency)."""


@test
async def rpc_rgbcct_sensors(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test sensors for RGBCCT light."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["rgbcct:0"] = {"id": 0}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["rgbcct:0"] = {
            "aenergy": {"total": 45.141},
            "apower": 12.2,
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 2)

        entity_id = "sensor.test_name_power"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("12.2")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfPower.WATT
        )

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-rgbcct:0-power_rgbcct")
        expect(entry.name).to_be_none()
        expect(entry.translation_key).to_be_none()

        entity_id = "sensor.test_name_energy"
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("0.045141")
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
            UnitOfEnergy.KILO_WATT_HOUR
        )

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-rgbcct:0-energy_rgbcct")
        expect(entry.name).to_be_none()
