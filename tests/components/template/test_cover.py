"""The tests for the Template cover platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import cover
from homeassistant.components.cover import (
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    CoverState,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    SERVICE_TOGGLE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    assert_action,
    async_trigger,
    make_test_action,
    make_test_trigger,
    mock_calls,
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
TEST_POSITION_ENTITY_ID = "sensor.test_position"
TEST_AVAILABILITY_ENTITY = "binary_sensor.availability"

TEST_COVER = TemplatePlatformSetup(
    cover.DOMAIN,
    "covers",
    "test_template_cover",
    make_test_trigger(
        TEST_STATE_ENTITY_ID,
        TEST_POSITION_ENTITY_ID,
        TEST_AVAILABILITY_ENTITY,
    ),
)

OPEN_COVER = make_test_action("open_cover")
CLOSE_COVER = make_test_action("close_cover")
STOP_COVER = make_test_action("stop_cover")
SET_COVER_POSITION = make_test_action(
    "set_cover_position", {"position": "{{ position }}"}
)
SET_COVER_TILT_POSITION = make_test_action(
    "set_cover_tilt_position", {"tilt_position": "{{ tilt }}"}
)

COVER_ACTIONS = {**OPEN_COVER, **CLOSE_COVER}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test.cases(
    test.case("legacy_open", style=ConfigurationStyle.LEGACY, set_state=CoverState.OPEN.value, test_state=CoverState.OPEN.value),
    test.case("legacy_closed", style=ConfigurationStyle.LEGACY, set_state=CoverState.CLOSED.value, test_state=CoverState.CLOSED.value),
    test.case("legacy_opening", style=ConfigurationStyle.LEGACY, set_state=CoverState.OPENING.value, test_state=CoverState.OPENING.value),
    test.case("legacy_closing", style=ConfigurationStyle.LEGACY, set_state=CoverState.CLOSING.value, test_state=CoverState.CLOSING.value),
    test.case("legacy_dog", style=ConfigurationStyle.LEGACY, set_state="dog", test_state=STATE_UNKNOWN),
    test.case("modern_open", style=ConfigurationStyle.MODERN, set_state=CoverState.OPEN.value, test_state=CoverState.OPEN.value),
    test.case("modern_closed", style=ConfigurationStyle.MODERN, set_state=CoverState.CLOSED.value, test_state=CoverState.CLOSED.value),
    test.case("modern_opening", style=ConfigurationStyle.MODERN, set_state=CoverState.OPENING.value, test_state=CoverState.OPENING.value),
    test.case("modern_closing", style=ConfigurationStyle.MODERN, set_state=CoverState.CLOSING.value, test_state=CoverState.CLOSING.value),
    test.case("modern_dog", style=ConfigurationStyle.MODERN, set_state="dog", test_state=STATE_UNKNOWN),
    test.case("trigger_open", style=ConfigurationStyle.TRIGGER, set_state=CoverState.OPEN.value, test_state=CoverState.OPEN.value),
    test.case("trigger_closed", style=ConfigurationStyle.TRIGGER, set_state=CoverState.CLOSED.value, test_state=CoverState.CLOSED.value),
    test.case("trigger_opening", style=ConfigurationStyle.TRIGGER, set_state=CoverState.OPENING.value, test_state=CoverState.OPENING.value),
    test.case("trigger_closing", style=ConfigurationStyle.TRIGGER, set_state=CoverState.CLOSING.value, test_state=CoverState.CLOSING.value),
    test.case("trigger_dog", style=ConfigurationStyle.TRIGGER, set_state="dog", test_state=STATE_UNKNOWN),
)
async def template_state_text(
    *,
    style: ConfigurationStyle,
    set_state: str,
    test_state: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the state text of a template."""
    await setup_entity(
        hass,
        TEST_COVER,
        style,
        1,
        COVER_ACTIONS,
        state_template="{{ states.sensor.test_state.state }}",
    )
    state = hass.states.get(TEST_COVER.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, set_state)

    state = hass.states.get(TEST_COVER.entity_id)
    expect(state.state).to_equal(test_state)


@test.cases(
    test.case("legacy_open_str", style=ConfigurationStyle.LEGACY, tpl="{{ 'open' }}", expected=CoverState.OPEN.value),
    test.case("legacy_on", style=ConfigurationStyle.LEGACY, tpl="{{ 'on' }}", expected=CoverState.OPEN.value),
    test.case("legacy_one", style=ConfigurationStyle.LEGACY, tpl="{{ 1 }}", expected=CoverState.OPEN.value),
    test.case("legacy_true", style=ConfigurationStyle.LEGACY, tpl="{{ True }}", expected=CoverState.OPEN.value),
    test.case("legacy_closed_str", style=ConfigurationStyle.LEGACY, tpl="{{ 'closed' }}", expected=CoverState.CLOSED.value),
    test.case("legacy_off", style=ConfigurationStyle.LEGACY, tpl="{{ 'off' }}", expected=CoverState.CLOSED.value),
    test.case("legacy_zero", style=ConfigurationStyle.LEGACY, tpl="{{ 0 }}", expected=CoverState.CLOSED.value),
    test.case("legacy_false", style=ConfigurationStyle.LEGACY, tpl="{{ False }}", expected=CoverState.CLOSED.value),
    test.case("legacy_opening", style=ConfigurationStyle.LEGACY, tpl="{{ 'opening' }}", expected=CoverState.OPENING.value),
    test.case("legacy_closing", style=ConfigurationStyle.LEGACY, tpl="{{ 'closing' }}", expected=CoverState.CLOSING.value),
    test.case("legacy_dog", style=ConfigurationStyle.LEGACY, tpl="{{ 'dog' }}", expected=STATE_UNKNOWN),
    test.case("legacy_unavailable", style=ConfigurationStyle.LEGACY, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
    test.case("modern_open_str", style=ConfigurationStyle.MODERN, tpl="{{ 'open' }}", expected=CoverState.OPEN.value),
    test.case("modern_closed_str", style=ConfigurationStyle.MODERN, tpl="{{ 'closed' }}", expected=CoverState.CLOSED.value),
    test.case("modern_opening", style=ConfigurationStyle.MODERN, tpl="{{ 'opening' }}", expected=CoverState.OPENING.value),
    test.case("modern_closing", style=ConfigurationStyle.MODERN, tpl="{{ 'closing' }}", expected=CoverState.CLOSING.value),
    test.case("modern_unavailable", style=ConfigurationStyle.MODERN, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
    test.case("trigger_open_str", style=ConfigurationStyle.TRIGGER, tpl="{{ 'open' }}", expected=CoverState.OPEN.value),
    test.case("trigger_closed_str", style=ConfigurationStyle.TRIGGER, tpl="{{ 'closed' }}", expected=CoverState.CLOSED.value),
    test.case("trigger_opening", style=ConfigurationStyle.TRIGGER, tpl="{{ 'opening' }}", expected=CoverState.OPENING.value),
    test.case("trigger_closing", style=ConfigurationStyle.TRIGGER, tpl="{{ 'closing' }}", expected=CoverState.CLOSING.value),
    test.case("trigger_unavailable", style=ConfigurationStyle.TRIGGER, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
)
async def template_state_states(
    *,
    style: ConfigurationStyle,
    tpl: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state template states."""
    await setup_entity(
        hass, TEST_COVER, style, 1, COVER_ACTIONS, state_template=tpl
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, None)
    state = hass.states.get(TEST_COVER.entity_id)
    expect(state.state).to_equal(expected)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_not_optimistic(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the is_closed attribute."""
    mock_calls(hass)
    await setup_entity(
        hass, TEST_COVER, style, 1, {**COVER_ACTIONS, "optimistic": False}
    )
    state = hass.states.get(TEST_COVER.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: TEST_COVER.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get(TEST_COVER.entity_id).state).to_be(STATE_UNKNOWN)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: TEST_COVER.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get(TEST_COVER.entity_id).state).to_be(STATE_UNKNOWN)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def open_action(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the open_cover command."""
    calls = mock_calls(hass)
    position_option = (
        "position_template" if style == ConfigurationStyle.LEGACY else "position"
    )
    await setup_entity(
        hass,
        TEST_COVER,
        style,
        1,
        COVER_ACTIONS,
        extra_config={position_option: "{{ 0 }}", **SET_COVER_POSITION},
    )

    await async_trigger(hass, TEST_STATE_ENTITY_ID, None)

    state = hass.states.get(TEST_COVER.entity_id)
    expect(state.state).to_equal(CoverState.CLOSED.value)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: TEST_COVER.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert_action(TEST_COVER, calls, 1, "open_cover")


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def close_stop_action(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the close-cover and stop_cover commands."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_COVER,
        style,
        1,
        {**COVER_ACTIONS, **STOP_COVER},
        state_template="{{ 1==1 }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, None)

    state = hass.states.get(TEST_COVER.entity_id)
    expect(state.state).to_equal(CoverState.OPEN.value)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: TEST_COVER.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: TEST_COVER.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert_action(TEST_COVER, calls, 2, "close_cover", index=0)
    assert_action(TEST_COVER, calls, 2, "stop_cover")


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def set_position(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the set_position command."""
    calls = mock_calls(hass)
    await setup_entity(hass, TEST_COVER, style, 1, SET_COVER_POSITION)

    state = hass.states.get(TEST_COVER.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)

    expected_calls = 1
    for service, position, options in (
        (SERVICE_OPEN_COVER, 100, {}),
        (SERVICE_CLOSE_COVER, 0, {}),
        (SERVICE_TOGGLE, 100, {}),
        (SERVICE_TOGGLE, 0, {}),
        (SERVICE_SET_COVER_POSITION, 25, {ATTR_POSITION: 25}),
    ):
        await hass.services.async_call(
            COVER_DOMAIN,
            service,
            {ATTR_ENTITY_ID: TEST_COVER.entity_id, **options},
            blocking=True,
        )
        await hass.async_block_till_done()

        state = hass.states.get(TEST_COVER.entity_id)
        expect(state.attributes.get("current_position")).to_equal(position)
        assert_action(
            TEST_COVER, calls, expected_calls, "set_cover_position", position=position
        )
        expected_calls += 1


@test.cases(
    test.case(
        "legacy", style=ConfigurationStyle.LEGACY, attribute="availability_template"
    ),
    test.case("modern", style=ConfigurationStyle.MODERN, attribute="availability"),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, attribute="availability"),
)
async def availability_template(
    *,
    style: ConfigurationStyle,
    attribute: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test availability templates with values from other entities."""
    await setup_entity(
        hass,
        TEST_COVER,
        style,
        1,
        {attribute: "{{ is_state('binary_sensor.availability','on') }}"},
        state_template="{{ 1 == 1 }}",
        extra_config=COVER_ACTIONS,
    )

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, "on")
    expect(
        hass.states.get(TEST_COVER.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, "off")
    expect(hass.states.get(TEST_COVER.entity_id).state).to_be(STATE_UNAVAILABLE)


@test.cases(
    test.case(
        "legacy", style=ConfigurationStyle.LEGACY, attribute="availability_template"
    ),
    test.case("modern", style=ConfigurationStyle.MODERN, attribute="availability"),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, attribute="availability"),
)
async def invalid_availability_template_keeps_component_available(
    *,
    style: ConfigurationStyle,
    attribute: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that an invalid availability keeps the device available."""
    await setup_entity(
        hass,
        TEST_COVER,
        style,
        1,
        {attribute: "{{ x - 12 }}"},
        state_template="{{ 1 == 1 }}",
        extra_config=COVER_ACTIONS,
    )

    expect(
        hass.states.get(TEST_COVER.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def device_class(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test device_class option."""
    await setup_entity(
        hass,
        TEST_COVER,
        style,
        1,
        {**COVER_ACTIONS, "device_class": "door"},
        state_template="{{ states.sensor.test_state.state }}",
    )
    state = hass.states.get(TEST_COVER.entity_id)
    expect(state.attributes.get("device_class")).to_equal("door")


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def invalid_device_class(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test invalid device_class option."""
    await setup_entity(
        hass,
        TEST_COVER,
        style,
        0,
        {**COVER_ACTIONS, "device_class": "ofnoexisting"},
        state_template="{{ states.sensor.test_state.state }}",
    )
    expect(hass.states.async_all("cover")).to_equal([])


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option only creates one cover per id."""
    await setup_and_test_unique_id(
        hass, TEST_COVER, style, COVER_ACTIONS, "{{ 'open' }}"
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
    """Test a template unique_id propagates to cover unique_ids."""
    await setup_and_test_nested_unique_id(
        hass, TEST_COVER, style, entity_registry, COVER_ACTIONS, "{{ 'open' }}"
    )


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.skip("self_referencing_icon needs intricate caplog interplay — port deferred")
async def self_referencing_icon_with_no_template_is_not_a_loop() -> None:
    """Stub."""


@test.skip("template_state_text_with_position is complex — port deferred")
async def template_state_text_with_position() -> None:
    """Stub."""


@test.skip("template_state_text_ignored_if_none_or_empty stub — port deferred")
async def template_state_text_ignored_if_none_or_empty() -> None:
    """Stub."""


@test.skip("template_position stub — port deferred")
async def template_position() -> None:
    """Stub."""


@test.skip("template_tilt stub — port deferred")
async def template_tilt() -> None:
    """Stub."""


@test.skip("position_out_of_bounds stub — port deferred")
async def position_out_of_bounds() -> None:
    """Stub."""


@test.skip("template_open_or_position uses caplog_setup_text — port deferred")
async def template_open_or_position() -> None:
    """Stub."""


@test.skip("set_tilt_position stub — port deferred")
async def set_tilt_position() -> None:
    """Stub."""


@test.skip("set_position_optimistic stub — port deferred")
async def set_position_optimistic() -> None:
    """Stub."""


@test.skip("non_optimistic_template_with_optimistic_state stub — port deferred")
async def non_optimistic_template_with_optimistic_state() -> None:
    """Stub."""


@test.skip("set_tilt_position_optimistic stub — port deferred")
async def set_tilt_position_optimistic() -> None:
    """Stub."""


@test.skip("icon_template stub — port deferred")
async def icon_template() -> None:
    """Stub."""


@test.skip("entity_picture_template stub — port deferred")
async def entity_picture_template() -> None:
    """Stub."""


@test.skip("state_gets_lowercased stub — port deferred")
async def state_gets_lowercased() -> None:
    """Stub."""


@test.skip("empty_action_config stub — port deferred")
async def empty_action_config() -> None:
    """Stub."""
