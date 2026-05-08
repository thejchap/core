"""The tests for the Template Binary sensor platform."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import binary_sensor
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
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

TEST_STATE_ENTITY_ID = "sensor.test_state"
TEST_ATTRIBUTE_ENTITY_ID = "sensor.test_attribute"
TEST_AVAILABILITY_ENTITY_ID = "binary_sensor.test_availability"

TEST_BINARY_SENSOR = TemplatePlatformSetup(
    binary_sensor.DOMAIN,
    "sensors",
    "test_binary_sensor",
    make_test_trigger(
        TEST_STATE_ENTITY_ID,
        TEST_ATTRIBUTE_ENTITY_ID,
        TEST_AVAILABILITY_ENTITY_ID,
    ),
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def setup_minimal(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setup."""
    await setup_entity(
        hass, TEST_BINARY_SENSOR, style, 1, {}, state_template="{{ True }}"
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
    expect(state).not_.to_be(None)
    expect(state.name).to_equal(TEST_BINARY_SENSOR.object_id)
    expect(state.state).to_be(STATE_ON)
    expect(state.attributes).to_equal({"friendly_name": TEST_BINARY_SENSOR.object_id})


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def setup_with_device_class(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setup with device_class."""
    await setup_entity(
        hass,
        TEST_BINARY_SENSOR,
        style,
        1,
        {"device_class": "motion"},
        state_template="{{ True }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
    expect(state).not_.to_be(None)
    expect(state.name).to_equal(TEST_BINARY_SENSOR.object_id)
    expect(state.state).to_be(STATE_ON)
    expect(state.attributes["device_class"]).to_equal("motion")


@test.cases(
    test.case(
        "legacy_icon",
        style=ConfigurationStyle.LEGACY,
        attribute="icon_template",
        attribute_value=(
            "{% if is_state('sensor.test_state', 'on') %}mdi:check{% endif %}"
        ),
        initial_state="",
        attr="icon",
        expected="mdi:check",
    ),
    test.case(
        "modern_icon",
        style=ConfigurationStyle.MODERN,
        attribute="icon",
        attribute_value=(
            "{% if is_state('sensor.test_state', 'on') %}mdi:check{% endif %}"
        ),
        initial_state="",
        attr="icon",
        expected="mdi:check",
    ),
    test.case(
        "trigger_icon",
        style=ConfigurationStyle.TRIGGER,
        attribute="icon",
        attribute_value=(
            "{% if is_state('sensor.test_state', 'on') %}mdi:check{% endif %}"
        ),
        initial_state=None,
        attr="icon",
        expected="mdi:check",
    ),
    test.case(
        "legacy_picture",
        style=ConfigurationStyle.LEGACY,
        attribute="entity_picture_template",
        attribute_value=(
            "{% if is_state('sensor.test_state', 'on') %}/local/sensor.png{% endif %}"
        ),
        initial_state="",
        attr="entity_picture",
        expected="/local/sensor.png",
    ),
    test.case(
        "modern_picture",
        style=ConfigurationStyle.MODERN,
        attribute="picture",
        attribute_value=(
            "{% if is_state('sensor.test_state', 'on') %}/local/sensor.png{% endif %}"
        ),
        initial_state="",
        attr="entity_picture",
        expected="/local/sensor.png",
    ),
    test.case(
        "trigger_picture",
        style=ConfigurationStyle.TRIGGER,
        attribute="picture",
        attribute_value=(
            "{% if is_state('sensor.test_state', 'on') %}/local/sensor.png{% endif %}"
        ),
        initial_state=None,
        attr="entity_picture",
        expected="/local/sensor.png",
    ),
)
async def icon_or_picture_template(
    *,
    style: ConfigurationStyle,
    attribute: str,
    attribute_value: str,
    initial_state: str | None,
    attr: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test icon and entity_picture templates."""
    await setup_entity(
        hass,
        TEST_BINARY_SENSOR,
        style,
        1,
        {attribute: attribute_value},
        state_template="{{ 1 == 1 }}",
    )
    state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
    expect(state.attributes.get(attr)).to_equal(initial_state)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
    expect(state.attributes[attr]).to_equal(expected)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def availability_template(
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
        TEST_BINARY_SENSOR,
        style,
        1,
        {attribute: "{{ is_state('binary_sensor.test_availability', 'on') }}"},
        state_template="{{ 1 == 1 }}",
    )
    await async_trigger(hass, TEST_AVAILABILITY_ENTITY_ID, STATE_ON)
    expect(
        hass.states.get(TEST_BINARY_SENSOR.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY_ID, STATE_OFF)
    expect(hass.states.get(TEST_BINARY_SENSOR.entity_id).state).to_be(STATE_UNAVAILABLE)


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
        TEST_BINARY_SENSOR,
        style,
        1,
        {attribute: "{{ x - 12 }}"},
        state_template="{{ 1 == 1 }}",
    )
    expect(
        hass.states.get(TEST_BINARY_SENSOR.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option."""
    await setup_and_test_unique_id(
        hass, TEST_BINARY_SENSOR, style, None, "{{ True }}"
    )


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
    """Test a template unique_id propagates."""
    await setup_and_test_nested_unique_id(
        hass, TEST_BINARY_SENSOR, style, entity_registry, None, "{{ True }}"
    )


@test.cases(
    test.case(
        "legacy_legacy",
        config={"binary_sensor": {"platform": "template"}},
        domain=binary_sensor.DOMAIN,
    ),
    test.case(
        "legacy_missing_mandatory",
        config={"binary_sensor": {"platform": "template", "sensors": {"foo bar": {}}}},
        domain=binary_sensor.DOMAIN,
    ),
    test.case(
        "modern_missing",
        config={"template": {"binary_sensor": {}}},
        domain="template",
    ),
)
async def setup_invalid_sensors(
    *,
    config: dict[str, Any],
    domain: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with invalid configuration."""
    from homeassistant.setup import async_setup_component

    await async_setup_component(hass, domain, config)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(len(hass.states.async_entity_ids("binary_sensor"))).to_equal(0)


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("state test creates MockConfigEntry per case — port deferred")
async def state() -> None:
    """Stub: requires snapshot/config-entry interplay."""


@test.skip("attribute_templates depends on caplog — port deferred")
async def attribute_templates() -> None:
    """Stub."""


@test.skip("invalid_attribute_template depends on caplog — port deferred")
async def invalid_attribute_template() -> None:
    """Stub."""


@test.skip("match_all stub — port deferred")
async def match_all() -> None:
    """Stub."""


@test.skip("binary_sensor_state stub — port deferred")
async def binary_sensor_state() -> None:
    """Stub."""


@test.skip("delay_on requires freezer + async_fire_time_changed — port deferred")
async def delay_on() -> None:
    """Stub."""


@test.skip("delay_off requires freezer + async_fire_time_changed — port deferred")
async def delay_off() -> None:
    """Stub."""


@test.skip("available_without_availability_template stub — port deferred")
async def available_without_availability_template() -> None:
    """Stub."""


@test.skip("no_update_template_match_all stub — port deferred")
async def no_update_template_match_all() -> None:
    """Stub."""


@test.skip("template_icon_validation_error stub — port deferred")
async def template_icon_validation_error() -> None:
    """Stub."""


@test.skip("restore_state requires mock_restore_cache — port deferred")
async def restore_state() -> None:
    """Stub."""


@test.skip("template_with_trigger_templated_auto_off stub — port deferred")
async def template_with_trigger_templated_auto_off() -> None:
    """Stub."""


@test.skip("template_trigger_delay_on_and_auto_off stub — port deferred")
async def template_trigger_delay_on_and_auto_off() -> None:
    """Stub."""


@test.skip("template_multiple_states_delay_on stub — port deferred")
async def template_multiple_states_delay_on() -> None:
    """Stub."""


@test.skip("template_with_trigger_auto_off_cancel stub — port deferred")
async def template_with_trigger_auto_off_cancel() -> None:
    """Stub."""


@test.skip("trigger_with_negative_time_periods stub — port deferred")
async def trigger_with_negative_time_periods() -> None:
    """Stub."""


@test.skip("trigger_template_delay_with_multiple_triggers stub")
async def trigger_template_delay_with_multiple_triggers() -> None:
    """Stub."""


@test.skip("trigger_entity_restore_state stub — port deferred")
async def trigger_entity_restore_state() -> None:
    """Stub."""


@test.skip("trigger_entity_restore_state_auto_off stub")
async def trigger_entity_restore_state_auto_off() -> None:
    """Stub."""


@test.skip("trigger_entity_restore_state_auto_off_expired stub")
async def trigger_entity_restore_state_auto_off_expired() -> None:
    """Stub."""


@test.skip("saving_auto_off stub")
async def saving_auto_off() -> None:
    """Stub."""


@test.skip("trigger_entity_restore_invalid_auto_off_time_data stub")
async def trigger_entity_restore_invalid_auto_off_time_data() -> None:
    """Stub."""


@test.skip("trigger_entity_restore_invalid_auto_off_time_key stub")
async def trigger_entity_restore_invalid_auto_off_time_key() -> None:
    """Stub."""


@test.skip("device_id stub — port deferred")
async def device_id() -> None:
    """Stub."""


@test.skip("flow_preview stub — port deferred")
async def flow_preview() -> None:
    """Stub."""
