"""Test the OralB sensors."""

from datetime import timedelta
import time

from tryke import Depends, expect, fixture, test

from homeassistant.components.bluetooth import (
    FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS,
    async_address_present,
)
from homeassistant.components.oralb.const import DOMAIN
from homeassistant.const import ATTR_ASSUMED_STATE, ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import (
    ORALB_IO_SERIES_4_SERVICE_INFO,
    ORALB_IO_SERIES_6_SERVICE_INFO,
    ORALB_SERVICE_INFO,
)
from ._fixtures import mock_bluetooth

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.bluetooth import (
    inject_bluetooth_service_info,
    inject_bluetooth_service_info_bleak,
    patch_all_discovered_devices,
    patch_bluetooth_time,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import entity_registry_enabled_by_default


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(mock_bluetooth),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires translation injection (state translation_key for toothbrush_state)")
async def sensors(
    _trigger: None = Depends(_trigger_executor),
    _registry: None = Depends(entity_registry_enabled_by_default),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up creates the sensors."""
    start_monotonic = time.monotonic()
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ORALB_SERVICE_INFO.address,
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("sensor"))).to_equal(0)
    inject_bluetooth_service_info(hass, ORALB_SERVICE_INFO)
    await hass.async_block_till_done()
    expect(len(hass.states.async_all("sensor"))).to_equal(9)

    toothbrush_sensor = hass.states.get("sensor.triumph_d36_48be")
    toothbrush_sensor_attrs = toothbrush_sensor.attributes
    expect(toothbrush_sensor.state).to_equal("running")
    expect(toothbrush_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal("Triumph D36 48BE")
    expect(ATTR_ASSUMED_STATE in toothbrush_sensor_attrs).to_be(False)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    # Fastforward time without BLE advertisements
    monotonic_now = start_monotonic + FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1

    with (
        patch_bluetooth_time(monotonic_now),
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

    # All of these devices are sleepy so we should still be available
    toothbrush_sensor = hass.states.get("sensor.triumph_d36_48be")
    expect(toothbrush_sensor.state).to_equal("running")


@test.skip("requires translation injection (entity_id slug brushing_mode needs translation)")
async def sensors_io_series_4(
    _trigger: None = Depends(_trigger_executor),
    _registry: None = Depends(entity_registry_enabled_by_default),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up creates the sensors with an io series 4."""


@test.skip("requires translation injection (entity_id slug battery needs translation)")
async def sensors_battery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test receiving battery percentage."""
