"""Test the Alarm Control Panel significant change platform."""

from tryke import expect, test

from homeassistant.components.alarm_control_panel import (
    ATTR_CHANGED_BY,
    ATTR_CODE_ARM_REQUIRED,
    ATTR_CODE_FORMAT,
)
from homeassistant.components.alarm_control_panel.significant_change import (
    async_check_significant_change,
)


@test
async def significant_state_change() -> None:
    """Detect Alarm Control Panel significant state changes."""
    attrs: dict = {}
    expect(
        async_check_significant_change(None, "on", attrs, "on", attrs)
    ).to_be_falsy()
    expect(
        async_check_significant_change(None, "on", attrs, "off", attrs)
    ).to_be_truthy()


@test.cases(
    test.case(
        "changed_by_same",
        old_attrs={ATTR_CHANGED_BY: "old_value"},
        new_attrs={ATTR_CHANGED_BY: "old_value"},
        expected_result=False,
    ),
    test.case(
        "changed_by_diff",
        old_attrs={ATTR_CHANGED_BY: "old_value"},
        new_attrs={ATTR_CHANGED_BY: "new_value"},
        expected_result=True,
    ),
    test.case(
        "code_arm_required_diff",
        old_attrs={ATTR_CODE_ARM_REQUIRED: "old_value"},
        new_attrs={ATTR_CODE_ARM_REQUIRED: "new_value"},
        expected_result=True,
    ),
    test.case(
        "multiple_attrs",
        old_attrs={ATTR_CHANGED_BY: "old_value", ATTR_CODE_ARM_REQUIRED: "old_value"},
        new_attrs={ATTR_CHANGED_BY: "new_value", ATTR_CODE_ARM_REQUIRED: "old_value"},
        expected_result=True,
    ),
    test.case(
        "code_format_same",
        old_attrs={ATTR_CODE_FORMAT: "old_value"},
        new_attrs={ATTR_CODE_FORMAT: "old_value"},
        expected_result=False,
    ),
    test.case(
        "code_format_diff_insignificant",
        old_attrs={ATTR_CODE_FORMAT: "old_value"},
        new_attrs={ATTR_CODE_FORMAT: "new_value"},
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
    """Detect Alarm Control Panel significant attribute changes."""
    expect(
        async_check_significant_change(None, "state", old_attrs, "state", new_attrs)
    ).to_equal(expected_result)
