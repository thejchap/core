"""Test the Fan significant change platform."""

from typing import Any

from tryke import expect, test

from homeassistant.components.fan import (
    ATTR_DIRECTION,
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    ATTR_PERCENTAGE_STEP,
    ATTR_PRESET_MODE,
)
from homeassistant.components.fan.significant_change import (
    async_check_significant_change,
)


@test
async def significant_state_change() -> None:
    """Detect Fan significant state changes."""
    attrs: dict[str, Any] = {}
    expect(async_check_significant_change(None, "on", attrs, "on", attrs)).to_be(False)
    expect(async_check_significant_change(None, "on", attrs, "off", attrs)).to_be(True)


@test.cases(
    test.case(
        "step_change",
        old_attrs={ATTR_PERCENTAGE_STEP: "1"},
        new_attrs={ATTR_PERCENTAGE_STEP: "2"},
        expected_result=False,
    ),
    test.case(
        "pct_1_to_2",
        old_attrs={ATTR_PERCENTAGE: 1},
        new_attrs={ATTR_PERCENTAGE: 2},
        expected_result=True,
    ),
    test.case(
        "pct_1_to_1.9",
        old_attrs={ATTR_PERCENTAGE: 1},
        new_attrs={ATTR_PERCENTAGE: 1.9},
        expected_result=False,
    ),
    test.case(
        "pct_invalid_to_1",
        old_attrs={ATTR_PERCENTAGE: "invalid"},
        new_attrs={ATTR_PERCENTAGE: 1},
        expected_result=True,
    ),
    test.case(
        "pct_1_to_invalid",
        old_attrs={ATTR_PERCENTAGE: 1},
        new_attrs={ATTR_PERCENTAGE: "invalid"},
        expected_result=False,
    ),
    test.case(
        "direction_same",
        old_attrs={ATTR_DIRECTION: "front"},
        new_attrs={ATTR_DIRECTION: "front"},
        expected_result=False,
    ),
    test.case(
        "direction_change",
        old_attrs={ATTR_DIRECTION: "front"},
        new_attrs={ATTR_DIRECTION: "back"},
        expected_result=True,
    ),
    test.case(
        "oscillating_same",
        old_attrs={ATTR_OSCILLATING: True},
        new_attrs={ATTR_OSCILLATING: True},
        expected_result=False,
    ),
    test.case(
        "oscillating_change",
        old_attrs={ATTR_OSCILLATING: True},
        new_attrs={ATTR_OSCILLATING: False},
        expected_result=True,
    ),
    test.case(
        "preset_same",
        old_attrs={ATTR_PRESET_MODE: "auto"},
        new_attrs={ATTR_PRESET_MODE: "auto"},
        expected_result=False,
    ),
    test.case(
        "preset_change",
        old_attrs={ATTR_PRESET_MODE: "auto"},
        new_attrs={ATTR_PRESET_MODE: "whoosh"},
        expected_result=True,
    ),
    test.case(
        "preset_same_oscillating_change",
        old_attrs={ATTR_PRESET_MODE: "auto", ATTR_OSCILLATING: True},
        new_attrs={ATTR_PRESET_MODE: "auto", ATTR_OSCILLATING: False},
        expected_result=True,
    ),
)
async def significant_atributes_change(
    old_attrs: dict[str, Any],
    new_attrs: dict[str, Any],
    expected_result: bool,
) -> None:
    """Detect Fan significant attribute changes."""
    expect(
        async_check_significant_change(None, "state", old_attrs, "state", new_attrs)
    ).to_equal(expected_result)
