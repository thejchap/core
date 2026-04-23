"""Tryke fixtures for mysensors config_flow tests."""

from __future__ import annotations

from tryke import Depends, fixture

from homeassistant.components.mqtt import DOMAIN as MQTT_DOMAIN
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture


@fixture
def mqtt(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Mock the MQTT integration presence."""
    hass.config.components.add(MQTT_DOMAIN)
