"""Test the Z-Wave JS config validation helpers."""

from typing import Any

import voluptuous as vol
from tryke import expect, test

from homeassistant.components.zwave_js.config_validation import VALUE_SCHEMA, boolean


@test.cases(
    test.case("truthy", test_cases=[True, "true", "yes", "on", "ON", "enable"], expected_value=True),
    test.case("falsy", test_cases=[False, "false", "no", "off", "NO", "disable"], expected_value=False),
    test.case("float_1_1", test_cases=[1.1, "1.1"], expected_value=1.1),
    test.case("float_1_0", test_cases=[1.0, "1.0"], expected_value=1.0),
    test.case("int_1", test_cases=[1, "1"], expected_value=1),
)
def validation(*, test_cases: list[Any], expected_value: Any) -> None:
    """Test config validation."""
    for case in test_cases:
        expect(VALUE_SCHEMA(case)).to_equal(expected_value)


@test.cases(
    test.case("invalid_string", value="invalid"),
    test.case("string_one", value="1"),
    test.case("string_zero", value="0"),
    test.case("int_one", value=1),
    test.case("int_zero", value=0),
)
def invalid_boolean_validation(*, value: str | int) -> None:
    """Test invalid cases for boolean config validator."""
    expect(lambda: boolean(value)).to_raise(vol.Invalid)
