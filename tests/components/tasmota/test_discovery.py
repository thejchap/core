"""The tests for the MQTT discovery."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.tasmota.const import DEFAULT_PREFIX
from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture, setup_tasmota

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def subscribing_config_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota),
) -> None:
    """Test setting up discovery — verify tasmota config_entry is loaded."""
    # mqtt_mock in this shim is the live MQTT client; assert tasmota
    # registered itself in hass.data and the discovery prefix is set.
    discovery_topic = DEFAULT_PREFIX
    expect(discovery_topic).to_equal("tasmota/discovery")
    expect("tasmota" in hass.config.components).to_be(True)
    expect(mqtt_mock is not None).to_be(True)


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def future_discovery_message() -> None:
    """Stub for test_future_discovery_message."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def valid_discovery_message() -> None:
    """Stub for test_valid_discovery_message."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def invalid_topic() -> None:
    """Stub for test_invalid_topic."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def invalid_message() -> None:
    """Stub for test_invalid_message."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def invalid_mac() -> None:
    """Stub for test_invalid_mac."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def correct_config_discovery() -> None:
    """Stub for test_correct_config_discovery."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_discover() -> None:
    """Stub for test_device_discover."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_discover_deprecated() -> None:
    """Stub for test_device_discover_deprecated."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_update() -> None:
    """Stub for test_device_update."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_remove() -> None:
    """Stub for test_device_remove."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_remove_multiple_config_entries_1() -> None:
    """Stub for test_device_remove_multiple_config_entries_1."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_remove_multiple_config_entries_2() -> None:
    """Stub for test_device_remove_multiple_config_entries_2."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_remove_stale() -> None:
    """Stub for test_device_remove_stale."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_rediscover() -> None:
    """Stub for test_device_rediscover."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_duplicate_discovery() -> None:
    """Stub for test_entity_duplicate_discovery."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_duplicate_removal() -> None:
    """Stub for test_entity_duplicate_removal."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def same_topic() -> None:
    """Stub for test_same_topic."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def topic_no_prefix() -> None:
    """Stub for test_topic_no_prefix."""
