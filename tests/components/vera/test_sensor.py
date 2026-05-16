"""Vera tests."""

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pyvera as pv
from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import async_rounded_state
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, LIGHT_LUX, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import vera_component_factory as vera_component_factory_fx
from .common import ComponentFactory, new_simple_controller_config

from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


async def run_sensor_test(
    hass: HomeAssistant,
    vera_component_factory: ComponentFactory,
    category: int,
    class_property: str,
    assert_states: tuple[tuple[Any, Any]],
    assert_unit_of_measurement: str | None = None,
    setup_callback: Callable[[pv.VeraController], None] | None = None,
) -> None:
    """Test generic sensor."""
    vera_device: pv.VeraSensor = MagicMock(spec=pv.VeraSensor)
    vera_device.device_id = 1
    vera_device.vera_device_id = vera_device.device_id
    vera_device.comm_failure = False
    vera_device.name = "dev1"
    vera_device.category = category
    setattr(vera_device, class_property, "33")
    entity_id = "sensor.dev1_1"

    component_data = await vera_component_factory.configure_component(
        hass=hass,
        controller_config=new_simple_controller_config(
            devices=(vera_device,), setup_callback=setup_callback
        ),
    )
    update_callback = component_data.controller_data[0].update_callback

    for initial_value, state_value in assert_states:
        setattr(vera_device, class_property, initial_value)
        update_callback(vera_device)
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        expect(async_rounded_state(hass, entity_id, state)).to_equal(state_value)
        if assert_unit_of_measurement:
            expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(
                assert_unit_of_measurement
            )


@test
async def temperature_sensor_f(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""

    def setup_callback(controller: pv.VeraController) -> None:
        controller.temperature_units = "F"

    await run_sensor_test(
        hass=hass,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_TEMPERATURE_SENSOR,
        class_property="temperature",
        assert_states=(("33", "0.6"), ("44", "6.7")),
        setup_callback=setup_callback,
    )


@test
async def temperature_sensor_c(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""
    await run_sensor_test(
        hass=hass,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_TEMPERATURE_SENSOR,
        class_property="temperature",
        assert_states=(("33", "33.0"), ("44", "44.0")),
    )


@test
async def light_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""
    await run_sensor_test(
        hass=hass,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_LIGHT_SENSOR,
        class_property="light",
        assert_states=(("12", "12"), ("13", "13")),
        assert_unit_of_measurement=LIGHT_LUX,
    )


@test
async def uv_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""
    await run_sensor_test(
        hass=hass,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_UV_SENSOR,
        class_property="light",
        assert_states=(("12", "12"), ("13", "13")),
        assert_unit_of_measurement="level",
    )


@test
async def humidity_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""
    await run_sensor_test(
        hass=hass,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_HUMIDITY_SENSOR,
        class_property="humidity",
        assert_states=(("12", "12"), ("13", "13")),
        assert_unit_of_measurement=PERCENTAGE,
    )


@test
async def power_meter_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""
    await run_sensor_test(
        hass=hass,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_POWER_METER,
        class_property="power",
        assert_states=(("12", "12"), ("13", "13")),
        assert_unit_of_measurement="W",
    )


@test
async def trippable_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""

    def setup_callback(controller: pv.VeraController) -> None:
        controller.get_devices()[0].is_trippable = True

    await run_sensor_test(
        hass=hass,
        vera_component_factory=vera_component_factory,
        category=999,
        class_property="is_tripped",
        assert_states=((True, "Tripped"), (False, "Not Tripped"), (True, "Tripped")),
        setup_callback=setup_callback,
    )


@test
async def unknown_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""

    def setup_callback(controller: pv.VeraController) -> None:
        controller.get_devices()[0].is_trippable = False

    await run_sensor_test(
        hass=hass,
        vera_component_factory=vera_component_factory,
        category=999,
        class_property="is_tripped",
        assert_states=((True, "Unknown"), (False, "Unknown"), (True, "Unknown")),
        setup_callback=setup_callback,
    )


@test
async def scene_controller_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
) -> None:
    """Test function."""
    vera_device: pv.VeraSensor = MagicMock(spec=pv.VeraSensor)
    vera_device.device_id = 1
    vera_device.vera_device_id = vera_device.device_id
    vera_device.comm_failure = False
    vera_device.name = "dev1"
    vera_device.category = pv.CATEGORY_SCENE_CONTROLLER
    vera_device.get_last_scene_id = MagicMock(return_value="id0")
    vera_device.get_last_scene_time = MagicMock(return_value="0000")
    entity_id = "sensor.dev1_1"

    component_data = await vera_component_factory.configure_component(
        hass=hass,
        controller_config=new_simple_controller_config(devices=(vera_device,)),
    )
    update_callback = component_data.controller_data[0].update_callback

    vera_device.get_last_scene_time.return_value = "1111"
    update_callback(vera_device)
    await hass.async_block_till_done()
    expect(hass.states.get(entity_id).state).to_equal("id0")


@test
async def switch_power_and_energy_sensors_created(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test that switches with metering expose power and energy sensors."""
    vera_switch: pv.VeraSwitch = MagicMock(spec=pv.VeraSwitch)
    vera_switch.device_id = 1
    vera_switch.vera_device_id = vera_switch.device_id
    vera_switch.comm_failure = False
    vera_switch.name = "metered_switch"
    vera_switch.category = 0
    vera_switch.power = 12
    vera_switch.energy = 3

    vera_sensor: pv.VeraSensor = MagicMock(spec=pv.VeraSensor)
    vera_sensor.device_id = 2
    vera_sensor.vera_device_id = vera_sensor.device_id
    vera_sensor.comm_failure = False
    vera_sensor.name = "dummy_sensor"
    vera_sensor.category = pv.CATEGORY_TEMPERATURE_SENSOR
    vera_sensor.temperature = "20"

    await vera_component_factory.configure_component(
        hass=hass,
        controller_config=new_simple_controller_config(
            devices=(vera_switch, vera_sensor)
        ),
    )
    await hass.async_block_till_done()

    power_entity_id = entity_registry.async_get_entity_id(
        "sensor", "vera", "vera_1111_1_power"
    )
    energy_entity_id = entity_registry.async_get_entity_id(
        "sensor", "vera", "vera_1111_1_energy"
    )

    expect(power_entity_id).not_.to_be(None)
    expect(energy_entity_id).not_.to_be(None)

    power_state = hass.states.get(power_entity_id)
    expect(power_state).not_.to_be(None)
    expect(power_state.state).to_equal("12")
    expect(power_state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("W")

    energy_state = hass.states.get(energy_entity_id)
    expect(energy_state).not_.to_be(None)
    expect(energy_state.state).to_equal("3")
    expect(energy_state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("kWh")


@test
async def switch_without_metering_does_not_create_power_energy_sensors(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    vera_component_factory: ComponentFactory = Depends(vera_component_factory_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test that non-metered switches do not create power/energy sensors."""
    vera_switch: pv.VeraSwitch = MagicMock(spec=pv.VeraSwitch)
    vera_switch.device_id = 1
    vera_switch.vera_device_id = vera_switch.device_id
    vera_switch.comm_failure = False
    vera_switch.name = "plain_switch"
    vera_switch.category = 0
    vera_switch.power = None
    vera_switch.energy = None

    vera_sensor: pv.VeraSensor = MagicMock(spec=pv.VeraSensor)
    vera_sensor.device_id = 2
    vera_sensor.vera_device_id = vera_sensor.device_id
    vera_sensor.comm_failure = False
    vera_sensor.name = "dummy_sensor"
    vera_sensor.category = pv.CATEGORY_TEMPERATURE_SENSOR
    vera_sensor.temperature = "20"

    await vera_component_factory.configure_component(
        hass=hass,
        controller_config=new_simple_controller_config(
            devices=(vera_switch, vera_sensor)
        ),
    )
    await hass.async_block_till_done()

    power_entity_id = entity_registry.async_get_entity_id(
        "sensor", "vera", "vera_1111_1_power"
    )
    energy_entity_id = entity_registry.async_get_entity_id(
        "sensor", "vera", "vera_1111_1_energy"
    )

    expect(power_entity_id).to_be(None)
    expect(energy_entity_id).to_be(None)
