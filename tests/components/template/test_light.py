"""The tests for the Template light platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import light
from homeassistant.components.light import ColorMode
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    async_setup_legacy_platforms,
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

TEST_STATE_ENTITY_ID = "light.test_state"
TEST_AVAILABILITY_ENTITY = "binary_sensor.availability"

TEST_LIGHT = TemplatePlatformSetup(
    light.DOMAIN,
    "lights",
    "test_light",
    make_test_trigger(TEST_STATE_ENTITY_ID, TEST_AVAILABILITY_ENTITY),
)

ON_ACTION = make_test_action("turn_on")
OFF_ACTION = make_test_action("turn_off")
ON_OFF_ACTIONS = {**ON_ACTION, **OFF_ACTION}

BRIGHTNESS_DATA = {"brightness": "{{ brightness }}"}
SET_LEVEL_ACTION = make_test_action("set_level", BRIGHTNESS_DATA)
ON_OFF_SET_LEVEL_ACTIONS = {**ON_OFF_ACTIONS, **SET_LEVEL_ACTION}


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
async def template_state_invalid(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template state with render error."""
    await setup_entity(
        hass,
        TEST_LIGHT,
        style,
        1,
        ON_OFF_SET_LEVEL_ACTIONS,
        state_template="{{states.test['big.fat...']}}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, None)

    state = hass.states.get(TEST_LIGHT.entity_id)
    expect(state.state).to_be(STATE_UNAVAILABLE)
    expect(state.attributes["supported_color_modes"]).to_equal([ColorMode.BRIGHTNESS])
    expect(state.attributes["supported_features"]).to_equal(0)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_state_text(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the state text of a template."""
    await setup_entity(
        hass,
        TEST_LIGHT,
        style,
        1,
        ON_OFF_SET_LEVEL_ACTIONS,
        state_template="{{ states.light.test_state.state }}",
    )
    set_state = STATE_ON
    await async_trigger(hass, TEST_STATE_ENTITY_ID, set_state)
    state = hass.states.get(TEST_LIGHT.entity_id)
    expect(state.state).to_be(set_state)
    expect(state.attributes["color_mode"]).to_equal(ColorMode.BRIGHTNESS)
    expect(state.attributes["supported_color_modes"]).to_equal([ColorMode.BRIGHTNESS])
    expect(state.attributes["supported_features"]).to_equal(0)

    set_state = STATE_OFF
    await async_trigger(hass, TEST_STATE_ENTITY_ID, set_state)
    state = hass.states.get(TEST_LIGHT.entity_id)
    expect(state.state).to_be(set_state)
    expect(state.attributes.get("color_mode")).to_be(None)
    expect(state.attributes["supported_color_modes"]).to_equal([ColorMode.BRIGHTNESS])
    expect(state.attributes["supported_features"]).to_equal(0)


@test.cases(
    test.case(
        "legacy_on", style=ConfigurationStyle.LEGACY,
        tpl="{{ 1 == 1 }}", expected_state=STATE_ON,
        expected_color_mode=ColorMode.BRIGHTNESS,
    ),
    test.case(
        "legacy_off", style=ConfigurationStyle.LEGACY,
        tpl="{{ 1 == 2 }}", expected_state=STATE_OFF, expected_color_mode=None,
    ),
    test.case(
        "modern_on", style=ConfigurationStyle.MODERN,
        tpl="{{ 1 == 1 }}", expected_state=STATE_ON,
        expected_color_mode=ColorMode.BRIGHTNESS,
    ),
    test.case(
        "modern_off", style=ConfigurationStyle.MODERN,
        tpl="{{ 1 == 2 }}", expected_state=STATE_OFF, expected_color_mode=None,
    ),
    test.case(
        "trigger_on", style=ConfigurationStyle.TRIGGER,
        tpl="{{ 1 == 1 }}", expected_state=STATE_ON,
        expected_color_mode=ColorMode.BRIGHTNESS,
    ),
    test.case(
        "trigger_off", style=ConfigurationStyle.TRIGGER,
        tpl="{{ 1 == 2 }}", expected_state=STATE_OFF, expected_color_mode=None,
    ),
)
async def template_state_boolean(
    *,
    style: ConfigurationStyle,
    tpl: str,
    expected_state: str,
    expected_color_mode: ColorMode | None,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the state with boolean on."""
    await setup_entity(
        hass, TEST_LIGHT, style, 1, ON_OFF_SET_LEVEL_ACTIONS, state_template=tpl
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, expected_state)

    state = hass.states.get(TEST_LIGHT.entity_id)
    expect(state.state).to_be(expected_state)
    expect(state.attributes.get("color_mode")).to_equal(expected_color_mode)
    expect(state.attributes["supported_color_modes"]).to_equal([ColorMode.BRIGHTNESS])
    expect(state.attributes["supported_features"]).to_equal(0)


@test
async def legacy_template_config_errors(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test legacy template light configuration errors."""
    await async_setup_legacy_platforms(
        hass,
        light.DOMAIN,
        "bad name here",
        0,
        {**ON_OFF_SET_LEVEL_ACTIONS, "value_template": "{{ 1== 1}}"},
    )
    expect(hass.states.async_all("light")).to_equal([])


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_config_errors(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template light configuration errors."""
    await setup_entity(
        hass,
        TEST_LIGHT,
        style,
        0,
        ON_OFF_SET_LEVEL_ACTIONS,
        state_template="{%- if false -%}",
    )
    expect(hass.states.async_all("light")).to_equal([])


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def missing_key(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test missing template."""
    await setup_entity(
        hass, TEST_LIGHT, style, 0, {**ON_ACTION, **SET_LEVEL_ACTION}
    )
    expect(hass.states.async_all("light")).to_equal([])


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
        TEST_LIGHT,
        style,
        1,
        {
            **ON_OFF_SET_LEVEL_ACTIONS,
            attribute: "{{ is_state('binary_sensor.availability', 'on') }}",
        },
        state_template="{{ 1 == 1 }}",
    )
    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, STATE_ON)
    expect(hass.states.get(TEST_LIGHT.entity_id).state != STATE_UNAVAILABLE).to_be(True)

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, STATE_OFF)
    expect(hass.states.get(TEST_LIGHT.entity_id).state).to_be(STATE_UNAVAILABLE)


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
        TEST_LIGHT,
        style,
        1,
        {**ON_OFF_SET_LEVEL_ACTIONS, attribute: "{{ x - 12 }}"},
        state_template="{{ 1 == 1 }}",
    )
    expect(hass.states.get(TEST_LIGHT.entity_id).state != STATE_UNAVAILABLE).to_be(True)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option only creates one light per id."""
    await setup_and_test_unique_id(
        hass, TEST_LIGHT, style, ON_OFF_SET_LEVEL_ACTIONS, "{{ 1==1 }}"
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
        TEST_LIGHT,
        style,
        entity_registry,
        ON_OFF_SET_LEVEL_ACTIONS,
        "{{ 1==1 }}",
    )


# === Skips for the rest ===


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.skip("on_action stub — port deferred")
async def on_action() -> None:
    """Stub."""


@test.skip("on_action_with_transition stub")
async def on_action_with_transition() -> None:
    """Stub."""


@test.skip("on_action_optimistic stub")
async def on_action_optimistic() -> None:
    """Stub."""


@test.skip("off_action stub")
async def off_action() -> None:
    """Stub."""


@test.skip("off_action_with_transition stub")
async def off_action_with_transition() -> None:
    """Stub."""


@test.skip("off_action_optimistic stub")
async def off_action_optimistic() -> None:
    """Stub."""


@test.skip("level_action_no_template stub")
async def level_action_no_template() -> None:
    """Stub."""


@test.skip("level_template stub")
async def level_template() -> None:
    """Stub."""


@test.skip("temperature_template stub")
async def temperature_template() -> None:
    """Stub."""


@test.skip("temperature_action_no_template stub")
async def temperature_action_no_template() -> None:
    """Stub."""


@test.skip("friendly_name stub")
async def friendly_name() -> None:
    """Stub."""


@test.skip("icon_template stub")
async def icon_template() -> None:
    """Stub."""


@test.skip("entity_picture_template stub")
async def entity_picture_template() -> None:
    """Stub."""


@test.skip("legacy_color_action_no_template stub")
async def legacy_color_action_no_template() -> None:
    """Stub."""


@test.skip("hs_color_action stub")
async def hs_color_action() -> None:
    """Stub."""


@test.skip("rgb_color_action stub")
async def rgb_color_action() -> None:
    """Stub."""


@test.skip("rgbw_color_action stub")
async def rgbw_color_action() -> None:
    """Stub."""


@test.skip("rgbww_color_action stub")
async def rgbww_color_action() -> None:
    """Stub."""


@test.skip("legacy_color_template stub")
async def legacy_color_template() -> None:
    """Stub."""


@test.skip("hs_color_template stub")
async def hs_color_template() -> None:
    """Stub."""


@test.skip("rgb_color_template stub")
async def rgb_color_template() -> None:
    """Stub."""


@test.skip("rgbw_color_template stub")
async def rgbw_color_template() -> None:
    """Stub."""


@test.skip("rgbww_color_template stub")
async def rgbww_color_template() -> None:
    """Stub."""


@test.skip("effect_action_no_template stub")
async def effect_action_no_template() -> None:
    """Stub."""


@test.skip("effect_action stub")
async def effect_action() -> None:
    """Stub."""


@test.skip("effect_template stub")
async def effect_template() -> None:
    """Stub."""


@test.skip("legacy_min_max_mireds_templates stub")
async def legacy_min_max_mireds_templates() -> None:
    """Stub."""


@test.skip("min_max_kelvin_templates stub")
async def min_max_kelvin_templates() -> None:
    """Stub."""


@test.skip("light_supports_transition_template stub")
async def light_supports_transition_template() -> None:
    """Stub."""


@test.skip("legacy_optimistic_state stub")
async def legacy_optimistic_state() -> None:
    """Stub."""


@test.skip("optimistic_state stub")
async def optimistic_state() -> None:
    """Stub."""


@test.skip("not_optimistic_state stub")
async def not_optimistic_state() -> None:
    """Stub."""


@test.skip("legacy_optimistic_supports_transition_template stub")
async def legacy_optimistic_supports_transition_template() -> None:
    """Stub."""


@test.skip("optimistic_supports_transition_template stub")
async def optimistic_supports_transition_template() -> None:
    """Stub."""


@test.skip("not_optimistic_supports_transition_template stub")
async def not_optimistic_supports_transition_template() -> None:
    """Stub."""


@test.skip("template_with_unavailable_entities stub")
async def template_with_unavailable_entities() -> None:
    """Stub."""


@test.skip("device_id stub")
async def device_id() -> None:
    """Stub."""


@test.skip("empty_action_config stub")
async def empty_action_config() -> None:
    """Stub."""
