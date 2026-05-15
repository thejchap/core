"""Test the Cover significant change platform."""

from typing import Any

from tryke import expect, test

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
)
from homeassistant.components.cover.significant_change import (
    async_check_significant_change,
)


@test
async def significant_state_change() -> None:
    """Detect Cover significant state changes."""
    attrs: dict[str, Any] = {}
    expect(async_check_significant_change(None, "on", attrs, "on", attrs)).to_be(False)
    expect(async_check_significant_change(None, "on", attrs, "off", attrs)).to_be(True)


@test.cases(
    test.case(
        "pos_60_to_61",
        old_attrs={ATTR_CURRENT_POSITION: 60.0},
        new_attrs={ATTR_CURRENT_POSITION: 61.0},
        expected_result=True,
    ),
    test.case(
        "pos_60_to_60.9",
        old_attrs={ATTR_CURRENT_POSITION: 60.0},
        new_attrs={ATTR_CURRENT_POSITION: 60.9},
        expected_result=False,
    ),
    test.case(
        "pos_invalid_to_60",
        old_attrs={ATTR_CURRENT_POSITION: "invalid"},
        new_attrs={ATTR_CURRENT_POSITION: 60.0},
        expected_result=True,
    ),
    test.case(
        "pos_60_to_invalid",
        old_attrs={ATTR_CURRENT_POSITION: 60.0},
        new_attrs={ATTR_CURRENT_POSITION: "invalid"},
        expected_result=False,
    ),
    test.case(
        "tilt_60_to_61",
        old_attrs={ATTR_CURRENT_TILT_POSITION: 60.0},
        new_attrs={ATTR_CURRENT_TILT_POSITION: 61.0},
        expected_result=True,
    ),
    test.case(
        "tilt_60_to_60.9",
        old_attrs={ATTR_CURRENT_TILT_POSITION: 60.0},
        new_attrs={ATTR_CURRENT_TILT_POSITION: 60.9},
        expected_result=False,
    ),
    test.case(
        "multi_tilt_change",
        old_attrs={ATTR_CURRENT_POSITION: 60, ATTR_CURRENT_TILT_POSITION: 60},
        new_attrs={ATTR_CURRENT_POSITION: 60, ATTR_CURRENT_TILT_POSITION: 61},
        expected_result=True,
    ),
    test.case(
        "multi_tilt_fraction",
        old_attrs={ATTR_CURRENT_POSITION: 60, ATTR_CURRENT_TILT_POSITION: 59.1},
        new_attrs={ATTR_CURRENT_POSITION: 60, ATTR_CURRENT_TILT_POSITION: 60.9},
        expected_result=True,
    ),
    test.case(
        "unknown_attr_same",
        old_attrs={"unknown_attr": "old_value"},
        new_attrs={"unknown_attr": "old_value"},
        expected_result=False,
    ),
    test.case(
        "unknown_attr_change",
        old_attrs={"unknown_attr": "old_value"},
        new_attrs={"unknown_attr": "new_value"},
        expected_result=False,
    ),
)
async def significant_atributes_change(
    old_attrs: dict[str, Any],
    new_attrs: dict[str, Any],
    expected_result: bool,
) -> None:
    """Detect Cover significant attribute changes."""
    expect(
        async_check_significant_change(None, "state", old_attrs, "state", new_attrs)
    ).to_equal(expected_result)
