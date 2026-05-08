"""The tests for the Template button platform."""

from __future__ import annotations

import datetime as dt
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.template import DOMAIN
from homeassistant.components.template.const import CONF_PICTURE
from homeassistant.const import (
    ATTR_ENTITY_PICTURE,
    ATTR_ICON,
    CONF_DEVICE_CLASS,
    CONF_ENTITY_ID,
    CONF_FRIENDLY_NAME,
    CONF_ICON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    assert_action,
    async_trigger,
    make_test_action,
    mock_calls,
    setup_and_test_nested_unique_id,
    setup_and_test_unique_id,
    setup_entity,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

TEST_ATTRIBUTE_ENTITY_ID = "sensor.test_attribute"
TEST_AVAILABILITY_ENTITY = "binary_sensor.availability"
TEST_BUTTON = TemplatePlatformSetup(BUTTON_DOMAIN, None, "template_button", {})
PRESS_ACTION = make_test_action("press")


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


def _verify(
    hass: HomeAssistant,
    expected_value: str,
    attributes: dict[str, Any] | None = None,
    entity_id: str = TEST_BUTTON.entity_id,
) -> None:
    """Verify button's state."""
    attributes = attributes or {}
    if CONF_FRIENDLY_NAME not in attributes:
        attributes[CONF_FRIENDLY_NAME] = TEST_BUTTON.object_id
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == expected_value
    assert state.attributes == attributes


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test
async def missing_optional_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: missing optional template is ok."""
    await setup_entity(
        hass, TEST_BUTTON, ConfigurationStyle.MODERN, 1, PRESS_ACTION
    )
    _verify(hass, STATE_UNKNOWN)


@test
async def missing_emtpy_press_action_config(
    hass: HomeAssistant = Depends(_trigger_executor),
    freezer: Any = Depends(freezer_fixture),
) -> None:
    """Test: missing optional template is ok."""
    await setup_entity(
        hass, TEST_BUTTON, ConfigurationStyle.MODERN, 1, {"press": []}
    )
    _verify(hass, STATE_UNKNOWN)

    now = dt.datetime.now(dt.UTC)
    freezer.move_to(now)
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {CONF_ENTITY_ID: TEST_BUTTON.entity_id},
        blocking=True,
    )

    _verify(hass, now.isoformat())


@test
async def missing_required_keys(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: missing required fields will fail."""
    await setup_entity(hass, TEST_BUTTON, ConfigurationStyle.MODERN, 0, {})
    expect(hass.states.async_all("button")).to_equal([])


@test
async def device_class_option(
    hass: HomeAssistant = Depends(_trigger_executor),
    freezer: Any = Depends(freezer_fixture),
) -> None:
    """Test optional options is ok."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_BUTTON,
        ConfigurationStyle.MODERN,
        1,
        {**PRESS_ACTION, "device_class": "restart"},
    )
    _verify(
        hass,
        STATE_UNKNOWN,
        {
            CONF_DEVICE_CLASS: "restart",
            CONF_FRIENDLY_NAME: TEST_BUTTON.object_id,
        },
        TEST_BUTTON.entity_id,
    )

    now = dt.datetime.now(dt.UTC)
    freezer.move_to(now)
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {CONF_ENTITY_ID: TEST_BUTTON.entity_id},
        blocking=True,
    )

    assert_action(TEST_BUTTON, calls, 1, "press")
    _verify(
        hass,
        now.isoformat(),
        {
            CONF_DEVICE_CLASS: "restart",
            CONF_FRIENDLY_NAME: TEST_BUTTON.object_id,
        },
        TEST_BUTTON.entity_id,
    )


@test.cases(
    test.case(
        "icon",
        attribute=CONF_ICON,
        attribute_template=(
            "{{ 'mdi:test' if is_state('sensor.test_attribute', 'on') else '' }}"
        ),
        attribute_name=ATTR_ICON,
        expected="mdi:test",
    ),
    test.case(
        "picture",
        attribute=CONF_PICTURE,
        attribute_template=(
            "{{ 'test.jpg' if is_state('sensor.test_attribute', 'on') else '' }}"
        ),
        attribute_name=ATTR_ENTITY_PICTURE,
        expected="test.jpg",
    ),
)
async def options_that_are_templates(
    *,
    attribute: str,
    attribute_template: str,
    attribute_name: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    freezer: Any = Depends(freezer_fixture),
) -> None:
    """Test button options that are templates."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_BUTTON,
        ConfigurationStyle.MODERN,
        1,
        PRESS_ACTION,
        extra_config={attribute: attribute_template},
    )
    expected_attributes = {attribute_name: expected}

    _verify(hass, STATE_UNKNOWN, {attribute_name: ""})
    await async_trigger(hass, TEST_ATTRIBUTE_ENTITY_ID, STATE_ON)

    _verify(hass, STATE_UNKNOWN, expected_attributes)

    now = dt.datetime.now(dt.UTC)
    freezer.move_to(now)
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {CONF_ENTITY_ID: TEST_BUTTON.entity_id},
        blocking=True,
    )

    assert_action(TEST_BUTTON, calls, 1, "press")
    _verify(hass, now.isoformat(), expected_attributes)


@test
async def name_template(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: name template."""
    await setup_entity(
        hass,
        TEST_BUTTON,
        ConfigurationStyle.MODERN,
        1,
        PRESS_ACTION,
        extra_config={"name": "Button {{ 1 + 1 }}"},
    )
    _verify(
        hass,
        STATE_UNKNOWN,
        {CONF_FRIENDLY_NAME: "Button 2"},
        "button.button_2",
    )


@test
async def unique_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option only creates one button per id."""
    await setup_and_test_unique_id(
        hass, TEST_BUTTON, ConfigurationStyle.MODERN, PRESS_ACTION
    )


@test
async def nested_unique_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test a template unique_id propagates to button unique_ids."""
    await setup_and_test_nested_unique_id(
        hass,
        TEST_BUTTON,
        ConfigurationStyle.MODERN,
        entity_registry,
        PRESS_ACTION,
    )


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
    expect(device_entry.id).not_.to_be(None)

    template_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My template",
            "template_type": "button",
            "device_id": device_entry.id,
            "press": [
                {
                    "service": "input_boolean.toggle",
                    "metadata": {},
                    "data": {},
                    "target": {"entity_id": "input_boolean.test"},
                }
            ],
        },
        title="My template",
    )
    template_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(template_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    template_entity = entity_registry.async_get("button.my_template")
    expect(template_entity).not_.to_be(None)
    expect(template_entity.device_id).to_equal(device_entry.id)


@test
async def available_template_with_entities(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test availability templates with values from other entities."""
    await setup_entity(
        hass,
        TEST_BUTTON,
        ConfigurationStyle.MODERN,
        1,
        PRESS_ACTION,
        extra_config={
            "availability": "{{ is_state('binary_sensor.availability', 'on') }}",
        },
    )
    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, STATE_ON)

    state = hass.states.get(TEST_BUTTON.entity_id)
    expect(state.state != STATE_UNAVAILABLE).to_be(True)

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY, STATE_OFF)

    expect(hass.states.get(TEST_BUTTON.entity_id).state).to_be(STATE_UNAVAILABLE)


@test
async def invalid_availability_template_keeps_component_available(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that an invalid availability keeps the device available."""
    await setup_entity(
        hass,
        TEST_BUTTON,
        ConfigurationStyle.MODERN,
        1,
        PRESS_ACTION,
        extra_config={"availability": "{{ x - 12 }}"},
    )
    expect(
        hass.states.get(TEST_BUTTON.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)
