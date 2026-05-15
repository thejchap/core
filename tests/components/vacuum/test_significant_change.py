"""Test the Vacuum significant change platform."""

from tryke import expect, test

from homeassistant.components.vacuum import (
    ATTR_BATTERY_ICON,
    ATTR_BATTERY_LEVEL,
    ATTR_FAN_SPEED,
)
from homeassistant.components.vacuum.significant_change import (
    async_check_significant_change,
)


@test
async def significant_state_change() -> None:
    """Detect Vacuum significant state changes."""
    attrs: dict = {}
    expect(
        async_check_significant_change(None, "on", attrs, "on", attrs)
    ).to_be_falsy()
    expect(
        async_check_significant_change(None, "on", attrs, "off", attrs)
    ).to_be_truthy()


@test.cases(
    test.case(
        "fan_speed_same",
        old_attrs={ATTR_FAN_SPEED: "old_value"},
        new_attrs={ATTR_FAN_SPEED: "old_value"},
        expected_result=False,
    ),
    test.case(
        "fan_speed_diff",
        old_attrs={ATTR_FAN_SPEED: "old_value"},
        new_attrs={ATTR_FAN_SPEED: "new_value"},
        expected_result=True,
    ),
    test.case(
        "multiple_attrs",
        old_attrs={ATTR_FAN_SPEED: "old_value", ATTR_BATTERY_LEVEL: 10.0},
        new_attrs={ATTR_FAN_SPEED: "new_value", ATTR_BATTERY_LEVEL: 10.0},
        expected_result=True,
    ),
    test.case(
        "battery_level_int_diff",
        old_attrs={ATTR_BATTERY_LEVEL: 10.0},
        new_attrs={ATTR_BATTERY_LEVEL: 11.0},
        expected_result=True,
    ),
    test.case(
        "battery_level_small_diff",
        old_attrs={ATTR_BATTERY_LEVEL: 10.0},
        new_attrs={ATTR_BATTERY_LEVEL: 10.9},
        expected_result=False,
    ),
    test.case(
        "battery_level_invalid_to_float",
        old_attrs={ATTR_BATTERY_LEVEL: "invalid"},
        new_attrs={ATTR_BATTERY_LEVEL: 10.0},
        expected_result=True,
    ),
    test.case(
        "battery_level_float_to_invalid",
        old_attrs={ATTR_BATTERY_LEVEL: 10.0},
        new_attrs={ATTR_BATTERY_LEVEL: "invalid"},
        expected_result=False,
    ),
    test.case(
        "battery_icon_diff_insignificant",
        old_attrs={ATTR_BATTERY_ICON: "old_value"},
        new_attrs={ATTR_BATTERY_ICON: "new_value"},
        expected_result=False,
    ),
    test.case(
        "battery_icon_same",
        old_attrs={ATTR_BATTERY_ICON: "old_value"},
        new_attrs={ATTR_BATTERY_ICON: "old_value"},
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
    """Detect Vacuum significant attribute changes."""
    expect(
        async_check_significant_change(None, "state", old_attrs, "state", new_attrs)
    ).to_equal(expected_result)
