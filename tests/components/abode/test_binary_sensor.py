"""Tests for the Abode binary sensor device."""

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode import ATTR_DEVICE_ID
from homeassistant.components.abode.const import ATTRIBUTION
from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
)
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    STATE_OFF,
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
    await setup_platform(hass, BINARY_SENSOR_DOMAIN)

    entry = entity_registry.async_get("binary_sensor.front_door")
    expect(entry.unique_id).to_equal("2834013428b6035fba7d4054aa7b25a3")


@test
async def attributes(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the binary sensor attributes are correct."""
    await setup_platform(hass, BINARY_SENSOR_DOMAIN)

    state = hass.states.get("binary_sensor.front_door")
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_ATTRIBUTION)).to_equal(ATTRIBUTION)
    expect(state.attributes.get(ATTR_DEVICE_ID)).to_equal("RF:01430030")
    expect(state.attributes.get("battery_low")).to_be_falsy()
    expect(state.attributes.get("no_response")).to_be_falsy()
    expect(state.attributes.get("device_type")).to_equal("Door Contact")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Front Door")
    expect(state.attributes.get(ATTR_DEVICE_CLASS)).to_equal(
        BinarySensorDeviceClass.WINDOW
    )
