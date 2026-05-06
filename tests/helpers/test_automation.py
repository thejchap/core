"""Test automation helpers."""

from typing import Any

from tryke import expect, test
import voluptuous as vol

from homeassistant.helpers.automation import (
    get_absolute_description_key,
    get_relative_description_key,
    move_options_fields_to_top_level as _move_options_fields_to_top_level,
    move_top_level_schema_fields_to_options,
)


@test.cases(
    test.case(
        "turned_on-homeassistant.turned_on",
        relative_key="turned_on",
        absolute_key="homeassistant.turned_on",
    ),
    test.case("_-homeassistant", relative_key="_", absolute_key="homeassistant"),
    test.case("_state-state", relative_key="_state", absolute_key="state"),
)
def absolute_description_key(relative_key: str, absolute_key: str) -> None:
    """Test absolute description key."""
    DOMAIN = "homeassistant"
    expect(get_absolute_description_key(DOMAIN, relative_key)).to_equal(absolute_key)


@test.cases(
    test.case(
        "turned_on-homeassistant.turned_on",
        relative_key="turned_on",
        absolute_key="homeassistant.turned_on",
    ),
    test.case("_-homeassistant", relative_key="_", absolute_key="homeassistant"),
    test.case("_state-state", relative_key="_state", absolute_key="state"),
)
def relative_description_key(relative_key: str, absolute_key: str) -> None:
    """Test relative description key."""
    DOMAIN = "homeassistant"
    expect(get_relative_description_key(DOMAIN, absolute_key)).to_equal(relative_key)


@test.cases(
    test.case(
        "config0-schema_dict0-expected_config0",
        config={
            "platform": "test",
            "entity": "sensor.test",
            "from": "open",
            "to": "closed",
            "for": {"hours": 1},
            "attribute": "state",
            "value_template": "{{ value_json.val }}",
            "extra_field": "extra_value",
        },
        schema_dict={},
        expected_config={
            "platform": "test",
            "entity": "sensor.test",
            "from": "open",
            "to": "closed",
            "for": {"hours": 1},
            "attribute": "state",
            "value_template": "{{ value_json.val }}",
            "extra_field": "extra_value",
            "options": {},
        },
    ),
    test.case(
        "config1-schema_dict1-expected_config1",
        config={
            "platform": "test",
            "entity": "sensor.test",
            "from": "open",
            "to": "closed",
            "for": {"hours": 1},
            "attribute": "state",
            "value_template": "{{ value_json.val }}",
            "extra_field": "extra_value",
        },
        schema_dict={
            vol.Required("entity"): str,
            vol.Optional("from"): str,
            vol.Optional("to"): str,
            vol.Optional("for"): dict,
            vol.Optional("attribute"): str,
            vol.Optional("value_template"): str,
        },
        expected_config={
            "platform": "test",
            "extra_field": "extra_value",
            "options": {
                "entity": "sensor.test",
                "from": "open",
                "to": "closed",
                "for": {"hours": 1},
                "attribute": "state",
                "value_template": "{{ value_json.val }}",
            },
        },
    ),
)
async def move_schema_fields_to_options(
    config: dict[str, Any],
    schema_dict: dict[Any, Any],
    expected_config: dict[str, Any],
) -> None:
    """Test moving schema fields to options."""
    expect(move_top_level_schema_fields_to_options(config, schema_dict)).to_equal(
        expected_config
    )


@test.cases(
    test.case(
        "config0-expected_config0",
        config={
            "platform": "test",
            "options": {
                "entity": "sensor.test",
                "from": "open",
                "to": "closed",
                "for": {"hours": 1},
            },
        },
        expected_config={
            "platform": "test",
            "entity": "sensor.test",
            "from": "open",
            "to": "closed",
            "for": {"hours": 1},
        },
    ),
    test.case(
        "config1-expected_config1",
        config={
            "platform": "test",
            "entity": "sensor.test",
            "from": "open",
            "to": "closed",
            "for": {"hours": 1},
        },
        expected_config={
            "platform": "test",
            "entity": "sensor.test",
            "from": "open",
            "to": "closed",
            "for": {"hours": 1},
        },
    ),
    test.case(
        "config2-expected_config2",
        config={"platform": "test", "options": 456},
        expected_config={"platform": "test", "options": 456},
    ),
    test.case(
        "config3-expected_config3",
        config={
            "platform": "test",
            "options": {"entity": "sensor.test"},
            "extra_field": "extra_value",
        },
        expected_config={
            "platform": "test",
            "options": {"entity": "sensor.test"},
            "extra_field": "extra_value",
        },
    ),
)
async def move_options_fields_to_top_level(
    config: dict[str, Any],
    expected_config: dict[str, Any],
) -> None:
    """Test moving options fields to top-level."""
    base_schema = vol.Schema({vol.Required("platform"): str})
    original_config = config.copy()
    expect(_move_options_fields_to_top_level(config, base_schema)).to_equal(
        expected_config
    )
    # Ensure original config is not modified
    expect(config).to_equal(original_config)
