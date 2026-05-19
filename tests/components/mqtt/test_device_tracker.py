"""The tests for the MQTT device_tracker platform."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components import device_tracker, mqtt
from homeassistant.const import STATE_HOME, STATE_NOT_HOME, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from ._fixtures import mqtt_mock as mqtt_mock_fixture
from .common import help_test_setting_blocked_attribute_via_mqtt_json_message
from tests.common import async_fire_mqtt_message
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
)

DEFAULT_CONFIG = {
    mqtt.DOMAIN: {
        device_tracker.DOMAIN: {
            "name": "test",
            "state_topic": "test-topic",
        }
    }
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _mqtt: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _make_mqtt_mock_entry(mqtt_mock: Any) -> Any:
    """Return a no-op coroutine returning ``mqtt_mock``.

    The original pytest ``mqtt_mock_entry`` fixture is a callable that sets
    up the MQTT integration on demand. In tryke the integration is set up
    eagerly by the ``mqtt_mock`` fixture in ``_fixtures.py``; this shim
    adapts the calling convention used by the ``help_test_*`` helpers.
    """

    async def _entry() -> Any:
        return mqtt_mock

    return _entry


@test
async def discover_device_tracker(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovering an MQTT device tracker component."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "test", "state_topic": "test_topic" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")

    assert state is not None
    assert state.name == "test"
    assert ("device_tracker", "bla") in hass.data["mqtt"].discovery_already_discovered


@test
async def discovery_broken(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test handling of bad discovery message."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "Beer" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.beer")
    assert state is None

    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "Beer", "state_topic": "required-topic" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.beer")
    assert state is not None
    assert state.name == "Beer"


@test.skip("caplog fixture not available in tryke shim")
async def non_duplicate_device_tracker_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test for a non duplicate component."""
    _ = (hass, mqtt_mock)


@test
async def device_tracker_removal(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test removal of component through empty discovery message."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()
    state = hass.states.get("device_tracker.beer")
    assert state is not None

    async_fire_mqtt_message(hass, "homeassistant/device_tracker/bla/config", "")
    await hass.async_block_till_done()
    state = hass.states.get("device_tracker.beer")
    assert state is None


@test
async def device_tracker_rediscover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test rediscover of removed component."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()
    state = hass.states.get("device_tracker.beer")
    assert state is not None

    async_fire_mqtt_message(hass, "homeassistant/device_tracker/bla/config", "")
    await hass.async_block_till_done()
    state = hass.states.get("device_tracker.beer")
    assert state is None

    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()
    state = hass.states.get("device_tracker.beer")
    assert state is not None


@test.skip("caplog fixture not available in tryke shim")
async def duplicate_device_tracker_removal(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test for a non duplicate component."""
    _ = (hass, mqtt_mock)


@test.skip("freezer fixture not available in tryke shim")
async def device_tracker_discovery_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test for a discovery update event."""
    _ = (hass, mqtt_mock)


@test.skip("hass_ws_client and registries fixtures not available in tryke shim")
async def cleanup_device_tracker(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test discovered device is cleaned up when removed from registry."""
    _ = (hass, mqtt_mock)


@test
async def setting_device_tracker_value_via_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the value via MQTT."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "test", "state_topic": "test-topic" }',
    )

    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")

    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "test-topic", "home")
    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_HOME

    async_fire_mqtt_message(hass, "test-topic", "not_home")
    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_NOT_HOME

    # Test an empty value is ignored and the state is retained
    async_fire_mqtt_message(hass, "test-topic", "")
    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_NOT_HOME


@test
async def setting_device_tracker_value_via_mqtt_message_and_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the value via MQTT."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        "{"
        '"name": "test", '
        '"state_topic": "test-topic", '
        '"value_template": "{% if value is equalto \\"proxy_for_home\\" %}home{% else %}not_home{% endif %}" '
        "}",
    )
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, "test-topic", "proxy_for_home")
    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_HOME

    async_fire_mqtt_message(hass, "test-topic", "anything_for_not_home")
    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_NOT_HOME


@test
async def setting_device_tracker_value_via_mqtt_message_and_template2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the value via MQTT."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        "{"
        '"name": "test", '
        '"state_topic": "test-topic", '
        '"value_template": "{{ value | lower }}" '
        "}",
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "test-topic", "HOME")
    state = hass.states.get("device_Tracker.test")
    assert state.state == STATE_HOME

    async_fire_mqtt_message(hass, "test-topic", "NOT_HOME")
    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_NOT_HOME


@test
async def setting_device_tracker_location_via_mqtt_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the location via MQTT."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "test", "state_topic": "test-topic", "source_type": "router" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")
    assert state.attributes["source_type"] == "router"

    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "test-topic", "test-location")
    state = hass.states.get("device_tracker.test")
    assert state.state == "test-location"


@test
async def setting_device_tracker_location_via_lat_lon_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of the latitude and longitude via MQTT without state topic."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "test", "json_attributes_topic": "attributes-topic"}',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")
    assert state.attributes["source_type"] == "gps"

    assert state.state == STATE_UNKNOWN

    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743

    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":32.87336,"longitude": -117.22743, "gps_accuracy":1.5, "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 32.87336
    assert state.attributes["longitude"] == -117.22743
    assert state.attributes["gps_accuracy"] == 1.5
    # source_type is overridden by discovery
    assert state.attributes["source_type"] == "router"
    assert state.state == STATE_HOME

    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":50.1,"longitude": -2.1}',
    )
    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 50.1
    assert state.attributes["longitude"] == -2.1
    assert state.attributes["gps_accuracy"] == 0
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_NOT_HOME

    # incomplete coordinates results in unknown state
    async_fire_mqtt_message(hass, "attributes-topic", '{"longitude": -117.22743}')
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "attributes-topic", '{"latitude":32.87336}')
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_UNKNOWN

    # invalid coordinates results in unknown state
    async_fire_mqtt_message(
        hass, "attributes-topic", '{"longitude": -117.22743, "latitude":null}'
    )
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_UNKNOWN

    # Test number validation
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude": "32.87336","longitude": "-117.22743", "gps_accuracy": "1.5", "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert "gps_accuracy" not in state.attributes
    # source_type is overridden by discovery
    assert state.attributes["source_type"] == "router"
    assert state.state == STATE_UNKNOWN

    # Invalid GPS accuracy should default to 0; location updates as expected.
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude": 32.871234,"longitude": -117.21234, "gps_accuracy": "invalid", "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_NOT_HOME
    assert state.attributes["latitude"] == 32.871234
    assert state.attributes["longitude"] == -117.21234
    assert state.attributes["gps_accuracy"] == 0
    assert state.attributes["source_type"] == "router"

    # Invalid latitude
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude": null,"longitude": "-117.22743", "gps_accuracy": 1, "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.state == STATE_UNKNOWN

    # Invalid longitude
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude": 32.87336,"longitude": "unknown", "gps_accuracy": 1, "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.state == STATE_UNKNOWN


@test
async def setting_device_tracker_location_via_reset_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the automatic inference of zones via MQTT via reset."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        "{ "
        '"name": "test", '
        '"state_topic": "test-topic", '
        '"json_attributes_topic": "attributes-topic" '
        "}",
    )

    hass.states.async_set(
        "zone.school",
        "zoning",
        {
            "latitude": 30.0,
            "longitude": -100.0,
            "radius": 100,
            "friendly_name": "School",
        },
    )

    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")
    assert state.attributes["source_type"] == "gps"

    assert state.state == STATE_UNKNOWN

    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743

    # test reset and gps attributes
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":32.87336,"longitude": -117.22743, "gps_accuracy":1.5}',
    )
    async_fire_mqtt_message(hass, "test-topic", "None")

    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 32.87336
    assert state.attributes["longitude"] == -117.22743
    assert state.attributes["gps_accuracy"] == 1.5
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_HOME

    # test manual state override
    async_fire_mqtt_message(hass, "test-topic", "Work")

    state = hass.states.get("device_tracker.test")
    assert state.state == "Work"

    # test reset
    async_fire_mqtt_message(hass, "test-topic", "None")

    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_HOME

    # test reset inferring correct school area
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":30.0,"longitude":-100.0,"gps_accuracy":1.5}',
    )

    state = hass.states.get("device_tracker.test")
    assert state.state == "School"


@test
async def setting_device_tracker_location_via_abbr_reset_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of reset via abbreviated names and custom payloads via MQTT."""
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        "{ "
        '"name": "test", '
        '"state_topic": "test-topic", '
        '"json_attributes_topic": "attributes-topic", '
        '"pl_rst": "reset" '
        "}",
    )

    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")
    assert state.attributes["source_type"] == "gps"

    assert state.state == STATE_UNKNOWN

    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743

    # test custom reset payload and gps attributes
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":32.87336,"longitude": -117.22743, "gps_accuracy":1.5}',
    )
    async_fire_mqtt_message(hass, "test-topic", "reset")

    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 32.87336
    assert state.attributes["longitude"] == -117.22743
    assert state.attributes["gps_accuracy"] == 1.5
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_HOME

    # Override the GPS state via a direct state update
    async_fire_mqtt_message(hass, "test-topic", "office")
    state = hass.states.get("device_tracker.test")
    assert state.state == "office"

    # Test a GPS attributes update without a reset
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":32.87336,"longitude": -117.22743, "gps_accuracy":1.5}',
    )

    state = hass.states.get("device_tracker.test")
    assert state.state == "office"

    # Reset the manual set location;
    # this should calculate the location from GPS attributes.
    async_fire_mqtt_message(hass, "test-topic", "reset")
    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 32.87336
    assert state.attributes["longitude"] == -117.22743
    assert state.attributes["gps_accuracy"] == 1.5
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_HOME


@test
async def setting_blocked_attribute_via_mqtt_json_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_blocked_attribute_via_mqtt_json_message(
        hass,
        _make_mqtt_mock_entry(mqtt_mock),
        device_tracker.DOMAIN,
        DEFAULT_CONFIG,
        None,
    )


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def setup_with_modern_schema(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test setup using the modern schema."""
    _ = (hass, mqtt_mock)


@test.skip("requires mqtt_client_mock fixture for reloadable test")
async def reloadable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test reloading the MQTT platform."""
    _ = (hass, mqtt_mock)


@test.skip("requires per-test hass_config parametrization via mqtt_mock_entry")
async def skipped_async_ha_write_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test a write state command is only called when there is change."""
    _ = (hass, mqtt_mock)


@test.skip("requires caplog and parametrized hass_config")
async def value_template_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test the rendering of MQTT value template fails."""
    _ = (hass, mqtt_mock)
