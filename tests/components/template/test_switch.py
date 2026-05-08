"""The tests for the Template switch platform."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import switch, template
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.setup import async_setup_component

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

from tests.common import MockConfigEntry, assert_setup_component
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

TEST_OBJECT_ID = "test_template_switch"
TEST_STATE_ENTITY_ID = "switch.test_state"
TEST_SENSOR = "sensor.test_sensor"

TEST_SWITCH = TemplatePlatformSetup(
    switch.DOMAIN,
    "switches",
    "test_template_switch",
    make_test_trigger(TEST_STATE_ENTITY_ID, TEST_SENSOR),
)

TURN_ON_ACTION = make_test_action("turn_on")
TURN_OFF_ACTION = make_test_action("turn_off")
SWITCH_ACTIONS = {**TURN_ON_ACTION, **TURN_OFF_ACTION}


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
async def setup(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template."""
    await setup_entity(
        hass, TEST_SWITCH, style, 1, SWITCH_ACTIONS, state_template="{{ True }}"
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID)
    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state).not_.to_be(None)
    expect(state.name).to_equal(TEST_SWITCH.object_id)
    expect(state.state).to_be(STATE_ON)


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


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
        TEST_SWITCH,
        style,
        1,
        SWITCH_ACTIONS,
        state_template="{{ states.switch.test_state.state }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(STATE_ON)
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)
    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(STATE_OFF)


@test.cases(
    test.case(
        "legacy_on", style=ConfigurationStyle.LEGACY, tpl="{{ 1 == 1 }}", expected=STATE_ON
    ),
    test.case(
        "legacy_off",
        style=ConfigurationStyle.LEGACY,
        tpl="{{ 1 == 2 }}",
        expected=STATE_OFF,
    ),
    test.case(
        "modern_on", style=ConfigurationStyle.MODERN, tpl="{{ 1 == 1 }}", expected=STATE_ON
    ),
    test.case(
        "modern_off",
        style=ConfigurationStyle.MODERN,
        tpl="{{ 1 == 2 }}",
        expected=STATE_OFF,
    ),
    test.case(
        "trigger_on",
        style=ConfigurationStyle.TRIGGER,
        tpl="{{ 1 == 1 }}",
        expected=STATE_ON,
    ),
    test.case(
        "trigger_off",
        style=ConfigurationStyle.TRIGGER,
        tpl="{{ 1 == 2 }}",
        expected=STATE_OFF,
    ),
)
async def template_state_boolean(
    *,
    style: ConfigurationStyle,
    tpl: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the state with boolean template."""
    await setup_entity(hass, TEST_SWITCH, style, 1, SWITCH_ACTIONS, state_template=tpl)
    await async_trigger(hass, TEST_STATE_ENTITY_ID)
    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(expected)


@test.cases(
    test.case(
        "legacy", style=ConfigurationStyle.LEGACY, attribute="icon_template"
    ),
    test.case("modern", style=ConfigurationStyle.MODERN, attribute="icon"),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, attribute="icon"),
)
async def icon_template(
    *,
    style: ConfigurationStyle,
    attribute: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test icon template."""
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        1,
        SWITCH_ACTIONS,
        state_template="{{ 1 == 1 }}",
        extra_config={
            attribute: "{% if states.switch.test_state.state %}mdi:check{% endif %}"
        },
    )
    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.attributes.get("icon") in ("", None)).to_be(True)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.attributes["icon"]).to_equal("mdi:check")


@test.cases(
    test.case(
        "legacy", style=ConfigurationStyle.LEGACY, attribute="entity_picture_template"
    ),
    test.case("modern", style=ConfigurationStyle.MODERN, attribute="picture"),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, attribute="picture"),
)
async def entity_picture_template(
    *,
    style: ConfigurationStyle,
    attribute: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test entity_picture template."""
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        1,
        SWITCH_ACTIONS,
        state_template="{{ 1 == 1 }}",
        extra_config={
            attribute: (
                "{% if states.switch.test_state.state %}/local/switch.png{% endif %}"
            )
        },
    )

    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.attributes.get("entity_picture") in ("", None)).to_be(True)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.attributes["entity_picture"]).to_equal("/local/switch.png")


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_syntax_error(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test templating syntax error."""
    await setup_entity(
        hass, TEST_SWITCH, style, 0, SWITCH_ACTIONS, state_template="{% if rubbish %}"
    )
    expect(hass.states.async_all("switch")).to_equal([])


@test
async def invalid_legacy_slug_does_not_create(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test invalid legacy slug."""
    with assert_setup_component(0, "switch"):
        expect(
            await async_setup_component(
                hass,
                "switch",
                {
                    "switch": {
                        "platform": "template",
                        "switches": {
                            "test INVALID switch": {
                                **SWITCH_ACTIONS,
                                "value_template": "{{ rubbish }",
                            }
                        },
                    }
                },
            )
        ).to_be(True)

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(hass.states.async_all("switch")).to_equal([])


@test.cases(
    test.case(
        "template",
        config={"template": {"switch": "Invalid"}},
        domain=template.DOMAIN,
    ),
    test.case(
        "switch",
        config={
            "switch": {
                "platform": "template",
                "switches": {TEST_SWITCH.object_id: "Invalid"},
            }
        },
        domain=switch.DOMAIN,
    ),
)
async def invalid_switch_does_not_create(
    *,
    config: dict[str, Any],
    domain: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test invalid switch."""
    with assert_setup_component(0, domain):
        expect(await async_setup_component(hass, domain, config)).to_be(True)

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(hass.states.async_all("switch")).to_equal([])


@test.cases(
    test.case(
        "template_empty",
        config={"template": {"switch": []}},
        domain=template.DOMAIN,
        count=1,
    ),
    test.case(
        "switch_no_switches",
        config={"switch": {"platform": "template"}},
        domain=switch.DOMAIN,
        count=0,
    ),
)
async def no_switches_does_not_create(
    *,
    config: dict[str, Any],
    domain: str,
    count: int,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test if there are no switches no creation."""
    with assert_setup_component(count, domain):
        expect(await async_setup_component(hass, domain, config)).to_be(True)

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(hass.states.async_all("switch")).to_equal([])


@test.cases(
    test.case(
        "legacy_no_on",
        style=ConfigurationStyle.LEGACY,
        config={"not_on": [], **TURN_OFF_ACTION},
    ),
    test.case(
        "legacy_no_off",
        style=ConfigurationStyle.LEGACY,
        config={**TURN_ON_ACTION, "not_off": []},
    ),
    test.case(
        "modern_no_on",
        style=ConfigurationStyle.MODERN,
        config={"not_on": [], **TURN_OFF_ACTION},
    ),
    test.case(
        "modern_no_off",
        style=ConfigurationStyle.MODERN,
        config={**TURN_ON_ACTION, "not_off": []},
    ),
    test.case(
        "trigger_no_on",
        style=ConfigurationStyle.TRIGGER,
        config={"not_on": [], **TURN_OFF_ACTION},
    ),
    test.case(
        "trigger_no_off",
        style=ConfigurationStyle.TRIGGER,
        config={**TURN_ON_ACTION, "not_off": []},
    ),
)
async def missing_action_does_not_create(
    *,
    style: ConfigurationStyle,
    config: dict[str, Any],
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test missing actions."""
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        0,
        config,
        state_template="{{ states.switch.test_state.state }}",
    )
    expect(hass.states.async_all("switch")).to_equal([])


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def on_action(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test on action."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        1,
        SWITCH_ACTIONS,
        state_template="{{ states('switch.test_state') }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)

    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.state).to_be(STATE_OFF)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )

    assert_action(TEST_SWITCH, calls, 1, "turn_on")


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def on_action_optimistic(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test on action in optimistic mode."""
    calls = mock_calls(hass)
    await setup_entity(hass, TEST_SWITCH, style, 1, SWITCH_ACTIONS)

    hass.states.async_set(TEST_SWITCH.entity_id, STATE_OFF)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.state).to_be(STATE_OFF)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )

    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.state).to_be(STATE_ON)

    assert_action(TEST_SWITCH, calls, 1, "turn_on")


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def off_action(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test off action."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        1,
        SWITCH_ACTIONS,
        state_template="{{ states.switch.test_state.state }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.state).to_be(STATE_ON)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )
    assert_action(TEST_SWITCH, calls, 1, "turn_off")


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def off_action_optimistic(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test off action in optimistic mode."""
    calls = mock_calls(hass)
    await setup_entity(hass, TEST_SWITCH, style, 1, SWITCH_ACTIONS)
    hass.states.async_set(TEST_SWITCH.entity_id, STATE_ON)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.state).to_be(STATE_ON)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )
    state = hass.states.get(TEST_SWITCH.entity_id)
    expect(state.state).to_be(STATE_OFF)
    assert_action(TEST_SWITCH, calls, 1, "turn_off")


@test.skip("requires mock_restore_cache + recorder mock — port deferred")
async def restore_state() -> None:
    """Stub: requires recorder + restore-cache scaffolding."""


@test.cases(
    test.case(
        "legacy", style=ConfigurationStyle.LEGACY, attribute="availability_template"
    ),
    test.case(
        "modern", style=ConfigurationStyle.MODERN, attribute="availability"
    ),
    test.case(
        "trigger", style=ConfigurationStyle.TRIGGER, attribute="availability"
    ),
)
async def available_template_with_entities(
    *,
    style: ConfigurationStyle,
    attribute: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test availability templates with values from other entities."""
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        1,
        SWITCH_ACTIONS,
        state_template="{{ 1 == 1 }}",
        extra_config={attribute: "{{ is_state('switch.test_state', 'on') }}"},
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    expect(
        hass.states.get(TEST_SWITCH.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)
    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(STATE_UNAVAILABLE)


@test.cases(
    test.case(
        "legacy",
        style=ConfigurationStyle.LEGACY,
        config={"availability_template": "{{ x - 12 }}"},
    ),
    test.case(
        "modern",
        style=ConfigurationStyle.MODERN,
        config={"availability": "{{ x - 12 }}"},
    ),
    test.case(
        "trigger",
        style=ConfigurationStyle.TRIGGER,
        config={"availability": "{{ x - 12 }}"},
    ),
)
async def invalid_availability_template_keeps_component_available(
    *,
    style: ConfigurationStyle,
    config: dict[str, Any],
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that an invalid availability keeps the device available."""
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        1,
        config,
        extra_config=SWITCH_ACTIONS,
        state_template="{{ true }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID)
    expect(
        hass.states.get(TEST_SWITCH.entity_id).state != STATE_UNAVAILABLE
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
    """Test unique_id option only creates one switch per id."""
    await setup_and_test_unique_id(hass, TEST_SWITCH, style, SWITCH_ACTIONS)


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
    """Test a template unique_id propagates to switch unique_ids."""
    await setup_and_test_nested_unique_id(
        hass, TEST_SWITCH, style, entity_registry, SWITCH_ACTIONS
    )


@test
async def device_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for device for Template."""
    device_config_entry = MockConfigEntry()
    device_config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=device_config_entry.entry_id,
        identifiers={("test", "identifier_test")},
        connections={("mac", "30:31:32:33:34:35")},
    )
    await hass.async_block_till_done()
    expect(device_entry).not_.to_be(None)

    template_config_entry = MockConfigEntry(
        data={},
        domain=template.DOMAIN,
        options={
            "name": "My template",
            "state": "{{ true }}",
            "template_type": "switch",
            "device_id": device_entry.id,
        },
        title="My template",
    )
    template_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(template_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    template_entity = entity_registry.async_get("switch.my_template")
    expect(template_entity).not_.to_be(None)
    expect(template_entity.device_id).to_equal(device_entry.id)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def empty_action_config(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test configuration with empty script."""
    await setup_entity(
        hass, TEST_SWITCH, style, 1, {"turn_on": [], "turn_off": []}
    )

    await hass.services.async_call(
        switch.DOMAIN,
        switch.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )
    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(STATE_ON)

    await hass.services.async_call(
        switch.DOMAIN,
        switch.SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )
    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(STATE_OFF)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def optimistic_option(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test optimistic yaml option."""
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        1,
        {
            "state": "{{ is_state('switch.test_state', 'on') }}",
            "turn_on": [],
            "turn_off": [],
            "optimistic": True,
        },
    )
    hass.states.async_set(TEST_STATE_ENTITY_ID, STATE_OFF)
    await hass.async_block_till_done()

    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(STATE_OFF)

    await hass.services.async_call(
        switch.DOMAIN,
        "turn_on",
        {"entity_id": TEST_SWITCH.entity_id},
        blocking=True,
    )
    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(STATE_ON)

    hass.states.async_set(TEST_STATE_ENTITY_ID, STATE_ON)
    await hass.async_block_till_done()

    hass.states.async_set(TEST_STATE_ENTITY_ID, STATE_OFF)
    await hass.async_block_till_done()

    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(STATE_OFF)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN, expected=STATE_OFF),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, expected=STATE_UNKNOWN),
)
async def not_optimistic(
    *,
    style: ConfigurationStyle,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test optimistic yaml option set to false."""
    await setup_entity(
        hass,
        TEST_SWITCH,
        style,
        1,
        {
            "state": "{{ is_state('switch.test_state', 'on') }}",
            "turn_on": [],
            "turn_off": [],
            "optimistic": False,
        },
    )

    await hass.services.async_call(
        switch.DOMAIN,
        "turn_on",
        {"entity_id": TEST_SWITCH.entity_id},
        blocking=True,
    )

    expect(hass.states.get(TEST_SWITCH.entity_id).state).to_be(expected)


@test.skip("trigger_attributes_with_optimistic_state needs trigger-only setup variant")
async def trigger_attributes_with_optimistic_state() -> None:
    """Stub: nontrivial trigger-only optimistic attribute test."""
