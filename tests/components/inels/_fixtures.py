"""Tryke fixtures for the iNELS integration."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import DATA_MQTT
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_mqtt_mock


@fixture
async def mqtt_mock(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[Any]:
    """Set up MQTT mock for iNELS tests."""
    # Patch yaml config loader so MQTT setup doesn't fail looking for
    # tests/testing_config/configuration.yaml (the pytest mqtt_mock fixture
    # depends on `mock_hass_config` which does this).
    with patch("homeassistant.config.load_yaml_config_file", return_value={}):
        try:
            await setup_mqtt_mock(hass)
        except AttributeError:
            # The shim fails on `entry.runtime_data` access — MQTT stores its
            # client on `hass.data[DATA_MQTT]` instead.
            pass
        # Pull out the real MQTT client object that integration code sees.
        mqtt_data = hass.data.get(DATA_MQTT)
        client = mqtt_data.client if mqtt_data is not None else None
        if client is not None:
            client.connected = True
        yield client
