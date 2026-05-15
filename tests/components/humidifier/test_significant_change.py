"""Test the Humidifier significant change platform."""

from tryke import expect, test

from homeassistant.components.humidifier import (
    ATTR_ACTION,
    ATTR_CURRENT_HUMIDITY,
    ATTR_HUMIDITY,
    ATTR_MODE,
)
from homeassistant.components.humidifier.significant_change import (
    async_check_significant_change,
)


@test
async def significant_state_change() -> None:
    """Detect Humidifier significant state changes."""
    attrs: dict = {}
    expect(
        async_check_significant_change(None, "on", attrs, "on", attrs)
    ).to_be_falsy()
    expect(
        async_check_significant_change(None, "on", attrs, "off", attrs)
    ).to_be_truthy()


@test.cases(
    test.case(
        "action_same",
        old_attrs={ATTR_ACTION: "old_value"},
        new_attrs={ATTR_ACTION: "old_value"},
        expected_result=False,
    ),
    test.case(
        "action_diff",
        old_attrs={ATTR_ACTION: "old_value"},
        new_attrs={ATTR_ACTION: "new_value"},
        expected_result=True,
    ),
    test.case(
        "mode_diff",
        old_attrs={ATTR_MODE: "old_value"},
        new_attrs={ATTR_MODE: "new_value"},
        expected_result=True,
    ),
    test.case(
        "multiple_attrs",
        old_attrs={ATTR_ACTION: "old_value", ATTR_MODE: "old_value"},
        new_attrs={ATTR_ACTION: "new_value", ATTR_MODE: "old_value"},
        expected_result=True,
    ),
    test.case(
        "current_humidity_int_diff",
        old_attrs={ATTR_CURRENT_HUMIDITY: 60.0},
        new_attrs={ATTR_CURRENT_HUMIDITY: 61},
        expected_result=True,
    ),
    test.case(
        "current_humidity_small_diff",
        old_attrs={ATTR_CURRENT_HUMIDITY: 60.0},
        new_attrs={ATTR_CURRENT_HUMIDITY: 60.9},
        expected_result=False,
    ),
    test.case(
        "current_humidity_invalid_to_float",
        old_attrs={ATTR_CURRENT_HUMIDITY: "invalid"},
        new_attrs={ATTR_CURRENT_HUMIDITY: 60.0},
        expected_result=True,
    ),
    test.case(
        "current_humidity_float_to_invalid",
        old_attrs={ATTR_CURRENT_HUMIDITY: 60.0},
        new_attrs={ATTR_CURRENT_HUMIDITY: "invalid"},
        expected_result=False,
    ),
    test.case(
        "humidity_diff",
        old_attrs={ATTR_HUMIDITY: 62.0},
        new_attrs={ATTR_HUMIDITY: 63.0},
        expected_result=True,
    ),
    test.case(
        "humidity_small_diff",
        old_attrs={ATTR_HUMIDITY: 62.0},
        new_attrs={ATTR_HUMIDITY: 62.9},
        expected_result=False,
    ),
    test.case(
        "unknown_attr_same",
        old_attrs={"unknown_attr": "old_value"},
        new_attrs={"unknown_attr": "old_value"},
        expected_result=False,
    ),
    test.case(
        "unknown_attr_diff",
        old_attrs={"unknown_attr": "old_value"},
        new_attrs={"unknown_attr": "new_value"},
        expected_result=False,
    ),
)
async def significant_attributes_change(
    *, old_attrs: dict, new_attrs: dict, expected_result: bool
) -> None:
    """Detect Humidifier significant attribute changes."""
    expect(
        async_check_significant_change(None, "state", old_attrs, "state", new_attrs)
    ).to_equal(expected_result)
