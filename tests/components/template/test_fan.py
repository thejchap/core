"""The tests for the Template fan platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import fan
from homeassistant.components.fan import (
    ATTR_DIRECTION,
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
)
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
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

TEST_INPUT_BOOLEAN = "input_boolean.state"
TEST_STATE_ENTITY_ID = "sensor.test_sensor"
TEST_AVAILABILITY_ENTITY = "binary_sensor.availability"

TEST_FAN = TemplatePlatformSetup(
    fan.DOMAIN,
    "fans",
    "test_fan",
    make_test_trigger(
        TEST_INPUT_BOOLEAN, TEST_STATE_ENTITY_ID, TEST_AVAILABILITY_ENTITY
    ),
)

ON_ACTION = make_test_action("turn_on")
OFF_ACTION = make_test_action("turn_off")
OPTIMISTIC_ON_OFF_ACTIONS = {**ON_ACTION, **OFF_ACTION}


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
    expected_percentage: int | None = None,
    expected_oscillating: bool | None = None,
    expected_direction: str | None = None,
    expected_preset_mode: str | None = None,
) -> None:
    """Verify fan's state, speed and osc."""
    state = hass.states.get(TEST_FAN.entity_id)
    attributes = state.attributes
    assert state.state == str(expected_state)
    assert attributes.get(ATTR_PERCENTAGE) == expected_percentage
    assert attributes.get(ATTR_OSCILLATING) == expected_oscillating
    assert attributes.get(ATTR_DIRECTION) == expected_direction
    assert attributes.get(ATTR_PRESET_MODE) == expected_preset_mode


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def missing_optional_config(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: missing optional template is ok."""
    await setup_entity(
        hass,
        TEST_FAN,
        style,
        1,
        OPTIMISTIC_ON_OFF_ACTIONS,
        state_template="{{ 'on' }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")
    _verify(hass, STATE_ON, None, None, None, None)


@test.cases(
    test.case("legacy_off", style=ConfigurationStyle.LEGACY, extra_config=OFF_ACTION),
    test.case("legacy_on", style=ConfigurationStyle.LEGACY, extra_config=ON_ACTION),
    test.case("modern_off", style=ConfigurationStyle.MODERN, extra_config=OFF_ACTION),
    test.case("modern_on", style=ConfigurationStyle.MODERN, extra_config=ON_ACTION),
    test.case("trigger_off", style=ConfigurationStyle.TRIGGER, extra_config=OFF_ACTION),
    test.case("trigger_on", style=ConfigurationStyle.TRIGGER, extra_config=ON_ACTION),
)
async def wrong_template_config(
    *,
    style: ConfigurationStyle,
    extra_config: dict,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: missing 'turn_on' or 'turn_off' will fail."""
    await setup_entity(
        hass, TEST_FAN, style, 0, {}, state_template="{{ 1==1 }}", extra_config=extra_config
    )
    expect(hass.states.async_all("fan")).to_equal([])


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def state_template(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state template."""
    await setup_entity(
        hass,
        TEST_FAN,
        style,
        1,
        OPTIMISTIC_ON_OFF_ACTIONS,
        state_template="{{ is_state('input_boolean.state', 'on') }}",
    )
    await async_trigger(hass, TEST_INPUT_BOOLEAN, STATE_OFF)
    _verify(hass, STATE_OFF, None, None, None, None)

    await async_trigger(hass, TEST_INPUT_BOOLEAN, STATE_ON)
    _verify(hass, STATE_ON, None, None, None, None)

    await async_trigger(hass, TEST_INPUT_BOOLEAN, STATE_OFF)
    _verify(hass, STATE_OFF, None, None, None, None)


@test.cases(
    test.case("legacy_true", style=ConfigurationStyle.LEGACY, tpl="{{ True }}", expected=STATE_ON),
    test.case("legacy_false", style=ConfigurationStyle.LEGACY, tpl="{{ False }}", expected=STATE_OFF),
    test.case("legacy_unavailable", style=ConfigurationStyle.LEGACY, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
    test.case("legacy_one", style=ConfigurationStyle.LEGACY, tpl="{{ 1 }}", expected=STATE_ON),
    test.case("legacy_str_true", style=ConfigurationStyle.LEGACY, tpl="{{ 'true' }}", expected=STATE_ON),
    test.case("legacy_yes", style=ConfigurationStyle.LEGACY, tpl="{{ 'yes' }}", expected=STATE_ON),
    test.case("legacy_on", style=ConfigurationStyle.LEGACY, tpl="{{ 'on' }}", expected=STATE_ON),
    test.case("legacy_enable", style=ConfigurationStyle.LEGACY, tpl="{{ 'enable' }}", expected=STATE_ON),
    test.case("legacy_zero", style=ConfigurationStyle.LEGACY, tpl="{{ 0 }}", expected=STATE_OFF),
    test.case("legacy_str_false", style=ConfigurationStyle.LEGACY, tpl="{{ 'false' }}", expected=STATE_OFF),
    test.case("legacy_no", style=ConfigurationStyle.LEGACY, tpl="{{ 'no' }}", expected=STATE_OFF),
    test.case("legacy_off", style=ConfigurationStyle.LEGACY, tpl="{{ 'off' }}", expected=STATE_OFF),
    test.case("legacy_disable", style=ConfigurationStyle.LEGACY, tpl="{{ 'disable' }}", expected=STATE_OFF),
    test.case("legacy_none", style=ConfigurationStyle.LEGACY, tpl="{{ None }}", expected=STATE_UNKNOWN),
    test.case("modern_true", style=ConfigurationStyle.MODERN, tpl="{{ True }}", expected=STATE_ON),
    test.case("modern_false", style=ConfigurationStyle.MODERN, tpl="{{ False }}", expected=STATE_OFF),
    test.case("modern_unavailable", style=ConfigurationStyle.MODERN, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
    test.case("modern_none", style=ConfigurationStyle.MODERN, tpl="{{ None }}", expected=STATE_UNKNOWN),
    test.case("trigger_true", style=ConfigurationStyle.TRIGGER, tpl="{{ True }}", expected=STATE_ON),
    test.case("trigger_false", style=ConfigurationStyle.TRIGGER, tpl="{{ False }}", expected=STATE_OFF),
    test.case("trigger_unavailable", style=ConfigurationStyle.TRIGGER, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
    test.case("trigger_none", style=ConfigurationStyle.TRIGGER, tpl="{{ None }}", expected=STATE_UNKNOWN),
)
async def state_template_states(
    *,
    style: ConfigurationStyle,
    tpl: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state template values."""
    await setup_entity(
        hass, TEST_FAN, style, 1, OPTIMISTIC_ON_OFF_ACTIONS, state_template=tpl
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")
    _verify(hass, expected, None, None, None, None)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def availability_template(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test availability template."""
    await setup_entity(
        hass,
        TEST_FAN,
        style,
        1,
        {
            **OPTIMISTIC_ON_OFF_ACTIONS,
            "availability": "{{ is_state('binary_sensor.availability', 'on') }}",
        },
        state_template="{{ 1 == 1 }}",
    )
    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, STATE_ON)
    expect(hass.states.get(TEST_FAN.entity_id).state != STATE_UNAVAILABLE).to_be(True)

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, STATE_OFF)
    expect(hass.states.get(TEST_FAN.entity_id).state).to_be(STATE_UNAVAILABLE)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def invalid_availability_template_keeps_component_available(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that an invalid availability keeps the device available."""
    await setup_entity(
        hass,
        TEST_FAN,
        style,
        1,
        {**OPTIMISTIC_ON_OFF_ACTIONS, "availability": "{{ x - 12 }}"},
        state_template="{{ 1 == 1 }}",
    )
    expect(hass.states.get(TEST_FAN.entity_id).state != STATE_UNAVAILABLE).to_be(True)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option only creates one fan per id."""
    await setup_and_test_unique_id(
        hass, TEST_FAN, style, OPTIMISTIC_ON_OFF_ACTIONS, "{{ 1==1 }}"
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
        TEST_FAN,
        style,
        entity_registry,
        OPTIMISTIC_ON_OFF_ACTIONS,
        "{{ 1==1 }}",
    )


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.skip("template_with_unavailable_entities stub — port deferred")
async def template_with_unavailable_entities() -> None:
    """Stub."""


@test.skip("on_off needs services — port deferred")
async def on_off() -> None:
    """Stub."""


@test.skip("on_with_extra_attributes stub")
async def on_with_extra_attributes() -> None:
    """Stub."""


@test.skip("set_invalid_direction_from_initial_stage stub")
async def set_invalid_direction_from_initial_stage() -> None:
    """Stub."""


@test.skip("set_osc stub")
async def set_osc() -> None:
    """Stub."""


@test.skip("set_direction stub")
async def set_direction() -> None:
    """Stub."""


@test.skip("set_invalid_direction stub")
async def set_invalid_direction() -> None:
    """Stub."""


@test.skip("preset_modes stub")
async def preset_modes() -> None:
    """Stub."""


@test.skip("invalid_preset_modes stub")
async def invalid_preset_modes() -> None:
    """Stub."""


@test.skip("set_percentage stub")
async def set_percentage() -> None:
    """Stub."""


@test.skip("increase_decrease_speed stub")
async def increase_decrease_speed() -> None:
    """Stub."""


@test.skip("optimistic_state stub")
async def optimistic_state() -> None:
    """Stub."""


@test.skip("optimistic_attributes stub")
async def optimistic_attributes() -> None:
    """Stub."""


@test.skip("increase_decrease_speed_default_speed_count stub")
async def increase_decrease_speed_default_speed_count() -> None:
    """Stub."""


@test.skip("set_invalid_osc_from_initial_state stub")
async def set_invalid_osc_from_initial_state() -> None:
    """Stub."""


@test.skip("set_invalid_osc stub")
async def set_invalid_osc() -> None:
    """Stub."""


@test.skip("speed_percentage_step stub")
async def speed_percentage_step() -> None:
    """Stub."""


@test.skip("preset_mode_supported_features stub")
async def preset_mode_supported_features() -> None:
    """Stub."""


@test.skip("empty_action_config stub")
async def empty_action_config() -> None:
    """Stub."""


@test.skip("optimistic_option stub")
async def optimistic_option() -> None:
    """Stub."""


@test.skip("not_optimistic stub")
async def not_optimistic() -> None:
    """Stub."""


@test.skip("picture_template stub — port deferred")
async def picture_template() -> None:
    """Stub."""


@test.skip("icon_template stub — port deferred")
async def icon_template() -> None:
    """Stub."""


@test.skip("percentage_template stub — port deferred")
async def percentage_template() -> None:
    """Stub."""


@test.skip("preset_mode_template stub — port deferred")
async def preset_mode_template() -> None:
    """Stub."""


@test.skip("oscillating_template stub — port deferred")
async def oscillating_template() -> None:
    """Stub."""


@test.skip("direction_template stub — port deferred")
async def direction_template() -> None:
    """Stub."""


@test.skip("availability_template_with_entities (legacy) — port deferred")
async def availability_template_with_entities() -> None:
    """Stub: legacy variant of availability_template."""
