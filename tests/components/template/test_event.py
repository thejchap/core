"""The tests for the Template event platform."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import event
from homeassistant.components.template import DOMAIN as TEMPLATE_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_PICTURE,
    ATTR_ICON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    async_trigger,
    make_test_trigger,
    setup_and_test_nested_unique_id,
    setup_and_test_unique_id,
    setup_entity,
)

from tests.common import MockConfigEntry, assert_setup_component
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

TEST_STATE_ENTITY_ID = "sensor.test_state"
TEST_EVENT = TemplatePlatformSetup(
    event.DOMAIN,
    None,
    "template_event",
    make_test_trigger(TEST_STATE_ENTITY_ID),
)

TEST_EVENT_TYPES_TEMPLATE = "{{ ['single', 'double', 'hold'] }}"
TEST_EVENT_TYPE_TEMPLATE = "{{ 'single' }}"

TEST_EVENT_CONFIG = {
    "event_types": TEST_EVENT_TYPES_TEMPLATE,
    "event_type": TEST_EVENT_TYPE_TEMPLATE,
}
TEST_FROZEN_INPUT = "2024-07-09 00:00:00+00:00"
TEST_FROZEN_STATE = "2024-07-09T00:00:00.000+00:00"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test
async def legacy_platform_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a legacy platform does not create event entities."""
    with assert_setup_component(1, event.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                event.DOMAIN,
                {
                    "event": {
                        "platform": "template",
                        "events": {TEST_EVENT.object_id: {}},
                    }
                },
            )
        ).to_be(True)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()
    expect(hass.states.async_all("event")).to_equal([])


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test
async def device_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _freezer: Any = Depends(freezer_fixture),
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
        domain=TEMPLATE_DOMAIN,
        options={
            "name": "My template",
            "event_type": TEST_EVENT_TYPE_TEMPLATE,
            "event_types": TEST_EVENT_TYPES_TEMPLATE,
            "template_type": "event",
            "device_id": device_entry.id,
        },
        title="My template",
    )
    template_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(template_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    template_entity = entity_registry.async_get("event.my_template")
    expect(template_entity).not_.to_be(None)
    expect(template_entity.device_id).to_equal(device_entry.id)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def event_type_syntax_error(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template event_type with render error."""
    await setup_entity(
        hass,
        TEST_EVENT,
        style,
        1,
        {
            "event_type": "{{states.test['big.fat...']}}",
            "event_types": TEST_EVENT_TYPES_TEMPLATE,
        },
    )

    state = hass.states.get(TEST_EVENT.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)


@test.cases(
    test.case("modern_single", style=ConfigurationStyle.MODERN, source="single"),
    test.case("modern_double", style=ConfigurationStyle.MODERN, source="double"),
    test.case("modern_hold", style=ConfigurationStyle.MODERN, source="hold"),
    test.case("trigger_single", style=ConfigurationStyle.TRIGGER, source="single"),
    test.case("trigger_double", style=ConfigurationStyle.TRIGGER, source="double"),
    test.case("trigger_hold", style=ConfigurationStyle.TRIGGER, source="hold"),
)
async def event_type_template(
    *,
    style: ConfigurationStyle,
    source: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template event_type."""
    await setup_entity(
        hass,
        TEST_EVENT,
        style,
        1,
        {
            "event_type": "{{ states('sensor.test_state') }}",
            "event_types": TEST_EVENT_TYPES_TEMPLATE,
        },
    )

    await async_trigger(hass, TEST_STATE_ENTITY_ID, source)

    state = hass.states.get(TEST_EVENT.entity_id)
    expect(state.attributes["event_type"]).to_equal(source)


@test.cases(
    test.case("modern_none", style=ConfigurationStyle.MODERN, tpl="{{ None }}"),
    test.case("modern_seven", style=ConfigurationStyle.MODERN, tpl="{{ 7 }}"),
    test.case("modern_unknown", style=ConfigurationStyle.MODERN, tpl="{{ 'unknown' }}"),
    test.case(
        "modern_tripple_double",
        style=ConfigurationStyle.MODERN,
        tpl="{{ 'tripple_double' }}",
    ),
    test.case("trigger_none", style=ConfigurationStyle.TRIGGER, tpl="{{ None }}"),
    test.case("trigger_seven", style=ConfigurationStyle.TRIGGER, tpl="{{ 7 }}"),
    test.case(
        "trigger_unknown", style=ConfigurationStyle.TRIGGER, tpl="{{ 'unknown' }}"
    ),
    test.case(
        "trigger_tripple_double",
        style=ConfigurationStyle.TRIGGER,
        tpl="{{ 'tripple_double' }}",
    ),
)
async def event_type_invalid(
    *,
    style: ConfigurationStyle,
    tpl: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template event_type with invalid values."""
    await setup_entity(
        hass,
        TEST_EVENT,
        style,
        1,
        {"event_type": tpl, "event_types": TEST_EVENT_TYPES_TEMPLATE},
    )

    state = hass.states.get(TEST_EVENT.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)
    expect(state.attributes["event_type"]).to_be(None)


@test.cases(
    test.case(
        "modern_picture",
        style=ConfigurationStyle.MODERN,
        attribute="picture",
        attribute_template=(
            "{% if is_state('sensor.test_state', 'double') %}something{% endif %}"
        ),
        key=ATTR_ENTITY_PICTURE,
        expected="something",
    ),
    test.case(
        "modern_icon",
        style=ConfigurationStyle.MODERN,
        attribute="icon",
        attribute_template=(
            "{% if is_state('sensor.test_state', 'double') %}mdi:something{% endif %}"
        ),
        key=ATTR_ICON,
        expected="mdi:something",
    ),
    test.case(
        "trigger_picture",
        style=ConfigurationStyle.TRIGGER,
        attribute="picture",
        attribute_template=(
            "{% if is_state('sensor.test_state', 'double') %}something{% endif %}"
        ),
        key=ATTR_ENTITY_PICTURE,
        expected="something",
    ),
    test.case(
        "trigger_icon",
        style=ConfigurationStyle.TRIGGER,
        attribute="icon",
        attribute_template=(
            "{% if is_state('sensor.test_state', 'double') %}mdi:something{% endif %}"
        ),
        key=ATTR_ICON,
        expected="mdi:something",
    ),
)
async def entity_picture_and_icon_templates(
    *,
    style: ConfigurationStyle,
    attribute: str,
    attribute_template: str,
    key: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test picture and icon template."""
    await setup_entity(
        hass,
        TEST_EVENT,
        style,
        1,
        {
            "event_type": "{{ states('sensor.test_state') }}",
            "event_types": TEST_EVENT_TYPES_TEMPLATE,
        },
        extra_config={attribute: attribute_template},
    )

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "single")

    state = hass.states.get(TEST_EVENT.entity_id)
    expect(state.attributes.get(key) in ("", None)).to_be(True)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "double")

    state = hass.states.get(TEST_EVENT.entity_id)
    expect(state.attributes[key]).to_equal(expected)


@test.cases(
    test.case(
        "modern_full",
        style=ConfigurationStyle.MODERN,
        types_template=(
            "{{ ['Strobe color', 'Police', 'Christmas', 'RGB', 'Random Loop'] }}"
        ),
        expected=["Strobe color", "Police", "Christmas", "RGB", "Random Loop"],
    ),
    test.case(
        "modern_partial",
        style=ConfigurationStyle.MODERN,
        types_template="{{ ['Police', 'RGB', 'Random Loop'] }}",
        expected=["Police", "RGB", "Random Loop"],
    ),
    test.case(
        "modern_empty_list",
        style=ConfigurationStyle.MODERN,
        types_template="{{ [] }}",
        expected=[],
    ),
    test.case(
        "modern_empty_string_list",
        style=ConfigurationStyle.MODERN,
        types_template="{{ '[]' }}",
        expected=[],
    ),
    test.case(
        "modern_int",
        style=ConfigurationStyle.MODERN,
        types_template="{{ 124 }}",
        expected=[],
    ),
    test.case(
        "modern_int_str",
        style=ConfigurationStyle.MODERN,
        types_template="{{ '124' }}",
        expected=[],
    ),
    test.case(
        "modern_none",
        style=ConfigurationStyle.MODERN,
        types_template="{{ none }}",
        expected=[],
    ),
    test.case(
        "modern_empty",
        style=ConfigurationStyle.MODERN,
        types_template="",
        expected=[],
    ),
    test.case(
        "trigger_full",
        style=ConfigurationStyle.TRIGGER,
        types_template=(
            "{{ ['Strobe color', 'Police', 'Christmas', 'RGB', 'Random Loop'] }}"
        ),
        expected=["Strobe color", "Police", "Christmas", "RGB", "Random Loop"],
    ),
    test.case(
        "trigger_partial",
        style=ConfigurationStyle.TRIGGER,
        types_template="{{ ['Police', 'RGB', 'Random Loop'] }}",
        expected=["Police", "RGB", "Random Loop"],
    ),
)
async def event_types_template(
    *,
    style: ConfigurationStyle,
    types_template: str,
    expected: list[str],
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template event_types."""
    await setup_entity(
        hass,
        TEST_EVENT,
        style,
        1,
        {"event_type": "{{ None }}", "event_types": types_template},
    )

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")

    state = hass.states.get(TEST_EVENT.entity_id)
    expect(state.attributes["event_types"]).to_equal(expected)


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
        TEST_EVENT,
        style,
        1,
        {
            "event_type": "{{ states('sensor.test_state') }}",
            "event_types": TEST_EVENT_TYPES_TEMPLATE,
        },
        extra_config={
            "availability": (
                "{{ states('sensor.test_state') in ['single', 'double', 'hold'] }}"
            ),
        },
    )

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "single")

    state = hass.states.get(TEST_EVENT.entity_id)
    expect(state.state != STATE_UNAVAILABLE).to_be(True)
    expect(state.attributes["event_type"]).to_equal("single")

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "triple")

    state = hass.states.get(TEST_EVENT.entity_id)
    expect(state.state).to_be(STATE_UNAVAILABLE)
    expect("event_type" in state.attributes).to_be(False)


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
        TEST_EVENT,
        style,
        1,
        {
            "event_type": TEST_EVENT_TYPE_TEMPLATE,
            "event_types": TEST_EVENT_TYPES_TEMPLATE,
        },
        extra_config={"availability": "{{ x - 12 }}"},
    )

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")

    expect(
        hass.states.get(TEST_EVENT.entity_id).state != STATE_UNAVAILABLE
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
    """Test unique_id option only creates one event per id."""
    await setup_and_test_unique_id(hass, TEST_EVENT, style, TEST_EVENT_CONFIG)


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
    """Test a template unique_id propagates to event unique_ids."""
    await setup_and_test_nested_unique_id(
        hass, TEST_EVENT, style, entity_registry, TEST_EVENT_CONFIG
    )


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator + freeze_time interplay."""


@test.skip("requires mock_restore_cache_with_extra_data — port deferred")
async def trigger_entity_restore_state() -> None:
    """Stub: needs restore-cache scaffolding for trigger entities."""


@test.skip("requires mock_restore_cache_with_extra_data — port deferred")
async def event_entity_restore_state() -> None:
    """Stub: needs restore-cache scaffolding for non-trigger entities."""


@test.skip("event type updates require freeze_time interplay — port deferred")
async def event_type_template_updates() -> None:
    """Stub: depends on @pytest.mark.freeze_time + setup ordering."""


@test.skip("event types updates require freeze_time interplay — port deferred")
async def event_types_template_updates() -> None:
    """Stub: depends on @pytest.mark.freeze_time + setup ordering."""
