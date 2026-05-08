"""Tests for ZHA helpers."""

from typing import Any

from tryke import expect, test

from homeassistant.components.zha.helpers import exclude_none_values


@test.cases(
    test.case(
        "drop_none",
        obj={"a": 1, "b": 2, "c": None},
        expected_output={"a": 1, "b": 2},
    ),
    test.case(
        "keep_zero",
        obj={"a": 1, "b": 2, "c": 0},
        expected_output={"a": 1, "b": 2, "c": 0},
    ),
    test.case(
        "keep_empty_string",
        obj={"a": 1, "b": 2, "c": ""},
        expected_output={"a": 1, "b": 2, "c": ""},
    ),
    test.case(
        "keep_false",
        obj={"a": 1, "b": 2, "c": False},
        expected_output={"a": 1, "b": 2, "c": False},
    ),
)
def exclude_none_values_helper(
    *, obj: dict[str, Any], expected_output: dict[str, Any]
) -> None:
    """Test exclude_none_values helper."""
    result = exclude_none_values(obj)
    expect(result).to_equal(expected_output)

    for key, value in expected_output.items():
        expect(value).to_equal(obj[key])


@test.skip("zha: requires zigpy ControllerApplication / mock_zigpy_connect")
async def zcl_schema_conversions() -> None:
    """Stub for test_zcl_schema_conversions."""


@test.skip("zha: requires zigpy ControllerApplication / mock_zigpy_connect")
async def create_zha_config_remove_unused() -> None:
    """Stub for test_create_zha_config_remove_unused."""
