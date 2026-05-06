"""Tests for the Abode sensor device."""

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode import ATTR_DEVICE_ID
from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import requests_mock_fixture
from .common import setup_platform

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
def _abode_setup(
    _requests: requests_mock.Mocker = Depends(requests_mock_fixture),
) -> None:
    """Wire the autouse Abode HTTP mocks for tryke."""


@test
async def entity_registry(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(hass, SENSOR_DOMAIN)

    entry = entity_registry.async_get("sensor.environment_sensor_humidity")
    expect(entry.unique_id).to_equal("13545b21f4bdcd33d9abd461f8443e65-humidity")


@test
async def attributes(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the sensor attributes are correct."""
    await setup_platform(hass, SENSOR_DOMAIN)

    state = hass.states.get("sensor.environment_sensor_humidity")
    expect(state.state).to_equal("32.0")
    expect(state.attributes.get(ATTR_DEVICE_ID)).to_equal("RF:02148e70")
    expect(state.attributes.get("battery_low")).to_be_falsy()
    expect(state.attributes.get("no_response")).to_be_falsy()
    expect(state.attributes.get("device_type")).to_equal("LM")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(PERCENTAGE)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "Environment Sensor Humidity"
    )
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(SensorDeviceClass.HUMIDITY)
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_equal(
        SensorStateClass.MEASUREMENT
    )

    state = hass.states.get("sensor.environment_sensor_illuminance")
    expect(state.state).to_equal("1.0")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal("lx")
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_equal(
        SensorStateClass.MEASUREMENT
    )

    state = hass.states.get("sensor.environment_sensor_temperature")
    # Abodepy device JSON reports 19.5, but Home Assistant shows 19.4
    expect(abs(float(state.state) - 19.44444) < 1e-4).to_be_truthy()
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfTemperature.CELSIUS
    )
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_equal(
        SensorStateClass.MEASUREMENT
    )
