"""Test the SensorPush sensors."""

from datetime import timedelta
import time

from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth import (
    FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS,
)
from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.components.sensorpush.const import DOMAIN
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import HTPWX_EMPTY_SERVICE_INFO, HTPWX_SERVICE_INFO

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.bluetooth import (
    inject_bluetooth_service_info,
    patch_all_discovered_devices,
    patch_bluetooth_time,
)
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
    start_monotonic = time.monotonic()
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info(hass, HTPWX_SERVICE_INFO)
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(3)

    temp_sensor = hass.states.get("sensor.htp_xw_f4d_temperature")
    temp_sensor_attributes = temp_sensor.attributes
    expect(temp_sensor.state).to_equal("20.11")
    expect(temp_sensor_attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "HTP.xw F4D Temperature"
    )
    expect(temp_sensor_attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("°C")
    expect(temp_sensor_attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    monotonic_now = start_monotonic + FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1

    with (
        patch_bluetooth_time(
            monotonic_now,
        ),
        patch_all_discovered_devices([]),
    ):
        async_fire_time_changed(
            hass,
            dt_util.utcnow()
            + timedelta(seconds=FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1),
        )
        await hass.async_block_till_done()

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    temp_sensor = hass.states.get("sensor.htp_xw_f4d_temperature")
    expect(temp_sensor.state).to_equal(STATE_UNAVAILABLE)
    inject_bluetooth_service_info(hass, HTPWX_EMPTY_SERVICE_INFO)
    await hass.async_block_till_done()

    temp_sensor = hass.states.get("sensor.htp_xw_f4d_temperature")
    expect(temp_sensor.state).to_equal("20.11")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
