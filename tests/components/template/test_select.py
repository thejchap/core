"""The tests for the Template select platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import select
from homeassistant.components.select import (
    ATTR_OPTION as SELECT_ATTR_OPTION,
    ATTR_OPTIONS as SELECT_ATTR_OPTIONS,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION as SELECT_SERVICE_SELECT_OPTION,
)
from homeassistant.components.template import DOMAIN
from homeassistant.components.template.const import CONF_PICTURE
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_ENTITY_PICTURE,
    ATTR_ICON,
    CONF_ENTITY_ID,
    CONF_ICON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
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

TEST_STATE_ENTITY_ID = "sensor.test_state"
TEST_AVAILABILITY_ENTITY_ID = "binary_sensor.test_availability"

TEST_SELECT = TemplatePlatformSetup(
    select.DOMAIN,
    None,
    "template_select",
    make_test_trigger(TEST_STATE_ENTITY_ID, TEST_AVAILABILITY_ENTITY_ID),
)

TEST_OPTIONS_WITHOUT_STATE = {
    "options": "{{ ['test', 'yes', 'no'] }}",
    "select_option": [],
}
TEST_OPTIONS = {"state": "test", **TEST_OPTIONS_WITHOUT_STATE}
TEST_OPTION_ACTION = make_test_action("select_option", {"option": "{{ option }}"})


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


def _verify(
    hass: HomeAssistant,
    expected_current_option: str,
    expected_options: list[str],
    entity_name: str = TEST_SELECT.entity_id,
) -> None:
    """Verify select's state."""
    state = hass.states.get(entity_name)
    attributes = state.attributes
    assert state.state == str(expected_current_option)
    assert attributes.get(SELECT_ATTR_OPTIONS) == expected_options


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.cases(
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
        TEST_SELECT,
        style,
        1,
        {"state": "{{ 'a' }}", "options": "{{ ['a', 'b'] }}"},
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")
    _verify(hass, "a", ["a", "b"])


@test
async def multiple_configs(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: multiple select entities get created."""
    with assert_setup_component(1, "template"):
        expect(
            await async_setup_component(
                hass,
                "template",
                {
                    "template": {
                        "select": [
                            {
                                "state": "{{ 'a' }}",
                                "select_option": {"service": "script.select_option"},
                                "options": "{{ ['a', 'b'] }}",
                            },
                            {
                                "state": "{{ 'a' }}",
                                "select_option": {"service": "script.select_option"},
                                "options": "{{ ['a', 'b'] }}",
                            },
                        ]
                    }
                },
            )
        ).to_be(True)

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    _verify(hass, "a", ["a", "b"])
    _verify(hass, "a", ["a", "b"], f"{TEST_SELECT.entity_id}_2")


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def missing_required_keys(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: missing required fields will fail."""
    await setup_entity(
        hass,
        TEST_SELECT,
        style,
        0,
        {
            "state": "{{ 'a' }}",
            "select_option": {"service": "script.select_option"},
        },
    )
    expect(hass.states.async_all("select")).to_equal([])


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_select(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test templates with values from other entities."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_SELECT,
        style,
        1,
        {
            "options": "{{ state_attr('sensor.test_state', 'options') or [] }}",
            **TEST_OPTION_ACTION,
            "state": "{{ states('sensor.test_state') }}",
        },
    )

    attributes = {"options": ["a", "b"]}
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "a", attributes)
    _verify(hass, "a", ["a", "b"])

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "b", attributes)
    _verify(hass, "b", ["a", "b"])

    attributes = {"options": ["a", "b", "c"]}
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "b", attributes)
    _verify(hass, "b", ["a", "b", "c"])

    await hass.services.async_call(
        SELECT_DOMAIN,
        SELECT_SERVICE_SELECT_OPTION,
        {CONF_ENTITY_ID: TEST_SELECT.entity_id, SELECT_ATTR_OPTION: "c"},
        blocking=True,
    )

    assert_action(TEST_SELECT, calls, 1, "select_option", option="c")

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "c", attributes)
    _verify(hass, "c", ["a", "b", "c"])


@test.cases(
    test.case(
        "modern_icon",
        style=ConfigurationStyle.MODERN,
        initial_expected_state="",
        attribute=ATTR_ICON,
        attribute_key=CONF_ICON,
        attribute_template=(
            "{% if states.sensor.test_state.state == 'yes' %}mdi:check{% endif %}"
        ),
        expected="mdi:check",
    ),
    test.case(
        "modern_picture",
        style=ConfigurationStyle.MODERN,
        initial_expected_state="",
        attribute=ATTR_ENTITY_PICTURE,
        attribute_key=CONF_PICTURE,
        attribute_template=(
            "{% if states.sensor.test_state.state == 'yes' %}check.jpg{% endif %}"
        ),
        expected="check.jpg",
    ),
    test.case(
        "trigger_icon",
        style=ConfigurationStyle.TRIGGER,
        initial_expected_state=None,
        attribute=ATTR_ICON,
        attribute_key=CONF_ICON,
        attribute_template=(
            "{% if states.sensor.test_state.state == 'yes' %}mdi:check{% endif %}"
        ),
        expected="mdi:check",
    ),
    test.case(
        "trigger_picture",
        style=ConfigurationStyle.TRIGGER,
        initial_expected_state=None,
        attribute=ATTR_ENTITY_PICTURE,
        attribute_key=CONF_PICTURE,
        attribute_template=(
            "{% if states.sensor.test_state.state == 'yes' %}check.jpg{% endif %}"
        ),
        expected="check.jpg",
    ),
)
async def templated_optional_config(
    *,
    style: ConfigurationStyle,
    initial_expected_state: str | None,
    attribute: str,
    attribute_key: str,
    attribute_template: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test optional config templates."""
    await setup_entity(
        hass,
        TEST_SELECT,
        style,
        1,
        {**TEST_OPTIONS, attribute_key: attribute_template},
    )

    state = hass.states.get(TEST_SELECT.entity_id)
    expect(state.attributes.get(attribute)).to_equal(initial_expected_state)

    hass.states.async_set(TEST_STATE_ENTITY_ID, "yes")
    await hass.async_block_till_done()

    state = hass.states.get(TEST_SELECT.entity_id)

    expect(state.attributes[attribute]).to_equal(expected)


@test
async def device_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for device for select template."""
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
        domain=DOMAIN,
        options={
            "name": "My template",
            "template_type": "select",
            "state": "{{ 'on' }}",
            "options": "{{ ['off', 'on', 'auto'] }}",
            "select_option": [],
            "device_id": device_entry.id,
        },
        title="My template",
    )
    template_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(template_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    template_entity = entity_registry.async_get("select.my_template")
    expect(template_entity).not_.to_be(None)
    expect(template_entity.device_id).to_equal(device_entry.id)


@test
async def empty_action_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test configuration with empty script."""
    await setup_entity(
        hass,
        TEST_SELECT,
        ConfigurationStyle.MODERN,
        1,
        {
            "state": "{{ 'b' }}",
            "select_option": [],
            "options": "{{ ['a', 'b'] }}",
            "optimistic": True,
        },
    )

    await hass.services.async_call(
        select.DOMAIN,
        select.SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: TEST_SELECT.entity_id, "option": "a"},
        blocking=True,
    )

    state = hass.states.get(TEST_SELECT.entity_id)
    expect(state.state).to_equal("a")


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
        hass,
        TEST_SELECT,
        style,
        1,
        {"options": "{{ ['test', 'yes', 'no'] }}", "select_option": []},
    )
    state = hass.states.get(TEST_SELECT.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)

    hass.states.async_set(TEST_STATE_ENTITY_ID, "anything")
    await hass.async_block_till_done()

    await hass.services.async_call(
        select.DOMAIN,
        select.SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: TEST_SELECT.entity_id, "option": "test"},
        blocking=True,
    )
    expect(hass.states.get(TEST_SELECT.entity_id).state).to_equal("test")

    await hass.services.async_call(
        select.DOMAIN,
        select.SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: TEST_SELECT.entity_id, "option": "yes"},
        blocking=True,
    )
    expect(hass.states.get(TEST_SELECT.entity_id).state).to_equal("yes")


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
        TEST_SELECT,
        style,
        1,
        {
            "state": "{{ states('sensor.test_state') }}",
            "optimistic": False,
            "options": "{{ ['test', 'yes', 'no'] }}",
            "select_option": [],
        },
    )

    hass.states.async_set(TEST_STATE_ENTITY_ID, "anything")
    await hass.async_block_till_done()

    await hass.services.async_call(
        select.DOMAIN,
        select.SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: TEST_SELECT.entity_id, "option": "test"},
        blocking=True,
    )

    state = hass.states.get(TEST_SELECT.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def availability(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test configuration with availability template."""
    await setup_entity(
        hass,
        TEST_SELECT,
        style,
        1,
        {
            "options": "{{ ['test', 'yes', 'no'] }}",
            "select_option": [],
            "state": "{{ states('sensor.test_state') }}",
            "availability": (
                "{{ is_state('binary_sensor.test_availability', 'on') }}"
            ),
        },
    )

    hass.states.async_set(TEST_AVAILABILITY_ENTITY_ID, "on")
    hass.states.async_set(TEST_STATE_ENTITY_ID, "test")
    await hass.async_block_till_done()

    expect(hass.states.get(TEST_SELECT.entity_id).state).to_equal("test")

    hass.states.async_set(TEST_AVAILABILITY_ENTITY_ID, "off")
    await hass.async_block_till_done()
    expect(hass.states.get(TEST_SELECT.entity_id).state).to_be(STATE_UNAVAILABLE)

    hass.states.async_set(TEST_STATE_ENTITY_ID, "yes")
    await hass.async_block_till_done()
    expect(hass.states.get(TEST_SELECT.entity_id).state).to_be(STATE_UNAVAILABLE)

    hass.states.async_set(TEST_AVAILABILITY_ENTITY_ID, "on")
    await hass.async_block_till_done()
    expect(hass.states.get(TEST_SELECT.entity_id).state).to_equal("yes")


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
        TEST_SELECT,
        style,
        1,
        {"availability": "{{ x - 12 }}", **TEST_OPTIONS},
    )
    await async_trigger(hass, TEST_AVAILABILITY_ENTITY_ID, "anything")
    expect(
        hass.states.get(TEST_SELECT.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option only creates one select per id."""
    await setup_and_test_unique_id(
        hass, TEST_SELECT, style, TEST_OPTIONS_WITHOUT_STATE, "{{ 'test' }}"
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
    """Test a template unique_id propagates to select unique_ids."""
    await setup_and_test_nested_unique_id(
        hass,
        TEST_SELECT,
        style,
        entity_registry,
        TEST_OPTIONS_WITHOUT_STATE,
        "{{ 'test' }}",
    )
