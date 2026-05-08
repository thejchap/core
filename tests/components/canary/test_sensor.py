"""The tests for the Canary sensor platform."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.canary.const import DOMAIN, MANUFACTURER
from homeassistant.components.canary.sensor import (
    ATTR_AIR_QUALITY,
    STATE_AIR_QUALITY_ABNORMAL,
    STATE_AIR_QUALITY_NORMAL,
    STATE_AIR_QUALITY_VERY_ABNORMAL,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util.dt import utcnow

from . import init_integration, mock_device, mock_location, mock_reading
from ._fixtures import canary, mock_ffmpeg

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ffmpeg: None = Depends(mock_ffmpeg),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def sensors_pro(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    canary: MagicMock = Depends(canary),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test the creation and values of the sensors for Canary Pro."""
    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.59"),
    ]

    with patch("homeassistant.components.canary.PLATFORMS", ["sensor"]):
        await init_integration(hass)

    sensors = {
        "dining_room_home_dining_room_temperature": (
            "20_temperature",
            "21.12",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            None,
        ),
        "dining_room_home_dining_room_humidity": (
            "20_humidity",
            "50.46",
            PERCENTAGE,
            SensorDeviceClass.HUMIDITY,
            None,
        ),
        "dining_room_home_dining_room_air_quality": (
            "20_air_quality",
            "0.59",
            None,
            None,
            "mdi:weather-windy",
        ),
    }

    for sensor_id, data in sensors.items():
        entity_entry = entity_registry.async_get(f"sensor.{sensor_id}")
        expect(entity_entry).not_.to_be(None)
        expect(entity_entry.original_device_class).to_equal(data[3])
        expect(entity_entry.unique_id).to_equal(data[0])
        expect(entity_entry.original_icon).to_equal(data[4])

        state = hass.states.get(f"sensor.{sensor_id}")
        expect(state).not_.to_be(None)
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(data[2])
        expect(state.state).to_equal(data[1])

    device = device_registry.async_get_device(identifiers={(DOMAIN, "20")})
    expect(device).not_.to_be(None)
    expect(device.manufacturer).to_equal(MANUFACTURER)
    expect(device.name).to_equal("Dining Room")
    expect(device.model).to_equal("Canary Pro")


@test
async def sensors_attributes_pro(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    canary: MagicMock = Depends(canary),
) -> None:
    """Test the creation and values of the sensors attributes for Canary Pro."""
    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.59"),
    ]

    with patch("homeassistant.components.canary.PLATFORMS", ["sensor"]):
        await init_integration(hass)

    entity_id = "sensor.dining_room_home_dining_room_air_quality"
    state1 = hass.states.get(entity_id)
    expect(state1).not_.to_be(None)
    expect(state1.state).to_equal("0.59")
    expect(state1.attributes[ATTR_AIR_QUALITY]).to_equal(STATE_AIR_QUALITY_ABNORMAL)

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.4"),
    ]

    future = utcnow() + timedelta(seconds=30)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done(wait_background_tasks=True)

    state2 = hass.states.get(entity_id)
    expect(state2).not_.to_be(None)
    expect(state2.state).to_equal("0.4")
    expect(state2.attributes[ATTR_AIR_QUALITY]).to_equal(STATE_AIR_QUALITY_VERY_ABNORMAL)

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "1.0"),
    ]

    future += timedelta(seconds=30)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done(wait_background_tasks=True)

    state3 = hass.states.get(entity_id)
    expect(state3).not_.to_be(None)
    expect(state3.state).to_equal("1.0")
    expect(state3.attributes[ATTR_AIR_QUALITY]).to_equal(STATE_AIR_QUALITY_NORMAL)


@test
async def sensors_flex(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    canary: MagicMock = Depends(canary),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test the creation and values of the sensors for Canary Flex."""
    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Flex")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("battery", "70.4567"),
        mock_reading("wifi", "-57"),
    ]

    with patch("homeassistant.components.canary.PLATFORMS", ["sensor"]):
        await init_integration(hass)

    sensors = {
        "dining_room_home_dining_room_battery": (
            "20_battery",
            "70.46",
            PERCENTAGE,
            SensorDeviceClass.BATTERY,
            None,
        ),
        "dining_room_home_dining_room_wifi": (
            "20_wifi",
            "-57.0",
            SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            SensorDeviceClass.SIGNAL_STRENGTH,
            None,
        ),
    }

    for sensor_id, data in sensors.items():
        entity_entry = entity_registry.async_get(f"sensor.{sensor_id}")
        expect(entity_entry).not_.to_be(None)
        expect(entity_entry.original_device_class).to_equal(data[3])
        expect(entity_entry.unique_id).to_equal(data[0])
        expect(entity_entry.original_icon).to_equal(data[4])

        state = hass.states.get(f"sensor.{sensor_id}")
        expect(state).not_.to_be(None)
        expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(data[2])
        expect(state.state).to_equal(data[1])
