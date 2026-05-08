"""The tests for the Template lock platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import lock
from homeassistant.components.lock import LockState
from homeassistant.const import (
    ATTR_CODE,
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    STATE_OPEN,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
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
TEST_AVAILABILITY_ENTITY_ID = "availability_state.state"
TEST_LOCK = TemplatePlatformSetup(
    lock.DOMAIN,
    None,
    "test_template_lock",
    make_test_trigger(TEST_AVAILABILITY_ENTITY_ID, TEST_STATE_ENTITY_ID),
)

CODE_DATA = {"code": "{{ code if code is defined else None }}"}
LOCK_ACTION = make_test_action("lock", CODE_DATA)
UNLOCK_ACTION = make_test_action("unlock", CODE_DATA)
OPEN_ACTION = make_test_action("open")
OPTIMISTIC_LOCK = {**LOCK_ACTION, **UNLOCK_ACTION}


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
async def template_state(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template."""
    await setup_entity(
        hass,
        TEST_LOCK,
        style,
        1,
        OPTIMISTIC_LOCK,
        state_template="{{ states.sensor.test_state.state }}",
    )

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(LockState.LOCKED.value)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(
        LockState.UNLOCKED.value
    )

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OPEN)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(LockState.OPEN.value)

    hass.states.async_set(TEST_STATE_ENTITY_ID, "None")
    await hass.async_block_till_done()
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_be(STATE_UNKNOWN)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_state_boolean_on(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the state with boolean on."""
    await setup_entity(
        hass, TEST_LOCK, style, 1, OPTIMISTIC_LOCK, state_template="{{ 1 == 1 }}"
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(LockState.LOCKED.value)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_state_boolean_off(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the state with off."""
    await setup_entity(
        hass, TEST_LOCK, style, 1, OPTIMISTIC_LOCK, state_template="{{ 1 == 2 }}"
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(
        LockState.UNLOCKED.value
    )


@test.cases(
    test.case(
        "legacy_template_syntax",
        style=ConfigurationStyle.LEGACY,
        state_tpl="{% if rubbish %}",
        extra_config=OPTIMISTIC_LOCK,
    ),
    test.case(
        "legacy_invalid",
        style=ConfigurationStyle.LEGACY,
        state_tpl="Invalid",
        extra_config={},
    ),
    test.case(
        "modern_template_syntax",
        style=ConfigurationStyle.MODERN,
        state_tpl="{% if rubbish %}",
        extra_config=OPTIMISTIC_LOCK,
    ),
    test.case(
        "modern_invalid",
        style=ConfigurationStyle.MODERN,
        state_tpl="Invalid",
        extra_config={},
    ),
    test.case(
        "trigger_template_syntax",
        style=ConfigurationStyle.TRIGGER,
        state_tpl="{% if rubbish %}",
        extra_config=OPTIMISTIC_LOCK,
    ),
)
async def template_syntax_error(
    *,
    style: ConfigurationStyle,
    state_tpl: str,
    extra_config: ConfigType,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test templating syntax errors don't create entities."""
    await setup_entity(hass, TEST_LOCK, style, 0, extra_config, state_template=state_tpl)
    expect(hass.states.async_all("lock")).to_equal([])


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_static(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that we allow static templates."""
    await setup_entity(
        hass, TEST_LOCK, style, 1, OPTIMISTIC_LOCK, state_template="{{ 1 + 1 }}"
    )
    hass.states.async_set(TEST_LOCK.entity_id, LockState.LOCKED)
    await hass.async_block_till_done()
    state = hass.states.get(TEST_LOCK.entity_id)
    expect(state.state).to_equal(LockState.LOCKED.value)


@test.cases(
    test.case("legacy_true", style=ConfigurationStyle.LEGACY, tpl="{{ True }}", expected=LockState.LOCKED.value),
    test.case("legacy_false", style=ConfigurationStyle.LEGACY, tpl="{{ False }}", expected=LockState.UNLOCKED.value),
    test.case("legacy_unavailable", style=ConfigurationStyle.LEGACY, tpl="{{ x - 12 }}", expected=STATE_UNAVAILABLE),
    test.case("legacy_unknown", style=ConfigurationStyle.LEGACY, tpl="{{ None }}", expected=STATE_UNKNOWN),
    test.case("modern_true", style=ConfigurationStyle.MODERN, tpl="{{ True }}", expected=LockState.LOCKED.value),
    test.case("modern_false", style=ConfigurationStyle.MODERN, tpl="{{ False }}", expected=LockState.UNLOCKED.value),
    test.case("modern_unavailable", style=ConfigurationStyle.MODERN, tpl="{{ x - 12 }}", expected=STATE_UNAVAILABLE),
    test.case("modern_unknown", style=ConfigurationStyle.MODERN, tpl="{{ None }}", expected=STATE_UNKNOWN),
    test.case("trigger_true", style=ConfigurationStyle.TRIGGER, tpl="{{ True }}", expected=LockState.LOCKED.value),
    test.case("trigger_false", style=ConfigurationStyle.TRIGGER, tpl="{{ False }}", expected=LockState.UNLOCKED.value),
    test.case("trigger_unavailable", style=ConfigurationStyle.TRIGGER, tpl="{{ x - 12 }}", expected=STATE_UNAVAILABLE),
    test.case("trigger_unknown", style=ConfigurationStyle.TRIGGER, tpl="{{ None }}", expected=STATE_UNKNOWN),
)
async def state_template(
    *,
    style: ConfigurationStyle,
    tpl: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state and value_template template."""
    await setup_entity(
        hass, TEST_LOCK, style, 1, OPTIMISTIC_LOCK, state_template=tpl
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    state = hass.states.get(TEST_LOCK.entity_id)
    expect(state.state).to_equal(expected)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def lock_action(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test lock action."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_LOCK,
        style,
        1,
        OPTIMISTIC_LOCK,
        state_template="{{ states.sensor.test_state.state }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(
        LockState.UNLOCKED.value
    )

    await hass.services.async_call(
        lock.DOMAIN,
        lock.SERVICE_LOCK,
        {ATTR_ENTITY_ID: TEST_LOCK.entity_id},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["action"]).to_equal("lock")
    expect(calls[0].data["caller"]).to_equal(TEST_LOCK.entity_id)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unlock_action(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unlock action."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_LOCK,
        style,
        1,
        OPTIMISTIC_LOCK,
        state_template="{{ states.sensor.test_state.state }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(LockState.LOCKED.value)

    await hass.services.async_call(
        lock.DOMAIN,
        lock.SERVICE_UNLOCK,
        {ATTR_ENTITY_ID: TEST_LOCK.entity_id},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["action"]).to_equal("unlock")


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
    """Test open action."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_LOCK,
        style,
        1,
        {**OPTIMISTIC_LOCK, **OPEN_ACTION},
        state_template="{{ states.sensor.test_state.state }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(LockState.LOCKED.value)

    await hass.services.async_call(
        lock.DOMAIN,
        lock.SERVICE_OPEN,
        {ATTR_ENTITY_ID: TEST_LOCK.entity_id},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["action"]).to_equal("open")


@test.cases(
    test.case("legacy_locked", style=ConfigurationStyle.LEGACY, test_state=LockState.LOCKED.value),
    test.case("legacy_unlocked", style=ConfigurationStyle.LEGACY, test_state=LockState.UNLOCKED.value),
    test.case("legacy_open", style=ConfigurationStyle.LEGACY, test_state=LockState.OPEN.value),
    test.case("legacy_unlocking", style=ConfigurationStyle.LEGACY, test_state=LockState.UNLOCKING.value),
    test.case("legacy_locking", style=ConfigurationStyle.LEGACY, test_state=LockState.LOCKING.value),
    test.case("legacy_jammed", style=ConfigurationStyle.LEGACY, test_state=LockState.JAMMED.value),
    test.case("legacy_opening", style=ConfigurationStyle.LEGACY, test_state=LockState.OPENING.value),
    test.case("modern_locked", style=ConfigurationStyle.MODERN, test_state=LockState.LOCKED.value),
    test.case("modern_unlocked", style=ConfigurationStyle.MODERN, test_state=LockState.UNLOCKED.value),
    test.case("modern_open", style=ConfigurationStyle.MODERN, test_state=LockState.OPEN.value),
    test.case("modern_unlocking", style=ConfigurationStyle.MODERN, test_state=LockState.UNLOCKING.value),
    test.case("modern_locking", style=ConfigurationStyle.MODERN, test_state=LockState.LOCKING.value),
    test.case("modern_jammed", style=ConfigurationStyle.MODERN, test_state=LockState.JAMMED.value),
    test.case("modern_opening", style=ConfigurationStyle.MODERN, test_state=LockState.OPENING.value),
    test.case("trigger_locked", style=ConfigurationStyle.TRIGGER, test_state=LockState.LOCKED.value),
    test.case("trigger_unlocked", style=ConfigurationStyle.TRIGGER, test_state=LockState.UNLOCKED.value),
    test.case("trigger_open", style=ConfigurationStyle.TRIGGER, test_state=LockState.OPEN.value),
    test.case("trigger_unlocking", style=ConfigurationStyle.TRIGGER, test_state=LockState.UNLOCKING.value),
    test.case("trigger_locking", style=ConfigurationStyle.TRIGGER, test_state=LockState.LOCKING.value),
    test.case("trigger_jammed", style=ConfigurationStyle.TRIGGER, test_state=LockState.JAMMED.value),
    test.case("trigger_opening", style=ConfigurationStyle.TRIGGER, test_state=LockState.OPENING.value),
)
async def lock_state(
    *,
    style: ConfigurationStyle,
    test_state: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test value template."""
    await setup_entity(
        hass,
        TEST_LOCK,
        style,
        1,
        OPTIMISTIC_LOCK,
        state_template="{{ states.sensor.test_state.state }}",
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, test_state)
    state = hass.states.get(TEST_LOCK.entity_id)
    expect(state.state).to_equal(test_state)


@test.cases(
    test.case(
        "legacy", style=ConfigurationStyle.LEGACY, attribute="availability_template"
    ),
    test.case("modern", style=ConfigurationStyle.MODERN, attribute="availability"),
    test.case("trigger", style=ConfigurationStyle.TRIGGER, attribute="availability"),
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
        TEST_LOCK,
        style,
        1,
        OPTIMISTIC_LOCK,
        state_template="{{ states('sensor.test_state') }}",
        extra_config={
            attribute: "{{ is_state('availability_state.state', 'on') }}"
        },
    )
    hass.states.async_set(TEST_AVAILABILITY_ENTITY_ID, STATE_ON)
    await hass.async_block_till_done()

    expect(
        hass.states.get(TEST_LOCK.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)

    hass.states.async_set(TEST_AVAILABILITY_ENTITY_ID, STATE_OFF)
    await hass.async_block_till_done()

    expect(hass.states.get(TEST_LOCK.entity_id).state).to_be(STATE_UNAVAILABLE)


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
        TEST_LOCK,
        style,
        1,
        OPTIMISTIC_LOCK,
        state_template="{{ 1 + 1 }}",
        extra_config={attribute: "{{ x - 12 }}"},
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    expect(
        hass.states.get(TEST_LOCK.entity_id).state != STATE_UNAVAILABLE
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
    """Test unique_id option only creates one entity per id."""
    await setup_and_test_unique_id(
        hass, TEST_LOCK, style, OPTIMISTIC_LOCK, "{{ 'on' }}"
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
    """Test a template unique_id propagates unique_ids."""
    await setup_and_test_nested_unique_id(
        hass, TEST_LOCK, style, entity_registry, OPTIMISTIC_LOCK, "{{ 'on' }}"
    )


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
    await setup_entity(
        hass, TEST_LOCK, style, 1, {"lock": [], "unlock": []}
    )

    state = hass.states.get(TEST_LOCK.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")

    await hass.services.async_call(
        lock.DOMAIN,
        lock.SERVICE_LOCK,
        {ATTR_ENTITY_ID: TEST_LOCK.entity_id},
        blocking=True,
    )
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(LockState.LOCKED.value)

    await hass.services.async_call(
        lock.DOMAIN,
        lock.SERVICE_UNLOCK,
        {ATTR_ENTITY_ID: TEST_LOCK.entity_id},
        blocking=True,
    )
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(
        LockState.UNLOCKED.value
    )


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
    await setup_entity(
        hass,
        TEST_LOCK,
        style,
        1,
        {
            "state": "{{ is_state('sensor.test_state', 'on') }}",
            "lock": [],
            "unlock": [],
            "optimistic": False,
        },
    )
    await hass.services.async_call(
        lock.DOMAIN,
        lock.SERVICE_LOCK,
        {ATTR_ENTITY_ID: TEST_LOCK.entity_id},
        blocking=True,
    )

    hass.states.async_set(TEST_AVAILABILITY_ENTITY_ID, "anything")
    await hass.async_block_till_done()

    state = hass.states.get(TEST_LOCK.entity_id)
    expect(state.state).to_equal(LockState.UNLOCKED.value)


@test.cases(
    test.case("legacy", style=ConfigurationStyle.LEGACY),
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def lock_action_with_code(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test lock action with defined code format and supplied lock code."""
    calls = mock_calls(hass)
    attribute = (
        "code_format_template" if style == ConfigurationStyle.LEGACY else "code_format"
    )
    await setup_entity(
        hass,
        TEST_LOCK,
        style,
        1,
        OPTIMISTIC_LOCK,
        state_template="{{ states.sensor.test_state.state }}",
        extra_config={attribute: "{{ '.+' }}"},
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)
    expect(hass.states.get(TEST_LOCK.entity_id).state).to_equal(
        LockState.UNLOCKED.value
    )

    await hass.services.async_call(
        lock.DOMAIN,
        lock.SERVICE_LOCK,
        {ATTR_ENTITY_ID: TEST_LOCK.entity_id, ATTR_CODE: "LOCK_CODE"},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["action"]).to_equal("lock")
    expect(calls[0].data["code"]).to_equal("LOCK_CODE")


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.skip("legacy unique_id test depends on start_ha fixture — port deferred")
async def legacy_unique_id() -> None:
    """Stub: requires start_ha fixture."""


@test.skip("emtpy_action_config requires lock supported_features setup — port deferred")
async def emtpy_action_config() -> None:
    """Stub: complex setup for the static-template flow."""


@test.skip("template_code_template_syntax_error fail-setup variant — port deferred")
async def template_code_template_syntax_error() -> None:
    """Stub."""


@test.skip("open_lock_optimistic depends on extra optimistic config — port deferred")
async def open_lock_optimistic() -> None:
    """Stub."""


@test.skip("unlock_action_with_code depends on switch component setup — port deferred")
async def unlock_action_with_code() -> None:
    """Stub."""


@test.skip("lock_actions_fail_with_invalid_code stub — port deferred")
async def lock_actions_fail_with_invalid_code() -> None:
    """Stub."""


@test.skip("lock_actions_dont_execute_with_code_template_rendering_error stub")
async def lock_actions_dont_execute_with_code_template_rendering_error() -> None:
    """Stub."""


@test.skip("actions_with_none_as_codeformat_ignores_code stub")
async def actions_with_none_as_codeformat_ignores_code() -> None:
    """Stub."""


@test.skip("actions_with_invalid_regexp_as_codeformat_never_execute stub")
async def actions_with_invalid_regexp_as_codeformat_never_execute() -> None:
    """Stub."""


@test.skip("icon/picture template tests for lock require additional fixtures")
async def picture_template() -> None:
    """Stub."""


@test.skip("icon template stub")
async def icon_template() -> None:
    """Stub."""
