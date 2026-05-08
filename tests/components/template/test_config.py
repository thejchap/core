"""Test Template config."""

from __future__ import annotations

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.template.config import CONFIG_SECTION_SCHEMA
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test.cases(
    test.case(
        "trigger_button_root_action_disallowed",
        config={
            "trigger": {"trigger": "event", "event_type": "my_event"},
            "button": {
                "press": {
                    "service": "test.automation",
                    "data_template": {"caller": "{{ this.entity_id }}"},
                },
                "device_class": "restart",
                "unique_id": "test",
                "name": "test",
                "icon": "mdi:test",
            },
        },
    ),
    test.case(
        "root_action_disallowed",
        config={
            "trigger": {"trigger": "event", "event_type": "my_event"},
            "action": {
                "service": "test.automation",
                "data_template": {"caller": "{{ this.entity_id }}"},
            },
            "button": {
                "press": {
                    "service": "test.automation",
                    "data_template": {"caller": "{{ this.entity_id }}"},
                },
                "device_class": "restart",
                "unique_id": "test",
                "name": "test",
                "icon": "mdi:test",
            },
        },
    ),
)
async def invalid_schema(
    *,
    config: dict,
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test invalid config schemas."""
    raised = False
    try:
        CONFIG_SECTION_SCHEMA(config)
    except vol.Invalid:
        raised = True
    expect(raised).to_be(True)


@test
async def valid_default_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test valid default_entity_id schemas."""
    config = {
        "button": {
            "press": [],
            "default_entity_id": "button.test",
        },
    }
    expect(CONFIG_SECTION_SCHEMA(config)).to_equal(
        {
            "button": [
                {
                    "press": [],
                    "name": Template("Template Button", hass),
                    "default_entity_id": "button.test",
                }
            ]
        }
    )


@test.cases(
    test.case("foo", default_entity_id="foo"),
    test.case("template_value", default_entity_id="{{ 'my_template' }}"),
    test.case("garbage", default_entity_id="SJLIVan as dfkaj;heafha faass00"),
    test.case("number", default_entity_id=48),
    test.case("none", default_entity_id=None),
    test.case("bttn_test", default_entity_id="bttn.test"),
)
async def invalid_default_entity_id(
    *,
    default_entity_id,
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test invalid default_entity_id schemas."""
    config = {
        "button": {
            "press": [],
            "default_entity_id": default_entity_id,
        },
    }
    raised = False
    try:
        CONFIG_SECTION_SCHEMA(config)
    except vol.Invalid:
        raised = True
    expect(raised).to_be(True)


@test.skip("auto_off binary sensor schema needs caplog text — port deferred")
async def invalid_binary_sensor_schema_with_auto_off() -> None:
    """Stub: parametrize-heavy test, port deferred."""


@test.skip("combined_state_variables uses async_validate_config_section — port deferred")
async def combined_state_variables() -> None:
    """Stub."""


@test.skip("combined_trigger_variables uses async_validate_config_section — port deferred")
async def combined_trigger_variables() -> None:
    """Stub."""


@test.skip("state_init_attribute_variables — port deferred")
async def state_init_attribute_variables() -> None:
    """Stub."""


@test.skip("invalid_schema_raises_issue — port deferred")
async def invalid_schema_raises_issue() -> None:
    """Stub."""


@test.skip("multiple_configuration_keys — port deferred")
async def multiple_configuration_keys() -> None:
    """Stub."""
