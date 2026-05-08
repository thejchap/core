"""Tests for the sensor provided by the CPU Speed integration."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.cpuspeed.const import DOMAIN
from homeassistant.components.cpuspeed.sensor import ATTR_ARCH, ATTR_BRAND, ATTR_HZ
from homeassistant.components.homeassistant import (
    DOMAIN as HOME_ASSISTANT_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import mock_config_entry as mock_config_entry_fixture, mock_cpuinfo

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
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def sensor(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cpuinfo: MagicMock = Depends(mock_cpuinfo),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test the CPU Speed sensor."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await async_setup_component(hass, "homeassistant", {})

    entry = entity_registry.async_get("sensor.cpu_speed")
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal(entry.config_entry_id)
    expect(entry.entity_category).to_be(None)

    state = hass.states.get("sensor.cpu_speed")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("3.2")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("CPU Speed")
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(SensorDeviceClass.FREQUENCY)

    expect(state.attributes.get(ATTR_ARCH)).to_equal("aargh")
    expect(state.attributes.get(ATTR_BRAND)).to_equal("Intel Ryzen 7")
    expect(state.attributes.get(ATTR_HZ)).to_equal(3.6)

    mock_cpuinfo.return_value = {}
    await hass.services.async_call(
        HOME_ASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: "sensor.cpu_speed"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.cpu_speed")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_ARCH)).to_equal("aargh")
    expect(state.attributes.get(ATTR_BRAND)).to_equal("Intel Ryzen 7")
    expect(state.attributes.get(ATTR_HZ)).to_equal(3.6)

    expect(entry.device_id).not_.to_be(None)
    device_entry = device_registry.async_get(entry.device_id)
    expect(device_entry).not_.to_be(None)
    expect(device_entry.identifiers).to_equal({(DOMAIN, entry.config_entry_id)})
    expect(device_entry.name).to_equal("CPU Speed")


@test
async def sensor_partial_info(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_cpuinfo: MagicMock = Depends(mock_cpuinfo),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test the CPU Speed sensor missing info."""
    mock_config_entry.add_to_hass(hass)

    # Pop some info from the mocked CPUSpeed
    mock_cpuinfo.return_value.pop("brand_raw")
    mock_cpuinfo.return_value.pop("arch_string_raw")

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.cpu_speed")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("3.2")
    expect(state.attributes.get(ATTR_ARCH)).to_be(None)
    expect(state.attributes.get(ATTR_BRAND)).to_be(None)
