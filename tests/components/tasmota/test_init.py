"""The tests for the Tasmota integration init."""

import copy
import json
from typing import Any
from unittest.mock import call

from tryke import Depends, expect, fixture, test

from homeassistant.components.tasmota.const import DEFAULT_PREFIX, DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    MockModule,
    async_fire_mqtt_message,
    mock_integration,
)
from tests.components.tasmota._fixtures import (
    mqtt_mock as mqtt_mock_fixture,
    setup_tasmota as setup_tasmota_fixture,
)
from tests.components.tasmota.test_common import (
    DEFAULT_CONFIG,
    DEFAULT_SENSOR_CONFIG,
    remove_device,
)
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.typing import WebSocketGenerator


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for tryke Depends() resolution."""
    return hass


@test
async def device_remove(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test removing a discovered device through device registry."""
    assert await async_setup_component(hass, "config", {})
    config = copy.deepcopy(DEFAULT_CONFIG)
    sensor_config = copy.deepcopy(DEFAULT_SENSOR_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    async_fire_mqtt_message(
        hass, f"{DEFAULT_PREFIX}/{mac}/sensors", json.dumps(sensor_config)
    )
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    expect(device_entry is not None).to_be(True)

    await remove_device(hass, hass_ws_client, device_entry.id)
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    expect(device_entry).to_be(None)

    mqtt_mock.async_publish.assert_has_calls(
        [
            call(f"tasmota/discovery/{mac}/config", "", 0, True),
            call(f"tasmota/discovery/{mac}/sensors", "", 0, True),
        ],
        any_order=True,
    )


@test
async def device_remove_non_tasmota_device(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test removing a non Tasmota device through device registry."""
    assert await async_setup_component(hass, "config", {})

    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
        return True

    mock_integration(
        hass,
        MockModule(
            "test", async_remove_config_entry_device=async_remove_config_entry_device
        ),
    )
    config_entry = MockConfigEntry(domain="test")
    config_entry.supports_remove_device = True
    config_entry.add_to_hass(hass)

    mac = "12:34:56:AB:CD:EF"
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, mac)},
    )
    expect(device_entry is not None).to_be(True)

    # Reset mock since setup_tasmota may have caused publishes during integration init
    mqtt_mock.async_publish.reset_mock()

    await remove_device(hass, hass_ws_client, device_entry.id, config_entry.entry_id)
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    expect(device_entry).to_be(None)

    mqtt_mock.async_publish.assert_not_called()


@test
async def device_remove_stale_tasmota_device(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test removing a stale (undiscovered) Tasmota device through device registry."""
    assert await async_setup_component(hass, "config", {})
    config_entry = hass.config_entries.async_entries("tasmota")[0]

    mac = "12:34:56:AB:CD:EF"
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, mac)},
    )
    expect(device_entry is not None).to_be(True)

    mqtt_mock.async_publish.reset_mock()

    await remove_device(hass, hass_ws_client, device_entry.id)
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    expect(device_entry).to_be(None)

    mqtt_mock.async_publish.assert_not_called()


@test
async def tasmota_ws_remove_discovered_device(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test Tasmota websocket device removal."""
    assert await async_setup_component(hass, "config", {})
    config = copy.deepcopy(DEFAULT_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    expect(device_entry is not None).to_be(True)

    tasmota_config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    await remove_device(
        hass, hass_ws_client, device_entry.id, tasmota_config_entry.entry_id
    )

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    expect(device_entry).to_be(None)
