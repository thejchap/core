"""The tests for the Template alarm control panel platform."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import template
from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    AlarmControlPanelState,
)
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import ConfigType

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

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

TEST_STATE_ENTITY_ID = "sensor.test_state"
TEST_AVAILABILITY_ENTITY = "binary_sensor.availability"

TEST_PANEL = TemplatePlatformSetup(
    ALARM_DOMAIN,
    "panels",
    "test_template_panel",
    make_test_trigger(TEST_STATE_ENTITY_ID, TEST_AVAILABILITY_ENTITY),
)

DATA_CODE = {"code": "{{ code }}"}
ARM_AWAY_ACTION = make_test_action("arm_away", DATA_CODE)
ARM_HOME_ACTION = make_test_action("arm_home", DATA_CODE)
ARM_NIGHT_ACTION = make_test_action("arm_night", DATA_CODE)
ARM_VACATION_ACTION = make_test_action("arm_vacation", DATA_CODE)
ARM_CUSTOM_BYPASS_ACTION = make_test_action("arm_custom_bypass", DATA_CODE)
DISARM_ACTION = make_test_action("disarm", DATA_CODE)
TRIGGER_ACTION = make_test_action("trigger", DATA_CODE)

OPTIMISTIC_ACTIONS = {
    **ARM_AWAY_ACTION,
    **ARM_HOME_ACTION,
    **ARM_NIGHT_ACTION,
    **ARM_VACATION_ACTION,
    **ARM_CUSTOM_BYPASS_ACTION,
    **DISARM_ACTION,
    **TRIGGER_ACTION,
}

EMPTY_ACTIONS: dict[str, Any] = {action: [] for action in OPTIMISTIC_ACTIONS}


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
async def template_state_text(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the state text of a template."""
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        OPTIMISTIC_ACTIONS,
        state_template="{{ states('sensor.test_state') }}",
    )

    for set_state in (
        AlarmControlPanelState.ARMED_AWAY,
        AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
        AlarmControlPanelState.ARMED_HOME,
        AlarmControlPanelState.ARMED_NIGHT,
        AlarmControlPanelState.ARMED_VACATION,
        AlarmControlPanelState.ARMING,
        AlarmControlPanelState.DISARMED,
        AlarmControlPanelState.DISARMING,
        AlarmControlPanelState.PENDING,
        AlarmControlPanelState.TRIGGERED,
    ):
        await async_trigger(hass, TEST_STATE_ENTITY_ID, set_state)
        state = hass.states.get(TEST_PANEL.entity_id)
        expect(state.state).to_equal(set_state.value)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "invalid_state")
    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.state).to_equal("unknown")


@test.cases(
    test.case("legacy_disarmed", style=ConfigurationStyle.LEGACY, tpl="{{ 'disarmed' }}", expected="disarmed"),
    test.case("legacy_armed_home", style=ConfigurationStyle.LEGACY, tpl="{{ 'armed_home' }}", expected="armed_home"),
    test.case("legacy_armed_away", style=ConfigurationStyle.LEGACY, tpl="{{ 'armed_away' }}", expected="armed_away"),
    test.case("legacy_armed_night", style=ConfigurationStyle.LEGACY, tpl="{{ 'armed_night' }}", expected="armed_night"),
    test.case("legacy_armed_vacation", style=ConfigurationStyle.LEGACY, tpl="{{ 'armed_vacation' }}", expected="armed_vacation"),
    test.case("legacy_armed_custom_bypass", style=ConfigurationStyle.LEGACY, tpl="{{ 'armed_custom_bypass' }}", expected="armed_custom_bypass"),
    test.case("legacy_pending", style=ConfigurationStyle.LEGACY, tpl="{{ 'pending' }}", expected="pending"),
    test.case("legacy_arming", style=ConfigurationStyle.LEGACY, tpl="{{ 'arming' }}", expected="arming"),
    test.case("legacy_disarming", style=ConfigurationStyle.LEGACY, tpl="{{ 'disarming' }}", expected="disarming"),
    test.case("legacy_triggered", style=ConfigurationStyle.LEGACY, tpl="{{ 'triggered' }}", expected="triggered"),
    test.case("legacy_invalid", style=ConfigurationStyle.LEGACY, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
    test.case("modern_disarmed", style=ConfigurationStyle.MODERN, tpl="{{ 'disarmed' }}", expected="disarmed"),
    test.case("modern_armed_home", style=ConfigurationStyle.MODERN, tpl="{{ 'armed_home' }}", expected="armed_home"),
    test.case("modern_armed_away", style=ConfigurationStyle.MODERN, tpl="{{ 'armed_away' }}", expected="armed_away"),
    test.case("modern_armed_night", style=ConfigurationStyle.MODERN, tpl="{{ 'armed_night' }}", expected="armed_night"),
    test.case("modern_armed_vacation", style=ConfigurationStyle.MODERN, tpl="{{ 'armed_vacation' }}", expected="armed_vacation"),
    test.case("modern_armed_custom_bypass", style=ConfigurationStyle.MODERN, tpl="{{ 'armed_custom_bypass' }}", expected="armed_custom_bypass"),
    test.case("modern_pending", style=ConfigurationStyle.MODERN, tpl="{{ 'pending' }}", expected="pending"),
    test.case("modern_arming", style=ConfigurationStyle.MODERN, tpl="{{ 'arming' }}", expected="arming"),
    test.case("modern_disarming", style=ConfigurationStyle.MODERN, tpl="{{ 'disarming' }}", expected="disarming"),
    test.case("modern_triggered", style=ConfigurationStyle.MODERN, tpl="{{ 'triggered' }}", expected="triggered"),
    test.case("modern_invalid", style=ConfigurationStyle.MODERN, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
    test.case("trigger_disarmed", style=ConfigurationStyle.TRIGGER, tpl="{{ 'disarmed' }}", expected="disarmed"),
    test.case("trigger_armed_home", style=ConfigurationStyle.TRIGGER, tpl="{{ 'armed_home' }}", expected="armed_home"),
    test.case("trigger_armed_away", style=ConfigurationStyle.TRIGGER, tpl="{{ 'armed_away' }}", expected="armed_away"),
    test.case("trigger_armed_night", style=ConfigurationStyle.TRIGGER, tpl="{{ 'armed_night' }}", expected="armed_night"),
    test.case("trigger_armed_vacation", style=ConfigurationStyle.TRIGGER, tpl="{{ 'armed_vacation' }}", expected="armed_vacation"),
    test.case("trigger_armed_custom_bypass", style=ConfigurationStyle.TRIGGER, tpl="{{ 'armed_custom_bypass' }}", expected="armed_custom_bypass"),
    test.case("trigger_pending", style=ConfigurationStyle.TRIGGER, tpl="{{ 'pending' }}", expected="pending"),
    test.case("trigger_arming", style=ConfigurationStyle.TRIGGER, tpl="{{ 'arming' }}", expected="arming"),
    test.case("trigger_disarming", style=ConfigurationStyle.TRIGGER, tpl="{{ 'disarming' }}", expected="disarming"),
    test.case("trigger_triggered", style=ConfigurationStyle.TRIGGER, tpl="{{ 'triggered' }}", expected="triggered"),
    test.case("trigger_invalid", style=ConfigurationStyle.TRIGGER, tpl="{{ x - 1 }}", expected=STATE_UNAVAILABLE),
)
async def state_template_states(
    *,
    style: ConfigurationStyle,
    tpl: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the state template."""
    await setup_entity(
        hass, TEST_PANEL, style, 1, OPTIMISTIC_ACTIONS, state_template=tpl
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, None)
    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.state).to_equal(expected)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN, initial_state=""),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, initial_state=None),
)
async def icon_template(
    *,
    style: ConfigurationStyle,
    initial_state: str | None,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test icon template."""
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        OPTIMISTIC_ACTIONS,
        state_template="{{ 'disarmed' }}",
        extra_config={
            "icon": "{% if states.sensor.test_state.state %}mdi:check{% endif %}"
        },
    )

    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.attributes.get("icon")).to_equal(initial_state)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.attributes["icon"]).to_equal("mdi:check")


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN, initial_state=""),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, initial_state=None),
)
async def picture_template(
    *,
    style: ConfigurationStyle,
    initial_state: str | None,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test picture template."""
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        OPTIMISTIC_ACTIONS,
        state_template="{{ 'disarmed' }}",
        extra_config={
            "picture": (
                "{% if states.sensor.test_state.state %}local/panel.png{% endif %}"
            )
        },
    )
    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.attributes.get("entity_picture")).to_equal(initial_state)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.attributes["entity_picture"]).to_equal("local/panel.png")


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.cases(
    test.case("legacy_optimistic", style=ConfigurationStyle.LEGACY, panel_config=OPTIMISTIC_ACTIONS),
    test.case("legacy_empty", style=ConfigurationStyle.LEGACY, panel_config=EMPTY_ACTIONS),
    test.case("modern_optimistic", style=ConfigurationStyle.MODERN, panel_config=OPTIMISTIC_ACTIONS),
    test.case("modern_empty", style=ConfigurationStyle.MODERN, panel_config=EMPTY_ACTIONS),
    test.case("trigger_optimistic", style=ConfigurationStyle.TRIGGER, panel_config=OPTIMISTIC_ACTIONS),
    test.case("trigger_empty", style=ConfigurationStyle.TRIGGER, panel_config=EMPTY_ACTIONS),
)
async def optimistic_states(
    *,
    style: ConfigurationStyle,
    panel_config: ConfigType,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the optimistic state."""
    mock_calls(hass)
    await setup_entity(hass, TEST_PANEL, style, 1, panel_config)

    state = hass.states.get(TEST_PANEL.entity_id)
    await hass.async_block_till_done()
    expect(state.state).to_equal("unknown")

    for service, set_state in (
        ("alarm_arm_away", AlarmControlPanelState.ARMED_AWAY),
        ("alarm_arm_home", AlarmControlPanelState.ARMED_HOME),
        ("alarm_arm_night", AlarmControlPanelState.ARMED_NIGHT),
        ("alarm_arm_vacation", AlarmControlPanelState.ARMED_VACATION),
        ("alarm_arm_custom_bypass", AlarmControlPanelState.ARMED_CUSTOM_BYPASS),
        ("alarm_disarm", AlarmControlPanelState.DISARMED),
        ("alarm_trigger", AlarmControlPanelState.TRIGGERED),
    ):
        await hass.services.async_call(
            ALARM_DOMAIN,
            service,
            {"entity_id": TEST_PANEL.entity_id, "code": "1234"},
            blocking=True,
        )
        await hass.async_block_till_done()
        expect(hass.states.get(TEST_PANEL.entity_id).state).to_equal(set_state.value)


@test.cases(
    test.case(
        "legacy_entity_id",
        style=ConfigurationStyle.LEGACY,
        test_entity_id=TEST_PANEL.entity_id,
    ),
    test.case(
        "modern_entity_id",
        style=ConfigurationStyle.MODERN,
        test_entity_id="alarm_control_panel.template_alarm_panel",
    ),
    test.case(
        "trigger_entity_id",
        style=ConfigurationStyle.TRIGGER,
        test_entity_id="alarm_control_panel.unnamed_device",
    ),
)
async def name(
    *,
    style: ConfigurationStyle,
    test_entity_id: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the accessibility of the name attribute."""
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        OPTIMISTIC_ACTIONS,
        state_template="disarmed",
        extra_config={"name": '{{ "Template Alarm Panel" }}'},
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "disarmed")

    state = hass.states.get(test_entity_id)
    expect(state).not_.to_be(None)
    expect(state.attributes.get("friendly_name")).to_equal("Template Alarm Panel")


@test.cases(
    test.case("legacy_arm_home", style=ConfigurationStyle.LEGACY, service="alarm_arm_home", expected_service="arm_home"),
    test.case("legacy_arm_away", style=ConfigurationStyle.LEGACY, service="alarm_arm_away", expected_service="arm_away"),
    test.case("legacy_arm_night", style=ConfigurationStyle.LEGACY, service="alarm_arm_night", expected_service="arm_night"),
    test.case("legacy_arm_vacation", style=ConfigurationStyle.LEGACY, service="alarm_arm_vacation", expected_service="arm_vacation"),
    test.case("legacy_arm_custom_bypass", style=ConfigurationStyle.LEGACY, service="alarm_arm_custom_bypass", expected_service="arm_custom_bypass"),
    test.case("legacy_disarm", style=ConfigurationStyle.LEGACY, service="alarm_disarm", expected_service="disarm"),
    test.case("legacy_trigger", style=ConfigurationStyle.LEGACY, service="alarm_trigger", expected_service="trigger"),
    test.case("modern_arm_home", style=ConfigurationStyle.MODERN, service="alarm_arm_home", expected_service="arm_home"),
    test.case("modern_arm_away", style=ConfigurationStyle.MODERN, service="alarm_arm_away", expected_service="arm_away"),
    test.case("modern_arm_night", style=ConfigurationStyle.MODERN, service="alarm_arm_night", expected_service="arm_night"),
    test.case("modern_arm_vacation", style=ConfigurationStyle.MODERN, service="alarm_arm_vacation", expected_service="arm_vacation"),
    test.case("modern_arm_custom_bypass", style=ConfigurationStyle.MODERN, service="alarm_arm_custom_bypass", expected_service="arm_custom_bypass"),
    test.case("modern_disarm", style=ConfigurationStyle.MODERN, service="alarm_disarm", expected_service="disarm"),
    test.case("modern_trigger", style=ConfigurationStyle.MODERN, service="alarm_trigger", expected_service="trigger"),
    test.case("trigger_arm_home", style=ConfigurationStyle.TRIGGER, service="alarm_arm_home", expected_service="arm_home"),
    test.case("trigger_arm_away", style=ConfigurationStyle.TRIGGER, service="alarm_arm_away", expected_service="arm_away"),
    test.case("trigger_arm_night", style=ConfigurationStyle.TRIGGER, service="alarm_arm_night", expected_service="arm_night"),
    test.case("trigger_arm_vacation", style=ConfigurationStyle.TRIGGER, service="alarm_arm_vacation", expected_service="arm_vacation"),
    test.case("trigger_arm_custom_bypass", style=ConfigurationStyle.TRIGGER, service="alarm_arm_custom_bypass", expected_service="arm_custom_bypass"),
    test.case("trigger_disarm", style=ConfigurationStyle.TRIGGER, service="alarm_disarm", expected_service="disarm"),
    test.case("trigger_trigger", style=ConfigurationStyle.TRIGGER, service="alarm_trigger", expected_service="trigger"),
)
async def actions(
    *,
    style: ConfigurationStyle,
    service: str,
    expected_service: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test alarm actions."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        OPTIMISTIC_ACTIONS,
        state_template="{{ states('sensor.test_state') }}",
    )
    await hass.services.async_call(
        ALARM_DOMAIN,
        service,
        {"entity_id": TEST_PANEL.entity_id, "code": "1234"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert_action(TEST_PANEL, calls, 1, expected_service, code=1234)


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
    """Test unique_id option only creates one alarm control panel per id."""
    await setup_and_test_unique_id(hass, TEST_PANEL, style, OPTIMISTIC_ACTIONS)


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
    """Test a template unique_id propagates to alarm control panel unique_ids."""
    await setup_and_test_nested_unique_id(
        hass, TEST_PANEL, style, entity_registry, OPTIMISTIC_ACTIONS
    )


@test.cases(
    test.case("legacy_default", style=ConfigurationStyle.LEGACY, extra={}, code_format="number", code_arm_required=True),
    test.case("legacy_text", style=ConfigurationStyle.LEGACY, extra={"code_format": "text"}, code_format="text", code_arm_required=True),
    test.case("legacy_no_code_no_arm", style=ConfigurationStyle.LEGACY, extra={"code_format": "no_code", "code_arm_required": False}, code_format=None, code_arm_required=False),
    test.case("legacy_text_no_arm", style=ConfigurationStyle.LEGACY, extra={"code_format": "text", "code_arm_required": False}, code_format="text", code_arm_required=False),
    test.case("modern_default", style=ConfigurationStyle.MODERN, extra={}, code_format="number", code_arm_required=True),
    test.case("modern_text", style=ConfigurationStyle.MODERN, extra={"code_format": "text"}, code_format="text", code_arm_required=True),
    test.case("modern_no_code_no_arm", style=ConfigurationStyle.MODERN, extra={"code_format": "no_code", "code_arm_required": False}, code_format=None, code_arm_required=False),
    test.case("modern_text_no_arm", style=ConfigurationStyle.MODERN, extra={"code_format": "text", "code_arm_required": False}, code_format="text", code_arm_required=False),
    test.case("trigger_default", style=ConfigurationStyle.TRIGGER, extra={}, code_format="number", code_arm_required=True),
    test.case("trigger_text", style=ConfigurationStyle.TRIGGER, extra={"code_format": "text"}, code_format="text", code_arm_required=True),
    test.case("trigger_no_code_no_arm", style=ConfigurationStyle.TRIGGER, extra={"code_format": "no_code", "code_arm_required": False}, code_format=None, code_arm_required=False),
    test.case("trigger_text_no_arm", style=ConfigurationStyle.TRIGGER, extra={"code_format": "text", "code_arm_required": False}, code_format="text", code_arm_required=False),
)
async def code_config(
    *,
    style: ConfigurationStyle,
    extra: dict,
    code_format: str | None,
    code_arm_required: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test configuration options related to alarm code."""
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        {**OPTIMISTIC_ACTIONS, **extra},
        state_template="disarmed",
    )

    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.attributes.get("code_format")).to_equal(code_format)
    expect(state.attributes.get("code_arm_required")).to_equal(code_arm_required)


@test
async def device_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for device for button template."""
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
            "value_template": "disarmed",
            "template_type": "alarm_control_panel",
            "code_arm_required": True,
            "code_format": "number",
            "device_id": device_entry.id,
        },
        title="My template",
    )

    template_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(template_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    template_entity = entity_registry.async_get("alarm_control_panel.my_template")
    expect(template_entity).not_.to_be(None)
    expect(template_entity.device_id).to_equal(device_entry.id)


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def optimistic(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test configuration with optimistic state."""
    mock_calls(hass)
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        {
            "state": "{{ states('sensor.test_state') }}",
            **OPTIMISTIC_ACTIONS,
            "optimistic": True,
        },
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, AlarmControlPanelState.DISARMED)

    await hass.services.async_call(
        ALARM_DOMAIN,
        "alarm_arm_away",
        {"entity_id": TEST_PANEL.entity_id, "code": "1234"},
        blocking=True,
    )

    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_AWAY.value)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, AlarmControlPanelState.ARMED_HOME)
    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_HOME.value)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def not_optimistic(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test optimistic yaml option set to false."""
    mock_calls(hass)
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        {
            "state": "{{ states('sensor.test_state') }}",
            **OPTIMISTIC_ACTIONS,
            "optimistic": False,
        },
    )
    await hass.services.async_call(
        ALARM_DOMAIN,
        "alarm_arm_away",
        {"entity_id": TEST_PANEL.entity_id, "code": "1234"},
        blocking=True,
    )

    state = hass.states.get(TEST_PANEL.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def available_template_with_entities(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test availability templates with values from other entities."""
    await setup_entity(
        hass,
        TEST_PANEL,
        style,
        1,
        OPTIMISTIC_ACTIONS,
        state_template="{{ 'disarmed' }}",
        extra_config={
            "availability": "{{ is_state('binary_sensor.availability', 'on') }}"
        },
    )
    hass.states.async_set(TEST_AVAILABILITY_ENTITY, STATE_ON)
    await hass.async_block_till_done()

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)

    expect(
        hass.states.get(TEST_PANEL.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)

    hass.states.async_set(TEST_AVAILABILITY_ENTITY, STATE_OFF)
    await hass.async_block_till_done()

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)

    expect(hass.states.get(TEST_PANEL.entity_id).state).to_be(STATE_UNAVAILABLE)


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
        TEST_PANEL,
        style,
        1,
        OPTIMISTIC_ACTIONS,
        state_template="{{ 'disarmed' }}",
        extra_config={"availability": "{{ x - 12 }}"},
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")
    expect(
        hass.states.get(TEST_PANEL.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)


@test.skip("template_syntax_error needs caplog_setup_text — port deferred")
async def template_syntax_error() -> None:
    """Stub: requires caplog_setup_text fixture."""


@test.skip("legacy_template_syntax_error needs caplog_setup_text — port deferred")
async def legacy_template_syntax_error() -> None:
    """Stub: requires caplog_setup_text fixture."""


@test.skip("restore_state needs mock_restore_cache — port deferred")
async def restore_state() -> None:
    """Stub: requires mock_restore_cache scaffolding."""
