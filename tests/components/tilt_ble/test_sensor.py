"""Test the Tilt Hydrometer BLE sensors."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import ATTR_STATE_CLASS, async_rounded_state
from homeassistant.components.tilt_ble.const import DOMAIN
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth as enable_bluetooth_fixture, hass as hass_fixture

from . import TILT_GREEN_SERVICE_INFO


@fixture
async def _trigger_executor(
    _bluetooth: None = Depends(enable_bluetooth_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def sensors(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting up creates the sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="F6:0F:28:F2:1F:CB",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info(hass, TILT_GREEN_SERVICE_INFO)
    await hass.async_block_till_done()
    # may trigger ibeacon integration as well since tilt uses ibeacon
    expect(len(hass.states.async_all()) >= 2).to_be(True)

    temp_sensor = hass.states.get("sensor.tilt_green_temperature")
    expect(temp_sensor is not None).to_be(True)

    temp_sensor_attribtes = temp_sensor.attributes
    expect(
        async_rounded_state(hass, "sensor.tilt_green_temperature", temp_sensor)
    ).to_equal("21.1")
    expect(temp_sensor_attribtes[ATTR_FRIENDLY_NAME]).to_equal("Tilt Green Temperature")
    expect(temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("°C")
    expect(temp_sensor_attribtes[ATTR_STATE_CLASS]).to_equal("measurement")

    temp_sensor = hass.states.get("sensor.tilt_green_specific_gravity")
    expect(temp_sensor is not None).to_be(True)

    temp_sensor_attribtes = temp_sensor.attributes
    expect(temp_sensor.state).to_equal("1.003")
    expect(temp_sensor_attribtes[ATTR_FRIENDLY_NAME]).to_equal("Tilt Green Specific Gravity")
    expect(temp_sensor_attribtes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
