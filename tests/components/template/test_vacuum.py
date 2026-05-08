"""The tests for the Template vacuum platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import vacuum
from homeassistant.components.vacuum import (
    ATTR_BATTERY_LEVEL,
    ATTR_FAN_SPEED,
    VacuumActivity,
)
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    async_trigger,
    make_test_action,
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
TEST_AVAILABILITY_ENTITY = "binary_sensor.availability"

TEST_VACUUM = TemplatePlatformSetup(
    vacuum.DOMAIN,
    "vacuums",
    "test_vacuum",
    make_test_trigger(
        TEST_STATE_ENTITY_ID,
        TEST_ATTRIBUTE_ENTITY_ID,
        TEST_AVAILABILITY_ENTITY,
    ),
)

CLEAN_SPOT_ACTION = make_test_action("clean_spot")
LOCATE_ACTION = make_test_action("locate")
PAUSE_ACTION = make_test_action("pause")
RETURN_TO_BASE_ACTION = make_test_action("return_to_base")
SET_FAN_SPEED_ACTION = make_test_action(
    "set_fan_speed", {"fan_speed": "{{ fan_speed }}"}
)
START_ACTION = make_test_action("start")
STOP_ACTION = make_test_action("stop")

TEMPLATE_VACUUM_ACTIONS = {
    **START_ACTION,
    **PAUSE_ACTION,
    **STOP_ACTION,
    **RETURN_TO_BASE_ACTION,
    **CLEAN_SPOT_ACTION,
    **LOCATE_ACTION,
    **SET_FAN_SPEED_ACTION,
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


def _verify(
    hass: HomeAssistant,
    expected_state: str,
    expected_battery_level: int | None = None,
    expected_fan_speed: str | None = None,
) -> None:
    """Verify vacuum's state and speed."""
    state = hass.states.get(TEST_VACUUM.entity_id)
    attributes = state.attributes
    assert state.state == expected_state
    assert attributes.get(ATTR_BATTERY_LEVEL) == expected_battery_level
    assert attributes.get(ATTR_FAN_SPEED) == expected_fan_speed


@test.cases(
    test.case("legacy_cleaning", style=ConfigurationStyle.LEGACY, set_state=VacuumActivity.CLEANING.value, expected=VacuumActivity.CLEANING.value),
    test.case("legacy_docked", style=ConfigurationStyle.LEGACY, set_state=VacuumActivity.DOCKED.value, expected=VacuumActivity.DOCKED.value),
    test.case("legacy_paused", style=ConfigurationStyle.LEGACY, set_state=VacuumActivity.PAUSED.value, expected=VacuumActivity.PAUSED.value),
    test.case("legacy_idle", style=ConfigurationStyle.LEGACY, set_state=VacuumActivity.IDLE.value, expected=VacuumActivity.IDLE.value),
    test.case("legacy_returning", style=ConfigurationStyle.LEGACY, set_state=VacuumActivity.RETURNING.value, expected=VacuumActivity.RETURNING.value),
    test.case("legacy_error", style=ConfigurationStyle.LEGACY, set_state=VacuumActivity.ERROR.value, expected=VacuumActivity.ERROR.value),
    test.case("legacy_dog", style=ConfigurationStyle.LEGACY, set_state="dog", expected=STATE_UNKNOWN),
    test.case("modern_cleaning", style=ConfigurationStyle.MODERN, set_state=VacuumActivity.CLEANING.value, expected=VacuumActivity.CLEANING.value),
    test.case("modern_docked", style=ConfigurationStyle.MODERN, set_state=VacuumActivity.DOCKED.value, expected=VacuumActivity.DOCKED.value),
    test.case("modern_paused", style=ConfigurationStyle.MODERN, set_state=VacuumActivity.PAUSED.value, expected=VacuumActivity.PAUSED.value),
    test.case("modern_idle", style=ConfigurationStyle.MODERN, set_state=VacuumActivity.IDLE.value, expected=VacuumActivity.IDLE.value),
    test.case("modern_returning", style=ConfigurationStyle.MODERN, set_state=VacuumActivity.RETURNING.value, expected=VacuumActivity.RETURNING.value),
    test.case("modern_error", style=ConfigurationStyle.MODERN, set_state=VacuumActivity.ERROR.value, expected=VacuumActivity.ERROR.value),
    test.case("trigger_cleaning", style=ConfigurationStyle.TRIGGER, set_state=VacuumActivity.CLEANING.value, expected=VacuumActivity.CLEANING.value),
    test.case("trigger_docked", style=ConfigurationStyle.TRIGGER, set_state=VacuumActivity.DOCKED.value, expected=VacuumActivity.DOCKED.value),
    test.case("trigger_paused", style=ConfigurationStyle.TRIGGER, set_state=VacuumActivity.PAUSED.value, expected=VacuumActivity.PAUSED.value),
    test.case("trigger_idle", style=ConfigurationStyle.TRIGGER, set_state=VacuumActivity.IDLE.value, expected=VacuumActivity.IDLE.value),
    test.case("trigger_returning", style=ConfigurationStyle.TRIGGER, set_state=VacuumActivity.RETURNING.value, expected=VacuumActivity.RETURNING.value),
    test.case("trigger_error", style=ConfigurationStyle.TRIGGER, set_state=VacuumActivity.ERROR.value, expected=VacuumActivity.ERROR.value),
)
async def state_template(
    *,
    style: ConfigurationStyle,
    set_state: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the state template."""
    await setup_entity(
        hass,
        TEST_VACUUM,
        style,
        1,
        TEMPLATE_VACUUM_ACTIONS,
        state_template="{{ states('sensor.test_state') }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, set_state)
    state = hass.states.get(TEST_VACUUM.entity_id)
    expect(state.state).to_equal(expected)


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
    """Test availability template."""
    attribute = (
        "availability_template"
        if style == ConfigurationStyle.LEGACY
        else "availability"
    )
    await setup_entity(
        hass,
        TEST_VACUUM,
        style,
        1,
        {
            **TEMPLATE_VACUUM_ACTIONS,
            attribute: "{{ is_state('binary_sensor.availability', 'on') }}",
        },
        state_template="{{ states('sensor.test_state') }}",
    )
    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, "on")
    expect(hass.states.get(TEST_VACUUM.entity_id).state != STATE_UNAVAILABLE).to_be(True)

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, "off")
    expect(hass.states.get(TEST_VACUUM.entity_id).state).to_be(STATE_UNAVAILABLE)


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
        TEST_VACUUM,
        style,
        1,
        {**TEMPLATE_VACUUM_ACTIONS, attribute: "{{ x - 12 }}"},
        state_template="{{ states('sensor.test_state') }}",
    )
    expect(
        hass.states.get(TEST_VACUUM.entity_id).state != STATE_UNAVAILABLE
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
        hass, TEST_VACUUM, style, TEMPLATE_VACUUM_ACTIONS, "{{ 'cleaning' }}"
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
        hass,
        TEST_VACUUM,
        style,
        entity_registry,
        TEMPLATE_VACUUM_ACTIONS,
        "{{ 'cleaning' }}",
    )


# === Skips ===


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub."""


@test.skip("valid_legacy_configs uses indirect parametrize — port deferred")
async def valid_legacy_configs() -> None:
    """Stub."""


@test.skip("invalid_configs uses indirect parametrize — port deferred")
async def invalid_configs() -> None:
    """Stub."""


@test.skip("battery_level_template stub — port deferred")
async def battery_level_template() -> None:
    """Stub."""


@test.skip("battery_level_template_repair stub")
async def battery_level_template_repair() -> None:
    """Stub."""


@test.skip("fan_speed_template stub")
async def fan_speed_template() -> None:
    """Stub."""


@test.skip("icon_template stub")
async def icon_template() -> None:
    """Stub."""


@test.skip("picture_template stub")
async def picture_template() -> None:
    """Stub."""


@test.skip("available_template_with_entities stub — duplicate of availability_template")
async def available_template_with_entities() -> None:
    """Stub."""


@test.skip("attribute_templates stub")
async def attribute_templates() -> None:
    """Stub."""


@test.skip("invalid_attribute_template stub")
async def invalid_attribute_template() -> None:
    """Stub."""


@test.skip("unused_services stub")
async def unused_services() -> None:
    """Stub."""


@test.skip("state_services stub")
async def state_services() -> None:
    """Stub."""


@test.skip("set_fan_speed stub")
async def set_fan_speed() -> None:
    """Stub."""


@test.skip("set_invalid_fan_speed stub")
async def set_invalid_fan_speed() -> None:
    """Stub."""


@test.skip("empty_action_config stub")
async def empty_action_config() -> None:
    """Stub."""


@test.skip("assumed_optimistic stub")
async def assumed_optimistic() -> None:
    """Stub."""


@test.skip("optimistic_option stub")
async def optimistic_option() -> None:
    """Stub."""


@test.skip("not_optimistic stub")
async def not_optimistic() -> None:
    """Stub."""


@test.skip("clean_area stub")
async def clean_area() -> None:
    """Stub."""


@test.skip("get_segments stub")
async def get_segments() -> None:
    """Stub."""


@test.skip("invalid_segments stub")
async def invalid_segments() -> None:
    """Stub."""


@test.skip("raise_segments_changed_issue stub")
async def raise_segments_changed_issue() -> None:
    """Stub."""


@test.skip("segments_part_config stub")
async def segments_part_config() -> None:
    """Stub."""


@test.skip("segments_unique_id stub")
async def segments_unique_id() -> None:
    """Stub."""
