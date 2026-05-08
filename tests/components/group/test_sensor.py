"""Tryke port for the Group Sensor platform tests."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.group import DOMAIN
from homeassistant.components.group.sensor import DEFAULT_NAME
from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network

VALUES = [17, 20, 15.3]
SUM_VALUE = sum(VALUES)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level trigger fixture so tryke fully resolves Depends."""


@test
async def sensors_attributes_defined(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the sensors with explicit attributes (single non-parametrized case)."""
    config: dict[str, Any] = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": DEFAULT_NAME,
            "type": "sum",
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "unique_id": "very_unique_id",
            "device_class": SensorDeviceClass.WATER,
            "state_class": SensorStateClass.TOTAL_INCREASING,
            "unit_of_measurement": "m³",
        }
    }

    expect(await async_setup_component(hass, "sensor", config)).to_be(True)
    await hass.async_block_till_done()

    entity_ids = config["sensor"]["entities"]

    for entity_id, value in dict(zip(entity_ids, VALUES, strict=False)).items():
        hass.states.async_set(
            entity_id,
            str(value),
            {
                ATTR_DEVICE_CLASS: SensorDeviceClass.VOLUME,
                ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
                ATTR_UNIT_OF_MEASUREMENT: "L",
            },
        )
        await hass.async_block_till_done()

    # Allow the group sensor to react to all member updates.
    await hass.async_block_till_done()

    state = hass.states.get("sensor.sensor_group_sum")
    expect(state, "sensor.sensor_group_sum state").not_.to_be(None)
    assert state is not None  # narrow for type-checker / following accesses

    # Liter to m3 = 1:0.001
    expect(state.state).to_equal(str(float(SUM_VALUE * 0.001)))
    expect(state.attributes.get(ATTR_ENTITY_ID)).to_equal(entity_ids)
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(SensorDeviceClass.WATER)
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_equal(
        SensorStateClass.TOTAL_INCREASING
    )
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal("m³")


@test.skip("pending tryke port - 10-row parametrize across sensor types")
async def sensors2() -> None:
    """Stub for test_sensors2."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def not_enough_sensor_value() -> None:
    """Stub for test_not_enough_sensor_value."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload() -> None:
    """Stub for test_reload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_incorrect_state_with_ignore_non_numeric() -> None:
    """Stub for test_sensor_incorrect_state_with_ignore_non_numeric."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_incorrect_state_with_not_ignore_non_numeric() -> None:
    """Stub for test_sensor_incorrect_state_with_not_ignore_non_numeric."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_require_all_states() -> None:
    """Stub for test_sensor_require_all_states."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_calculated_properties() -> None:
    """Stub for test_sensor_calculated_properties."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_with_uoms_but_no_device_class() -> None:
    """Stub for test_sensor_with_uoms_but_no_device_class."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_calculated_properties_not_same() -> None:
    """Stub for test_sensor_calculated_properties_not_same."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_calculated_result_fails_on_uom() -> None:
    """Stub for test_sensor_calculated_result_fails_on_uom."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_calculated_properties_not_convertible_device_class() -> None:
    """Stub for test_sensor_calculated_properties_not_convertible_device_class."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def last_sensor() -> None:
    """Stub for test_last_sensor."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def first_available_sensor() -> None:
    """Stub for test_first_available_sensor."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_attributes_added_when_entity_info_available() -> None:
    """Stub for test_sensors_attributes_added_when_entity_info_available."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_state_class_no_uom_not_available() -> None:
    """Stub for test_sensor_state_class_no_uom_not_available."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_different_attributes_ignore_non_numeric() -> None:
    """Stub for test_sensor_different_attributes_ignore_non_numeric."""
