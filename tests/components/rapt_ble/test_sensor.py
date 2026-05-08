"""Test the RAPT Pill BLE sensors."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.rapt_ble.const import DOMAIN
from homeassistant.components.sensor import ATTR_STATE_CLASS, SensorStateClass
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant

from . import COMPLETE_SERVICE_INFO, RAPT_MAC

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def sensors(
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up creates the sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=RAPT_MAC,
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info(hass, COMPLETE_SERVICE_INFO)
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(3)

    temp_sensor = hass.states.get("sensor.rapt_pill_0666_battery")
    expect(temp_sensor is not None).to_be(True)

    temp_sensor_attributes = temp_sensor.attributes
    expect(temp_sensor.state).to_equal("43")
    expect(temp_sensor_attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "RAPT Pill 0666 Battery"
    )
    expect(temp_sensor_attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(PERCENTAGE)
    expect(temp_sensor_attributes[ATTR_STATE_CLASS]).to_equal(
        SensorStateClass.MEASUREMENT
    )

    temp_sensor = hass.states.get("sensor.rapt_pill_0666_temperature")
    expect(temp_sensor is not None).to_be(True)

    temp_sensor_attributes = temp_sensor.attributes
    expect(temp_sensor.state).to_equal("23.81")
    expect(temp_sensor_attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "RAPT Pill 0666 Temperature"
    )
    expect(temp_sensor_attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(
        UnitOfTemperature.CELSIUS
    )
    expect(temp_sensor_attributes[ATTR_STATE_CLASS]).to_equal(
        SensorStateClass.MEASUREMENT
    )

    temp_sensor = hass.states.get("sensor.rapt_pill_0666_specific_gravity")
    expect(temp_sensor is not None).to_be(True)

    temp_sensor_attributes = temp_sensor.attributes
    expect(temp_sensor.state).to_equal("1.0111")
    expect(temp_sensor_attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "RAPT Pill 0666 Specific Gravity"
    )
    expect(temp_sensor_attributes[ATTR_STATE_CLASS]).to_equal(
        SensorStateClass.MEASUREMENT
    )

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
