"""Test the Leaone sensors."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.leaone.const import DOMAIN
from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth as enable_bluetooth_fixture, hass as hass_fixture

from . import SCALE_SERVICE_INFO, SCALE_SERVICE_INFO_2, SCALE_SERVICE_INFO_3


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
        unique_id="5F:5A:5C:52:D3:94",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("sensor"))).to_equal(0)

    inject_bluetooth_service_info(hass, SCALE_SERVICE_INFO)
    await hass.async_block_till_done()
    inject_bluetooth_service_info(hass, SCALE_SERVICE_INFO_2)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("sensor"))).to_equal(2)

    mass_sensor = hass.states.get("sensor.tzc4_d394_mass")
    mass_sensor_attrs = mass_sensor.attributes
    expect(mass_sensor.state).to_equal("77.11")
    expect(mass_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal("TZC4 D394 Mass")
    expect(mass_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("kg")
    expect(mass_sensor_attrs[ATTR_STATE_CLASS]).to_equal("measurement")

    mass_sensor = hass.states.get("sensor.tzc4_d394_non_stabilized_mass")
    mass_sensor_attrs = mass_sensor.attributes
    expect(mass_sensor.state).to_equal("77.11")
    expect(mass_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal("TZC4 D394 Non Stabilized Mass")
    expect(mass_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("kg")
    expect(mass_sensor_attrs[ATTR_STATE_CLASS]).to_equal("measurement")

    inject_bluetooth_service_info(hass, SCALE_SERVICE_INFO_3)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("sensor"))).to_equal(2)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
