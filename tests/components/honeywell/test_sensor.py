"""Test honeywell sensor."""

from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import aiosomecomfort
from aiosomecomfort.device import Device
from aiosomecomfort.location import Location
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from ._fixtures import (
    CURRENTTEMPERATURE,
    COOLLOWERSETPOINTLIMIT,
    COOLUPPERSETPOINTLIMIT,
    HEATLOWERSETPOINTLIMIT,
    HEATUPPERSETPOINTLIMIT,
    NEXTCOOLPERIOD,
    NEXTHEATPERIOD,
    client,
    config_entry as config_entry_fx,
    device as device_fx,
    location as location_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

OUTDOORTEMP = 5
OUTDOORHUMIDITY = 25


_FAKE_TRANSLATIONS = {
    "component.honeywell.entity.sensor.outdoor_temperature.name":
        "Outdoor temperature",
    "component.honeywell.entity.sensor.outdoor_humidity.name":
        "Outdoor humidity",
    "component.sensor.entity_component.temperature.name": "Temperature",
    "component.sensor.entity_component.humidity.name": "Humidity",
}


async def _fake_get_translations(hass, language, category, integrations=None, config_flow=None):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _client: MagicMock = Depends(client),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@fixture
def device_with_outdoor_sensor() -> AsyncMock:
    """Mock a somecomfort.Device with outdoor sensor data."""
    mock_device = create_autospec(aiosomecomfort.device.Device, instance=True)
    mock_device.deviceid = 1234567
    mock_device._data = {
        "canControlHumidification": False,
        "hasFan": False,
    }
    mock_device.system_mode = "off"
    mock_device.name = "device3"
    mock_device.current_temperature = CURRENTTEMPERATURE
    mock_device.mac_address = "macaddress1"
    mock_device.temperature_unit = "C"
    mock_device.outdoor_temperature = OUTDOORTEMP
    mock_device.outdoor_humidity = OUTDOORHUMIDITY
    mock_device.has_humidifier = False
    mock_device.has_dehumidifier = False
    mock_device.raw_ui_data = {
        "SwitchOffAllowed": True,
        "SwitchAutoAllowed": True,
        "SwitchCoolAllowed": True,
        "SwitchHeatAllowed": True,
        "SwitchEmergencyHeatAllowed": True,
        "HeatUpperSetptLimit": HEATUPPERSETPOINTLIMIT,
        "HeatLowerSetptLimit": HEATLOWERSETPOINTLIMIT,
        "CoolUpperSetptLimit": COOLUPPERSETPOINTLIMIT,
        "CoolLowerSetptLimit": COOLLOWERSETPOINTLIMIT,
        "HeatNextPeriod": NEXTHEATPERIOD,
        "CoolNextPeriod": NEXTCOOLPERIOD,
    }
    mock_device.raw_fan_data = {
        "fanModeOnAllowed": True,
        "fanModeAutoAllowed": True,
        "fanModeCirculateAllowed": True,
    }
    mock_device.raw_dr_data = {"CoolSetpLimit": None, "HeatSetpLimit": None}
    return mock_device


@test.cases(
    test.case("celsius", unit="C", temp=5),
    test.case("fahrenheit", unit="F", temp=-15),
)
async def outdoor_sensor(
    *,
    unit: str,
    temp: int,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    location: Location = Depends(location_fx),
    sensor_device: AsyncMock = Depends(device_with_outdoor_sensor),
) -> None:
    """Test outdoor temperature sensor."""
    sensor_device.temperature_unit = unit
    location.devices_by_id[sensor_device.deviceid] = sensor_device
    config_entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    temperature_state = hass.states.get("sensor.device3_outdoor_temperature")
    humidity_state = hass.states.get("sensor.device3_outdoor_humidity")

    expect(temperature_state).not_.to_be(None)
    expect(humidity_state).not_.to_be(None)
    expect(float(temperature_state.state)).to_equal(temp)
    expect(float(humidity_state.state)).to_equal(25)


@test.cases(
    test.case("celsius", unit="C", temp=5),
    test.case("fahrenheit", unit="F", temp=-15),
)
async def indoor_sensor(
    *,
    unit: str,
    temp: int,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    location: Location = Depends(location_fx),
    device: Device = Depends(device_fx),
) -> None:
    """Test indoor temperature sensor with no outdoor sensors."""
    device.temperature_unit = unit
    device.current_temperature = 5
    device.current_humidity = 25
    location.devices_by_id[device.deviceid] = device
    config_entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.device1_outdoor_temperature")).to_be(None)
    expect(hass.states.get("sensor.device1_outdoor_humidity")).to_be(None)

    temperature_state = hass.states.get("sensor.device1_temperature")
    humidity_state = hass.states.get("sensor.device1_humidity")

    expect(temperature_state).not_.to_be(None)
    expect(humidity_state).not_.to_be(None)
    expect(float(temperature_state.state)).to_equal(temp)
    expect(humidity_state.state).to_equal("25")
