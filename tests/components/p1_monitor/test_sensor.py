"""Tests for the sensors provided by the P1 Monitor integration."""

from unittest.mock import MagicMock

from p1monitor import P1MonitorNoDataError
from tryke import Depends, expect, fixture, test

from homeassistant.components.p1_monitor.const import DOMAIN
from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    CURRENCY_EURO,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from ._fixtures import (
    init_integration,
    mock_config_entry,
    mock_p1monitor,
    p1_translations,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _translations: None = Depends(p1_translations),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def smartmeter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test the P1 Monitor - SmartMeter sensors."""
    entry_id = integration.entry_id

    state = hass.states.get("sensor.smartmeter_power_consumption")
    entry = entity_registry.async_get("sensor.smartmeter_power_consumption")
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{entry_id}_smartmeter_power_consumption")
    expect(state.state).to_equal("877")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "SmartMeter Power consumption"
    )
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(SensorStateClass.MEASUREMENT)
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(UnitOfPower.WATT)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(SensorDeviceClass.POWER)

    state = hass.states.get("sensor.smartmeter_energy_consumption_high_tariff")
    entry = entity_registry.async_get(
        "sensor.smartmeter_energy_consumption_high_tariff"
    )
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{entry_id}_smartmeter_energy_consumption_high")
    expect(state.state).to_equal("2770.133")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "SmartMeter Energy consumption - High tariff"
    )
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(
        SensorStateClass.TOTAL_INCREASING
    )
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfEnergy.KILO_WATT_HOUR
    )
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(SensorDeviceClass.ENERGY)

    state = hass.states.get("sensor.smartmeter_energy_tariff_period")
    entry = entity_registry.async_get("sensor.smartmeter_energy_tariff_period")
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{entry_id}_smartmeter_energy_tariff_period")
    expect(state.state).to_equal("high")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "SmartMeter Energy tariff period"
    )
    expect(ATTR_UNIT_OF_MEASUREMENT in state.attributes).to_be(False)
    expect(ATTR_DEVICE_CLASS in state.attributes).to_be(False)

    expect(entry.device_id is not None).to_be(True)
    device_entry = device_registry.async_get(entry.device_id)
    expect(device_entry is not None).to_be(True)
    expect(device_entry.identifiers).to_equal({(DOMAIN, f"{entry_id}_smartmeter")})
    expect(device_entry.manufacturer).to_equal("P1 Monitor")
    expect(device_entry.name).to_equal("SmartMeter")
    expect(device_entry.entry_type).to_be(dr.DeviceEntryType.SERVICE)
    expect(bool(device_entry.model)).to_be(False)
    expect(bool(device_entry.sw_version)).to_be(False)


@test
async def phases(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test the P1 Monitor - Phases sensors."""
    entry_id = integration.entry_id

    state = hass.states.get("sensor.phases_voltage_phase_l1")
    entry = entity_registry.async_get("sensor.phases_voltage_phase_l1")
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{entry_id}_phases_voltage_phase_l1")
    expect(state.state).to_equal("233.6")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Phases Voltage phase L1")
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(SensorStateClass.MEASUREMENT)
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfElectricPotential.VOLT
    )
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(SensorDeviceClass.VOLTAGE)

    state = hass.states.get("sensor.phases_current_phase_l1")
    entry = entity_registry.async_get("sensor.phases_current_phase_l1")
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{entry_id}_phases_current_phase_l1")
    expect(state.state).to_equal("1.6")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Phases Current phase L1")
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(SensorStateClass.MEASUREMENT)
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfElectricCurrent.AMPERE
    )
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(SensorDeviceClass.CURRENT)

    state = hass.states.get("sensor.phases_power_consumed_phase_l1")
    entry = entity_registry.async_get("sensor.phases_power_consumed_phase_l1")
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{entry_id}_phases_power_consumed_phase_l1")
    expect(state.state).to_equal("315")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "Phases Power consumed phase L1"
    )
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(SensorStateClass.MEASUREMENT)
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(UnitOfPower.WATT)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(SensorDeviceClass.POWER)

    expect(entry.device_id is not None).to_be(True)
    device_entry = device_registry.async_get(entry.device_id)
    expect(device_entry is not None).to_be(True)
    expect(device_entry.identifiers).to_equal({(DOMAIN, f"{entry_id}_phases")})
    expect(device_entry.manufacturer).to_equal("P1 Monitor")
    expect(device_entry.name).to_equal("Phases")
    expect(device_entry.entry_type).to_be(dr.DeviceEntryType.SERVICE)
    expect(bool(device_entry.model)).to_be(False)
    expect(bool(device_entry.sw_version)).to_be(False)


@test
async def settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test the P1 Monitor - Settings sensors."""
    entry_id = integration.entry_id

    state = hass.states.get("sensor.settings_energy_consumption_price_low")
    entry = entity_registry.async_get("sensor.settings_energy_consumption_price_low")
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(
        f"{entry_id}_settings_energy_consumption_price_low"
    )
    expect(state.state).to_equal("0.20522")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "Settings Energy consumption price - Low"
    )
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(SensorStateClass.MEASUREMENT)
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )

    state = hass.states.get("sensor.settings_energy_production_price_low")
    entry = entity_registry.async_get("sensor.settings_energy_production_price_low")
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(
        f"{entry_id}_settings_energy_production_price_low"
    )
    expect(state.state).to_equal("0.20522")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "Settings Energy production price - Low"
    )
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(SensorStateClass.MEASUREMENT)
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )

    expect(entry.device_id is not None).to_be(True)
    device_entry = device_registry.async_get(entry.device_id)
    expect(device_entry is not None).to_be(True)
    expect(device_entry.identifiers).to_equal({(DOMAIN, f"{entry_id}_settings")})
    expect(device_entry.manufacturer).to_equal("P1 Monitor")
    expect(device_entry.name).to_equal("Settings")
    expect(device_entry.entry_type).to_be(dr.DeviceEntryType.SERVICE)
    expect(bool(device_entry.model)).to_be(False)
    expect(bool(device_entry.sw_version)).to_be(False)


@test
async def watermeter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test the P1 Monitor - WaterMeter sensors."""
    entry_id = integration.entry_id
    state = hass.states.get("sensor.watermeter_consumption_day")
    entry = entity_registry.async_get("sensor.watermeter_consumption_day")
    expect(entry is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(entry.unique_id).to_equal(f"{entry_id}_watermeter_consumption_day")
    expect(state.state).to_equal("112.0")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "WaterMeter Consumption day"
    )
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(
        SensorStateClass.TOTAL_INCREASING
    )
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(UnitOfVolume.LITERS)

    expect(entry.device_id is not None).to_be(True)
    device_entry = device_registry.async_get(entry.device_id)
    expect(device_entry is not None).to_be(True)
    expect(device_entry.identifiers).to_equal({(DOMAIN, f"{entry_id}_watermeter")})
    expect(device_entry.manufacturer).to_equal("P1 Monitor")
    expect(device_entry.name).to_equal("WaterMeter")
    expect(device_entry.entry_type).to_be(dr.DeviceEntryType.SERVICE)
    expect(bool(device_entry.model)).to_be(False)
    expect(bool(device_entry.sw_version)).to_be(False)


@test
async def no_watermeter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_p1monitor),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the P1 Monitor - Without WaterMeter sensors."""
    client.watermeter.side_effect = P1MonitorNoDataError
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.watermeter_consumption_day") is None).to_be(True)
    expect(hass.states.get("sensor.consumption_total") is None).to_be(True)
    expect(hass.states.get("sensor.pulse_count") is None).to_be(True)


@test
async def smartmeter_disabled_by_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test the P1 Monitor - SmartMeter sensors that are disabled by default."""
    entity_id = "sensor.smartmeter_gas_consumption"
    state = hass.states.get(entity_id)
    expect(state is None).to_be(True)

    entry = entity_registry.async_get(entity_id)
    expect(entry is not None).to_be(True)
    expect(entry.disabled).to_be(True)
    expect(entry.disabled_by).to_be(er.RegistryEntryDisabler.INTEGRATION)
