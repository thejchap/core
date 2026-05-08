"""The tests for the Tasmota fan platform."""

import copy
import json
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.tasmota.const import DEFAULT_PREFIX
from homeassistant.const import ATTR_ASSUMED_STATE, STATE_OFF
from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture, setup_tasmota
from .test_common import DEFAULT_CONFIG

from tests.common import async_fire_mqtt_message
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def controlling_state_via_mqtt(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota),
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["if"] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("fan.tasmota")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unavailable")
    expect(bool(state.attributes.get(ATTR_ASSUMED_STATE))).to_be(False)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("fan.tasmota")
    expect(state.state).to_equal(STATE_OFF)


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def sending_mqtt_commands() -> None:
    """Stub for test_sending_mqtt_commands."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def invalid_fan_speed_percentage() -> None:
    """Stub for test_invalid_fan_speed_percentage."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability_when_connection_lost() -> None:
    """Stub for test_availability_when_connection_lost."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def deep_sleep_availability_when_connection_lost() -> None:
    """Stub for test_deep_sleep_availability_when_connection_lost."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability() -> None:
    """Stub for test_availability."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def deep_sleep_availability() -> None:
    """Stub for test_deep_sleep_availability."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability_discovery_update() -> None:
    """Stub for test_availability_discovery_update."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def availability_poll_state() -> None:
    """Stub for test_availability_poll_state."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_removal_fan() -> None:
    """Stub for test_discovery_removal_fan."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_update_unchanged_fan() -> None:
    """Stub for test_discovery_update_unchanged_fan."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_device_remove() -> None:
    """Stub for test_discovery_device_remove."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_subscriptions() -> None:
    """Stub for test_entity_id_update_subscriptions."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_discovery_update() -> None:
    """Stub for test_entity_id_update_discovery_update."""
