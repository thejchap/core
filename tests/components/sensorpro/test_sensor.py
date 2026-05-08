"""Test the SensorPro sensors."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.components.sensorpro.const import DOMAIN
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant

from . import SENSORPRO_SERVICE_INFO

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
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("sensor"))).to_equal(0)
    inject_bluetooth_service_info(hass, SENSORPRO_SERVICE_INFO)
    await hass.async_block_till_done()
    expect(len(hass.states.async_all("sensor"))).to_equal(4)

    humid_sensor = hass.states.get("sensor.t201_eeff_humidity")
    humid_sensor_attrs = humid_sensor.attributes
    expect(humid_sensor.state).to_equal("50.21")
    expect(humid_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal("T201 EEFF Humidity")
    expect(humid_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("%")
    expect(humid_sensor_attrs[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
