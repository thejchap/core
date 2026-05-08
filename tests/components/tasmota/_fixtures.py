"""Tryke fixtures for the Tasmota integration."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock, patch

from hatasmota.discovery import get_status_sensor_entities
from tryke import Depends, fixture

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import DATA_MQTT
from homeassistant.components.tasmota.const import (
    CONF_DISCOVERY_PREFIX,
    DEFAULT_PREFIX,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_mqtt_mock


@fixture
async def disable_debounce() -> AsyncGenerator[None]:
    """Set MQTT debounce timer to zero."""
    with patch("hatasmota.mqtt.DEBOUNCE_TIMEOUT", 0):
        yield


@fixture
async def disable_status_sensor() -> AsyncGenerator[None]:
    """Disable Tasmota status sensor (default)."""
    with patch("hatasmota.discovery.get_status_sensor_entities", wraps=None):
        yield


@fixture
async def enable_status_sensor() -> AsyncGenerator[None]:
    """Enable Tasmota status sensor (use real implementation)."""
    with patch(
        "hatasmota.discovery.get_status_sensor_entities",
        wraps=get_status_sensor_entities,
    ):
        yield


@fixture
async def mqtt_mock(
    hass: HomeAssistant = Depends(hass_fixture),
    _debounce: None = Depends(disable_debounce),
    _status_sensor: None = Depends(disable_status_sensor),
) -> AsyncGenerator[Any]:
    """Set up MQTT mock for Tasmota tests.

    Mirrors the pytest ``mqtt_mock`` fixture by wrapping the real ``MQTT``
    client instance in a MagicMock(wraps=...) so test bodies can both invoke
    real publish/subscribe and assert via ``mqtt_mock.async_publish.assert_*``.
    """
    real_mqtt = mqtt.MQTT
    mock_mqtt_instance: MagicMock | None = None

    def create_mock_mqtt(*args: Any, **kwargs: Any) -> MagicMock:
        nonlocal mock_mqtt_instance
        real_instance = real_mqtt(*args, **kwargs)
        spec = [*dir(real_instance), "_mqttc"]
        mock_mqtt_instance = MagicMock(
            return_value=real_instance,
            spec_set=spec,
            wraps=real_instance,
        )
        return mock_mqtt_instance

    # Patch yaml config loader so MQTT setup doesn't fail looking for
    # tests/testing_config/configuration.yaml.
    with (
        patch("homeassistant.config.load_yaml_config_file", return_value={}),
        patch("homeassistant.components.mqtt.MQTT", side_effect=create_mock_mqtt),
    ):
        try:
            await setup_mqtt_mock(hass)
        except AttributeError:
            # Shim fails on `entry.runtime_data` access — MQTT stores its
            # client on hass.data[DATA_MQTT] instead.
            pass

        if mock_mqtt_instance is not None:
            mock_mqtt_instance.connected = True

        # Yield the wrapped mock if we captured one, else fall back to the
        # raw client from hass.data.
        if mock_mqtt_instance is not None:
            yield mock_mqtt_instance
        else:
            mqtt_data = hass.data.get(DATA_MQTT)
            client = mqtt_data.client if mqtt_data is not None else None
            if client is not None:
                client.connected = True
            yield client


async def setup_tasmota_helper(hass: HomeAssistant) -> None:
    """Set up the Tasmota integration for tests."""
    hass.config.components.add("tasmota")

    entry = MockConfigEntry(
        data={CONF_DISCOVERY_PREFIX: DEFAULT_PREFIX},
        domain=DOMAIN,
        title="Tasmota",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert "tasmota" in hass.config.components


@fixture
async def setup_tasmota(
    hass: HomeAssistant = Depends(hass_fixture),
    _mqtt: Any = Depends(mqtt_mock),
) -> None:
    """Set up Tasmota."""
    await setup_tasmota_helper(hass)
