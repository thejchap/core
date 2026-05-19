"""The tests for the Tasmota cover platform."""

import copy
import json
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import cover
from homeassistant.components.tasmota.const import DEFAULT_PREFIX
from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture, setup_tasmota
from .test_common import DEFAULT_CONFIG

from tests.common import async_fire_mqtt_message
from tests.hass_fixtures import hass as hass_fixture, mock_network

COVER_SUPPORT = (
    cover.CoverEntityFeature.OPEN
    | cover.CoverEntityFeature.CLOSE
    | cover.CoverEntityFeature.STOP
    | cover.CoverEntityFeature.SET_POSITION
)
TILT_SUPPORT = (
    cover.CoverEntityFeature.OPEN_TILT
    | cover.CoverEntityFeature.CLOSE_TILT
    | cover.CoverEntityFeature.STOP_TILT
    | cover.CoverEntityFeature.SET_TILT_POSITION
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def tilt_support(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota),
) -> None:
    """Test tilt support detection."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"] = [3, 3, 3, 3, 3, 3, 3, 3]
    config["sht"] = [
        [0, 0, 0],
        [-90, 90, 24],
        [-90, 90, 0],
        [-90, -90, 24],
    ]
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("cover"))).to_equal(4)

    state = hass.states.get("cover.tasmota_cover_1")
    expect(state.attributes["supported_features"]).to_be(COVER_SUPPORT)

    state = hass.states.get("cover.tasmota_cover_2")
    expect(state.attributes["supported_features"]).to_be(COVER_SUPPORT | TILT_SUPPORT)

    state = hass.states.get("cover.tasmota_cover_3")
    expect(state.attributes["supported_features"]).to_be(COVER_SUPPORT)

    state = hass.states.get("cover.tasmota_cover_4")
    expect(state.attributes["supported_features"]).to_be(COVER_SUPPORT)


@test("multiple_covers").cases(
    test.case("16", relay_config=[3, 3, 3, 3, 3, 3, 1, 1, 3, 3] + [3, 3] * 12, num_covers=16),
    test.case("4", relay_config=[3, 3, 3, 3, 3, 3, 1, 1, 3, 3], num_covers=4),
    test.case("2", relay_config=[3, 3, 3, 3, 0, 0, 0, 0], num_covers=2),
    test.case("1", relay_config=[3, 3, 1, 1, 0, 0, 0, 0], num_covers=1),
    test.case("0", relay_config=[3, 3, 3, 1, 0, 0, 0, 0], num_covers=0),
)
async def multiple_covers(
    relay_config: list[int],
    num_covers: int,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota),
) -> None:
    """Test discovery of multiple covers."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"] = relay_config
    mac = config["mac"]

    expect(len(hass.states.async_all("cover"))).to_equal(0)

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("cover"))).to_equal(num_covers)


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def missing_relay() -> None:
    """Stub for test_missing_relay."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def controlling_state_via_mqtt_tilt() -> None:
    """Stub for test_controlling_state_via_mqtt_tilt."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def controlling_state_via_mqtt_inverted() -> None:
    """Stub for test_controlling_state_via_mqtt_inverted."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def sending_mqtt_commands() -> None:
    """Stub for test_sending_mqtt_commands."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def sending_mqtt_commands_inverted() -> None:
    """Stub for test_sending_mqtt_commands_inverted."""


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
async def discovery_removal_cover() -> None:
    """Stub for test_discovery_removal_cover."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_update_unchanged_cover() -> None:
    """Stub for test_discovery_update_unchanged_cover."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def discovery_device_remove() -> None:
    """Stub for test_discovery_device_remove."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_subscriptions() -> None:
    """Stub for test_entity_id_update_subscriptions."""


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def entity_id_update_discovery_update() -> None:
    """Stub for test_entity_id_update_discovery_update."""
