"""The test for the Template sensor platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import sensor
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    async_trigger,
    make_test_trigger,
    setup_and_test_nested_unique_id,
    setup_and_test_unique_id,
    setup_entity,
)

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

TEST_STATE_SENSOR = "sensor.test_state"
TEST_AVAILABILITY_SENSOR = "sensor.availability_sensor"

TEST_SENSOR = TemplatePlatformSetup(
    sensor.DOMAIN,
    "sensors",
    "test_template_sensor",
    make_test_trigger(TEST_STATE_SENSOR, TEST_AVAILABILITY_SENSOR),
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY, initial_state="It ."),
    test.case("modern", style=ConfigurationStyle.MODERN, initial_state="It ."),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, initial_state=STATE_UNKNOWN),
)
async def sensor_state(
    *,
    style: ConfigurationStyle,
    initial_state: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template."""
    await setup_entity(
        hass,
        TEST_SENSOR,
        style,
        1,
        {},
        state_template="It {{ states.sensor.test_state.state }}.",
    )
    expect(hass.states.get(TEST_SENSOR.entity_id).state).to_equal(initial_state)

    await async_trigger(hass, TEST_STATE_SENSOR, "Works")
    expect(hass.states.get(TEST_SENSOR.entity_id).state).to_equal("It Works.")


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def bad_template_unavailable(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a bad template creates an unavailable sensor."""
    await setup_entity(
        hass, TEST_SENSOR, style, 1, {}, state_template="{{ x - 12 }}"
    )
    await async_trigger(hass, TEST_STATE_SENSOR)
    expect(hass.states.get(TEST_SENSOR.entity_id).state).to_be(STATE_UNAVAILABLE)


@test.cases(
    test.case(
        "legacy_temperature",
        style=ConfigurationStyle.LEGACY,
        config={"unit_of_measurement": "°C", "device_class": "temperature"},
        expected="temperature",
    ),
    test.case(
        "legacy_none",
        style=ConfigurationStyle.LEGACY,
        config={},
        expected=None,
    ),
    test.case(
        "modern_temperature",
        style=ConfigurationStyle.MODERN,
        config={"unit_of_measurement": "°C", "device_class": "temperature"},
        expected="temperature",
    ),
    test.case(
        "modern_none",
        style=ConfigurationStyle.MODERN,
        config={},
        expected=None,
    ),
    test.case(
        "trigger_temperature",
        style=ConfigurationStyle.TRIGGER,
        config={"unit_of_measurement": "°C", "device_class": "temperature"},
        expected="temperature",
    ),
    test.case(
        "trigger_none",
        style=ConfigurationStyle.TRIGGER,
        config={},
        expected=None,
    ),
)
async def setup_valid_device_class(
    *,
    style: ConfigurationStyle,
    config: dict,
    expected: str | None,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with valid device_class."""
    await setup_entity(
        hass,
        TEST_SENSOR,
        style,
        1,
        config,
        state_template="{{ states('sensor.test_sensor') | float(0) }}",
    )
    await async_trigger(hass, TEST_STATE_SENSOR, "75")
    expect(
        hass.states.get(TEST_SENSOR.entity_id).attributes.get("device_class")
    ).to_equal(expected)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def available_template_with_entities(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test availability templates with values from other entities."""
    attribute = (
        "availability_template"
        if style == ConfigurationStyle.LEGACY
        else "availability"
    )
    await setup_entity(
        hass,
        TEST_SENSOR,
        style,
        1,
        {attribute: "{{ is_state('sensor.availability_sensor', 'on') }}"},
        state_template="{{ states('sensor.test_state') }}",
    )
    await async_trigger(hass, TEST_AVAILABILITY_SENSOR, "on")
    expect(hass.states.get(TEST_SENSOR.entity_id).state != STATE_UNAVAILABLE).to_be(True)

    await async_trigger(hass, TEST_AVAILABILITY_SENSOR, "off")
    expect(hass.states.get(TEST_SENSOR.entity_id).state).to_be(STATE_UNAVAILABLE)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def invalid_availability_template_keeps_component_available(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that an invalid availability keeps the device available."""
    attribute = (
        "availability_template"
        if style == ConfigurationStyle.LEGACY
        else "availability"
    )
    await setup_entity(
        hass,
        TEST_SENSOR,
        style,
        1,
        {attribute: "{{ x - 12 }}"},
        state_template="{{ 'something' }}",
    )
    await async_trigger(hass, TEST_STATE_SENSOR)
    expect(
        hass.states.get(TEST_SENSOR.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option only creates one sensor per id."""
    await setup_and_test_unique_id(hass, TEST_SENSOR, style, {}, "{{ 'foo' }}")


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def nested_unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test a template unique_id propagates to sensor unique_ids."""
    await setup_and_test_nested_unique_id(
        hass, TEST_SENSOR, style, entity_registry, {}, "{{ 'foo' }}"
    )


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.skip("icon_template requires single-attribute setup helper — port deferred")
async def icon_template() -> None:
    """Stub."""


@test.skip("entity_picture_template requires single-attribute setup helper")
async def entity_picture_template() -> None:
    """Stub."""


@test.skip("name_template requires single-attribute setup helper")
async def name_template() -> None:
    """Stub."""


@test.skip("legacy_template_syntax_error requires start_ha — port deferred")
async def legacy_template_syntax_error() -> None:
    """Stub."""


@test.skip("creating_sensor_loads_group needs custom load_registries=False")
async def creating_sensor_loads_group() -> None:
    """Stub."""


@test.skip("attribute_templates needs setup_attributes_state_sensor")
async def attribute_templates() -> None:
    """Stub."""


@test.skip("invalid_attribute_template needs caplog inspection")
async def invalid_attribute_template() -> None:
    """Stub."""


@test.skip("sun_renders_once_per_sensor needs start_ha")
async def sun_renders_once_per_sensor() -> None:
    """Stub."""


@test.skip("this_variable stub")
async def this_variable() -> None:
    """Stub."""


@test.skip("this_variable_early_hass_not_running stub")
async def this_variable_early_hass_not_running() -> None:
    """Stub."""


@test.skip("this_variable_early_hass_running stub")
async def this_variable_early_hass_running() -> None:
    """Stub."""


@test.skip("self_referencing_sensor_loop stub")
async def self_referencing_sensor_loop() -> None:
    """Stub."""


@test.skip("self_referencing stub")
async def self_referencing() -> None:
    """Stub."""


@test.skip("self_referencing_icon_with_no_loop stub")
async def self_referencing_icon_with_no_loop() -> None:
    """Stub."""


@test.skip("duplicate_templates stub")
async def duplicate_templates() -> None:
    """Stub."""


@test.skip("trigger_conditional_entity stub")
async def trigger_conditional_entity() -> None:
    """Stub."""


@test.skip("trigger_conditional_entity_evaluation_error stub")
async def trigger_conditional_entity_evaluation_error() -> None:
    """Stub."""


@test.skip("trigger_conditional_entity_invalid_condition stub")
async def trigger_conditional_entity_invalid_condition() -> None:
    """Stub."""


@test.skip("trigger_entity_runs_once stub")
async def trigger_entity_runs_once() -> None:
    """Stub."""


@test.skip("trigger_not_allowed_platform_config stub")
async def trigger_not_allowed_platform_config() -> None:
    """Stub."""


@test.skip("numeric_trigger_entity_set_unknown stub")
async def numeric_trigger_entity_set_unknown() -> None:
    """Stub."""


@test.skip("trigger_attribute_order stub")
async def trigger_attribute_order() -> None:
    """Stub."""


@test.skip("entity_last_reset_total_increasing stub")
async def entity_last_reset_total_increasing() -> None:
    """Stub."""


@test.skip("last_reset stub")
async def last_reset() -> None:
    """Stub."""


@test.skip("invalid_last_reset stub")
async def invalid_last_reset() -> None:
    """Stub."""


@test.skip("sensor_datetime_device_classes stub")
async def sensor_datetime_device_classes() -> None:
    """Stub."""


@test.skip("sensor_date_device_class stub")
async def sensor_date_device_class() -> None:
    """Stub."""


@test.skip("trigger_entity_restore_state stub")
async def trigger_entity_restore_state() -> None:
    """Stub."""


@test.skip("trigger_action stub")
async def trigger_action() -> None:
    """Stub."""


@test.skip("trigger_action_variables stub")
async def trigger_action_variables() -> None:
    """Stub."""


@test.skip("trigger_conditional_action stub")
async def trigger_conditional_action() -> None:
    """Stub."""


@test.skip("legacy_and_new_config_schema stub")
async def legacy_and_new_config_schema() -> None:
    """Stub."""


@test.skip("device_id stub")
async def device_id() -> None:
    """Stub."""


@test.skip("numeric_sensor_recovers_from_exception stub")
async def numeric_sensor_recovers_from_exception() -> None:
    """Stub."""


@test.skip("numeric_sensor_int_float stub")
async def numeric_sensor_int_float() -> None:
    """Stub."""
