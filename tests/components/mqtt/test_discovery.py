"""The tests for the MQTT discovery."""

import json
from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components import mqtt
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture
from tests.common import async_fire_mqtt_message
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
)

# Reference ``mqtt`` to avoid unused-import warnings; the symbol may also be
# useful for future re-enabled tests that need ``mqtt.DOMAIN`` etc.
_ = mqtt


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _mqtt: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires mqtt_config_entry_data parametrization not in tryke shim")
async def subscribing_config_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setting up discovery."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog fixture and parametrized topic/log inputs")
async def invalid_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test sending in invalid topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog fixture and parametrized discovery_topic")
async def invalid_json(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test sending in invalid JSON."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog fixture and parametrized domain inputs")
async def discovery_schema_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovery schema errors."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog fixture for log assertions")
async def invalid_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test sending in JSON that violates the platform schema."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog fixture for log assertions")
async def invalid_device_discovery_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test sending in JSON that violates the discovery schema."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog fixture for log assertions")
async def only_valid_components(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test for a valid component."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry fixture and parametrized discovery_topic")
async def correct_config_discovery_component(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test sending in correct JSON."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry fixture and parametrized discovery_topic")
async def correct_config_discovery_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test sending in correct JSON for a device."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized discovery payloads")
async def discovery_integration_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test integration info as part of discovery payload."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry/entity_registry/tag_mock/caplog and parametrize")
async def discovery_migration_to_device_base(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test migration from single component discovery to device based discovery."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog fixture and parametrized config")
async def discovery_migration_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that the unique_id is preserved during migration."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry/entity_registry/tag_mock/caplog and parametrize")
async def discovery_rollback_to_single_base(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test rollback from device based discovery to single component discovery."""
    _ = (hass, mqtt_mock)


@test.skip("requires parametrized discovery_topic and payload inputs")
async def discovery_availability(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device discovery availability."""
    _ = (hass, mqtt_mock)


@test.skip("requires parametrized discovery_topic and payload inputs")
async def discovery_component_availability_overridden(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test device discovery with overridden component availability."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized discovery_topic/config_message inputs")
async def discovery_with_invalid_integration_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovery with invalid integration info."""
    _ = (hass, mqtt_mock)


@test
async def discover_fan(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovering an MQTT fan."""
    _ = mqtt_mock
    async_fire_mqtt_message(
        hass,
        "homeassistant/fan/bla/config",
        '{ "name": "Beer", "command_topic": "test_topic" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("fan.beer")

    assert state is not None
    assert state.name == "Beer"
    assert ("fan", "bla") in hass.data["mqtt"].discovery_already_discovered


@test
async def discover_climate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovering an MQTT climate component."""
    _ = mqtt_mock
    data = (
        '{ "name": "ClimateTest",'
        '  "current_temperature_topic": "climate/bla/current_temp",'
        '  "temperature_command_topic": "climate/bla/target_temp" }'
    )

    async_fire_mqtt_message(hass, "homeassistant/climate/bla/config", data)
    await hass.async_block_till_done()

    state = hass.states.get("climate.ClimateTest")

    assert state is not None
    assert state.name == "ClimateTest"
    assert ("climate", "bla") in hass.data["mqtt"].discovery_already_discovered


@test
async def discover_alarm_control_panel(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovering an MQTT alarm control panel component."""
    _ = mqtt_mock
    data = (
        '{ "name": "AlarmControlPanelTest",'
        '  "state_topic": "test_topic",'
        '  "command_topic": "test_topic" }'
    )

    async_fire_mqtt_message(hass, "homeassistant/alarm_control_panel/bla/config", data)
    await hass.async_block_till_done()

    state = hass.states.get("alarm_control_panel.AlarmControlPanelTest")

    assert state is not None
    assert state.name == "AlarmControlPanelTest"
    assert ("alarm_control_panel", "bla") in hass.data[
        "mqtt"
    ].discovery_already_discovered


@test.skip("requires entity_registry fixture not in tryke shim")
async def discovery_with_default_entity_id_for_previous_deleted_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovering an MQTT entity with default_entity_id and unique_id."""
    _ = (hass, mqtt_mock)


@test
async def discovery_incl_nodeid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test sending in correct JSON with optional node_id included."""
    _ = mqtt_mock
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/my_node_id/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.beer")

    assert state is not None
    assert state.name == "Beer"
    assert ("binary_sensor", "my_node_id bla") in hass.data[
        "mqtt"
    ].discovery_already_discovered


@test.skip("requires caplog fixture for log assertions")
async def non_duplicate_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test for a non duplicate component."""
    _ = (hass, mqtt_mock)


@test
async def removal(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test removal of component through empty discovery message."""
    _ = mqtt_mock
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is not None

    async_fire_mqtt_message(hass, "homeassistant/binary_sensor/bla/config", "")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is None


@test
async def rediscover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test rediscover of removed component."""
    _ = mqtt_mock
    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is not None

    async_fire_mqtt_message(hass, "homeassistant/binary_sensor/bla/config", "")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is None

    async_fire_mqtt_message(
        hass,
        "homeassistant/binary_sensor/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.beer")
    assert state is not None


@test.skip("requires async_capture_events helper behavior in tryke shim")
async def rapid_rediscover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test immediate rediscover of removed component."""
    _ = (hass, mqtt_mock)


@test.skip("requires event listener behavior in tryke shim")
async def rapid_rediscover_unique(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test immediate rediscover of removed component."""
    _ = (hass, mqtt_mock)


@test.skip("requires event listener behavior in tryke shim")
async def rapid_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test immediate reconfigure of added component."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog fixture for log assertions")
async def duplicate_removal(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test for duplicate removal log."""
    _ = (hass, mqtt_mock)


@test.skip("requires hass_ws_client/device_registry/entity_registry and parametrize")
async def cleanup_device_manual(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test cleanup of a manually added device."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry/entity_registry and parametrize inputs")
async def cleanup_device_mqtt(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test cleanup of a device created via MQTT discovery."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry/entity_registry/caplog fixtures")
async def cleanup_device_mqtt_device_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test cleanup of a device created via MQTT device discovery."""
    _ = (hass, mqtt_mock)


@test.skip("requires hass_ws_client/device_registry/entity_registry fixtures")
async def cleanup_device_multiple_config_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test cleanup of a device with multiple config entries."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog/device_registry/entity_registry fixtures")
async def cleanup_device_multiple_config_entries_mqtt(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test cleanup via MQTT of a device with multiple config entries."""
    _ = (hass, mqtt_mock)


@test
async def discovery_expansion(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test expansion of abbreviated discovery payload."""
    _ = mqtt_mock
    data = (
        '{ "~": "some/base/topic",'
        '  "name": "DiscoveryExpansionTest1",'
        '  "stat_t": "test_topic/~",'
        '  "cmd_t": "~/test_topic",'
        '  "availability": ['
        "    {"
        '      "topic":"~/avail_item1",'
        '      "payload_available": "available",'
        '      "payload_not_available": "not_available"'
        "    },"
        "    {"
        '      "t":"avail_item2/~",'
        '      "pl_avail": "available",'
        '      "pl_not_avail": "not_available"'
        "    }"
        "  ],"
        '  "dev":{'
        '    "ids":["5706DF"],'
        '    "name":"DiscoveryExpansionTest1 Device",'
        '    "mdl":"Generic",'
        '    "hw":"rev1",'
        '    "sw":"1.2.3.4",'
        '    "mf":"None",'
        '    "sa":"default_area"'
        "  }"
        "}"
    )

    async_fire_mqtt_message(hass, "homeassistant/switch/bla/config", data)
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "avail_item2/some/base/topic", "available")
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state is not None
    assert state.name == "DiscoveryExpansionTest1"
    assert ("switch", "bla") in hass.data["mqtt"].discovery_already_discovered
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "test_topic/some/base/topic", "ON")

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_ON

    async_fire_mqtt_message(hass, "some/base/topic/avail_item1", "not_available")
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE


@test
async def discovery_expansion_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test expansion of abbreviated discovery payload."""
    _ = mqtt_mock
    data = (
        '{ "~": "some/base/topic",'
        '  "name": "DiscoveryExpansionTest1",'
        '  "stat_t": "test_topic/~",'
        '  "cmd_t": "~/test_topic",'
        '  "availability": {'
        '    "t":"~/avail_item1",'
        '    "pl_avail": "available",'
        '    "pl_not_avail": "not_available"'
        "  },"
        '  "dev":{'
        '    "ids":["5706DF"],'
        '    "name":"DiscoveryExpansionTest1 Device",'
        '    "mdl":"Generic",'
        '    "hw":"rev1",'
        '    "sw":"1.2.3.4",'
        '    "mf":"None",'
        '    "sa":"default_area"'
        "  }"
        "}"
    )

    async_fire_mqtt_message(hass, "homeassistant/switch/bla/config", data)
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "some/base/topic/avail_item1", "available")
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state is not None
    assert state.name == "DiscoveryExpansionTest1"
    assert ("switch", "bla") in hass.data["mqtt"].discovery_already_discovered
    assert state.state == STATE_UNKNOWN


@test.skip("requires caplog fixture for log assertions")
async def discovery_expansion_3(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test expansion of broken discovery payload."""
    _ = (hass, mqtt_mock)


@test
async def discovery_expansion_without_encoding_and_value_template_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test expansion of raw availability payload with a template as list."""
    _ = mqtt_mock
    data = (
        '{ "~": "some/base/topic",'
        '  "name": "DiscoveryExpansionTest1",'
        '  "stat_t": "test_topic/~",'
        '  "cmd_t": "~/test_topic",'
        '  "encoding":"",'
        '  "availability": [{'
        '    "topic":"~/avail_item1",'
        '    "payload_available": "1",'
        '    "payload_not_available": "0",'
        '    "value_template":"{{value|unpack(\'b\')}}"'
        "  }],"
        '  "dev":{'
        '    "ids":["5706DF"],'
        '    "name":"DiscoveryExpansionTest1 Device",'
        '    "mdl":"Generic",'
        '    "hw":"rev1",'
        '    "sw":"1.2.3.4",'
        '    "mf":"None",'
        '    "sa":"default_area"'
        "  }"
        "}"
    )

    async_fire_mqtt_message(hass, "homeassistant/switch/bla/config", data)
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "some/base/topic/avail_item1", b"\x01")
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state is not None
    assert state.name == "DiscoveryExpansionTest1"
    assert ("switch", "bla") in hass.data["mqtt"].discovery_already_discovered
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "some/base/topic/avail_item1", b"\x00")

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE


@test
async def discovery_expansion_without_encoding_and_value_template_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test expansion of raw availability payload with a template directly."""
    _ = mqtt_mock
    data = (
        '{ "~": "some/base/topic",'
        '  "name": "DiscoveryExpansionTest1",'
        '  "stat_t": "test_topic/~",'
        '  "cmd_t": "~/test_topic",'
        '  "availability_topic":"~/avail_item1",'
        '  "payload_available": "1",'
        '  "payload_not_available": "0",'
        '  "encoding":"",'
        '  "availability_template":"{{ value | unpack(\'b\') }}",'
        '  "dev":{'
        '    "ids":["5706DF"],'
        '    "name":"DiscoveryExpansionTest1 Device",'
        '    "mdl":"Generic",'
        '    "hw":"rev1",'
        '    "sw":"1.2.3.4",'
        '    "mf":"None",'
        '    "sa":"default_area"'
        "  }"
        "}"
    )

    async_fire_mqtt_message(hass, "homeassistant/switch/bla/config", data)
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "some/base/topic/avail_item1", b"\x01")
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state is not None
    assert state.name == "DiscoveryExpansionTest1"
    assert ("switch", "bla") in hass.data["mqtt"].discovery_already_discovered
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "some/base/topic/avail_item1", b"\x00")

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE


@test.skip("filesystem-based abbreviation check is not relevant under tryke shim")
async def missing_discover_abbreviations(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Check MQTT platforms for missing abbreviations."""
    _ = (hass, mqtt_mock)


@test
async def no_implicit_state_topic_switch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test no implicit state topic for switch."""
    _ = mqtt_mock
    data = '{ "name": "Test1", "command_topic": "cmnd" }'

    async_fire_mqtt_message(hass, "homeassistant/switch/bla/config", data)
    await hass.async_block_till_done()

    state = hass.states.get("switch.Test1")
    assert state is not None
    assert state.name == "Test1"
    assert ("switch", "bla") in hass.data["mqtt"].discovery_already_discovered
    assert state.state == STATE_UNKNOWN
    assert state.attributes["assumed_state"] is True

    async_fire_mqtt_message(hass, "homeassistant/switch/bla/state", "ON")

    state = hass.states.get("switch.Test1")
    assert state and state.state == STATE_UNKNOWN


@test.skip("requires mqtt_config_entry_data parametrization for discovery prefix")
async def complex_discovery_topic_prefix(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovery topic prefix with multiple slashes."""
    _ = (hass, mqtt_mock)


@test.skip("requires mqtt_client_mock fixture not in tryke shim")
async def mqtt_integration_discovery_flow_fitering_on_redundant_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test filtering on redundant discovery payload."""
    _ = (hass, mqtt_mock)


@test.skip("requires mqtt_client_mock/caplog/mock_mqtt_flow fixtures")
async def mqtt_discovery_flow_starts_once(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that MQTT discovery flow only starts once."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry/caplog fixtures")
async def clear_config_topic_disabled_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test clearing config topic for a disabled entity."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry fixture not in tryke shim")
async def clean_up_registry_monitoring(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test clean up of registry monitoring."""
    _ = (hass, mqtt_mock)


@test.skip("requires entity_registry fixture not in tryke shim")
async def unique_id_collission_has_priority(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that unique_id collisions have priority over default."""
    _ = (hass, mqtt_mock)


@test
async def update_with_bad_config_not_breaks_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test a bad update does not break discovery."""
    _ = mqtt_mock
    config1 = {
        "name": "sbfspot_12345",
        "state_topic": "homeassistant_test/sensor/sbfspot_0/state",
    }
    async_fire_mqtt_message(
        hass,
        "homeassistant/sensor/sbfspot_0/config",
        json.dumps(config1),
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.sbfspot_12345") is not None
    config2 = {
        "name": "sbfspot_12345",
        "availability": 1,
        "state_topic": "homeassistant_test/sensor/sbfspot_0/state",
    }
    async_fire_mqtt_message(
        hass,
        "homeassistant/sensor/sbfspot_0/config",
        json.dumps(config2),
    )
    await hass.async_block_till_done()
    config3 = {
        "name": "sbfspot_12345",
        "state_topic": "homeassistant_test/sensor/sbfspot_0/new_state_topic",
    }
    async_fire_mqtt_message(
        hass,
        "homeassistant/sensor/sbfspot_0/config",
        json.dumps(config3),
    )
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass,
        "homeassistant_test/sensor/sbfspot_0/new_state_topic",
        "new_value",
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.sbfspot_12345")
    assert state and state.state == "new_value"


@test.skip("requires parametrized signal_message inputs")
async def discovery_dispatcher_signal_type_messages(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovery dispatcher messages."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry/entity_registry and parametrized inputs")
async def shared_state_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that entities can share a state topic."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry/tag_mock and parametrized single_configs")
async def discovery_with_late_via_device_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovery with late via_device discovery."""
    _ = (hass, mqtt_mock)


@test.skip("requires device_registry/tag_mock and parametrized single_configs")
async def discovery_with_late_via_device_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovery with late via_device update."""
    _ = (hass, mqtt_mock)
