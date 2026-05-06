"""Test Home Assistant percentage conversions."""

import math

from tryke import expect, test

from homeassistant.util.percentage import (
    ordered_list_item_to_percentage as _ordered_list_item_to_percentage,
    percentage_to_ordered_list_item as _percentage_to_ordered_list_item,
    percentage_to_ranged_value as _percentage_to_ranged_value,
    ranged_value_to_percentage as _ranged_value_to_percentage,
)

SPEED_LOW = "low"
SPEED_MEDIUM = "medium"
SPEED_HIGH = "high"

SPEED_1 = SPEED_LOW
SPEED_2 = SPEED_MEDIUM
SPEED_3 = SPEED_HIGH
SPEED_4 = "very_high"
SPEED_5 = "storm"
SPEED_6 = "hurricane"
SPEED_7 = "solar_wind"

LEGACY_ORDERED_LIST = [SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
SMALL_ORDERED_LIST = [SPEED_1, SPEED_2, SPEED_3, SPEED_4]
LARGE_ORDERED_LIST = [SPEED_1, SPEED_2, SPEED_3, SPEED_4, SPEED_5, SPEED_6, SPEED_7]


@test
async def ordered_list_item_to_percentage() -> None:
    """Test percentage of an item in an ordered list."""

    expect(_ordered_list_item_to_percentage(LEGACY_ORDERED_LIST, SPEED_LOW)).to_equal(
        33
    )
    expect(
        _ordered_list_item_to_percentage(LEGACY_ORDERED_LIST, SPEED_MEDIUM)
    ).to_equal(66)
    expect(_ordered_list_item_to_percentage(LEGACY_ORDERED_LIST, SPEED_HIGH)).to_equal(
        100
    )

    expect(_ordered_list_item_to_percentage(SMALL_ORDERED_LIST, SPEED_1)).to_equal(25)
    expect(_ordered_list_item_to_percentage(SMALL_ORDERED_LIST, SPEED_2)).to_equal(50)
    expect(_ordered_list_item_to_percentage(SMALL_ORDERED_LIST, SPEED_3)).to_equal(75)
    expect(_ordered_list_item_to_percentage(SMALL_ORDERED_LIST, SPEED_4)).to_equal(100)

    expect(_ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_1)).to_equal(14)
    expect(_ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_2)).to_equal(28)
    expect(_ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_3)).to_equal(42)
    expect(_ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_4)).to_equal(57)
    expect(_ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_5)).to_equal(71)
    expect(_ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_6)).to_equal(85)
    expect(_ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_7)).to_equal(100)

    expect(lambda: _ordered_list_item_to_percentage([], SPEED_1)).to_raise(ValueError)


@test
async def percentage_to_ordered_list_item() -> None:
    """Test item that most closely matches the percentage in an ordered list."""

    expect(_percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 1)).to_equal(SPEED_1)
    expect(_percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 25)).to_equal(SPEED_1)
    expect(_percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 26)).to_equal(SPEED_2)
    expect(_percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 50)).to_equal(SPEED_2)
    expect(_percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 51)).to_equal(SPEED_3)
    expect(_percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 75)).to_equal(SPEED_3)
    expect(_percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 76)).to_equal(SPEED_4)
    expect(_percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 100)).to_equal(SPEED_4)

    expect(_percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 17)).to_equal(
        SPEED_LOW
    )
    expect(_percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 33)).to_equal(
        SPEED_LOW
    )
    expect(_percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 50)).to_equal(
        SPEED_MEDIUM
    )
    expect(_percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 66)).to_equal(
        SPEED_MEDIUM
    )
    expect(_percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 84)).to_equal(
        SPEED_HIGH
    )
    expect(_percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 100)).to_equal(
        SPEED_HIGH
    )

    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 1)).to_equal(SPEED_1)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 14)).to_equal(SPEED_1)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 25)).to_equal(SPEED_2)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 26)).to_equal(SPEED_2)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 28)).to_equal(SPEED_2)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 29)).to_equal(SPEED_3)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 41)).to_equal(SPEED_3)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 42)).to_equal(SPEED_3)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 43)).to_equal(SPEED_4)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 56)).to_equal(SPEED_4)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 50)).to_equal(SPEED_4)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 51)).to_equal(SPEED_4)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 75)).to_equal(SPEED_6)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 76)).to_equal(SPEED_6)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 100)).to_equal(SPEED_7)

    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 1)).to_equal(SPEED_1)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 25)).to_equal(SPEED_2)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 26)).to_equal(SPEED_2)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 50)).to_equal(SPEED_4)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 51)).to_equal(SPEED_4)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 75)).to_equal(SPEED_6)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 76)).to_equal(SPEED_6)
    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 100)).to_equal(SPEED_7)

    expect(_percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 100.1)).to_equal(
        SPEED_7
    )

    expect(lambda: _percentage_to_ordered_list_item([], 100)).to_raise(ValueError)


@test
async def ranged_value_to_percentage_large() -> None:
    """Test a large range of low and high values convert a single value to a percentage."""
    value_range = (1, 255)

    expect(_ranged_value_to_percentage(value_range, 255)).to_equal(100)
    expect(_ranged_value_to_percentage(value_range, 127)).to_equal(49)
    expect(_ranged_value_to_percentage(value_range, 10)).to_equal(3)
    expect(_ranged_value_to_percentage(value_range, 1)).to_equal(0)


@test
async def percentage_to_ranged_value_large() -> None:
    """Test a large range of low and high values convert a percentage to a single value."""
    value_range = (1, 255)

    expect(_percentage_to_ranged_value(value_range, 100)).to_equal(255)
    expect(_percentage_to_ranged_value(value_range, 50)).to_equal(127.5)
    expect(_percentage_to_ranged_value(value_range, 4)).to_equal(10.2)

    expect(math.ceil(_percentage_to_ranged_value(value_range, 100))).to_equal(255)
    expect(math.ceil(_percentage_to_ranged_value(value_range, 50))).to_equal(128)
    expect(math.ceil(_percentage_to_ranged_value(value_range, 4))).to_equal(11)


@test
async def ranged_value_to_percentage_small() -> None:
    """Test a small range of low and high values convert a single value to a percentage."""
    value_range = (1, 6)

    expect(_ranged_value_to_percentage(value_range, 1)).to_equal(16)
    expect(_ranged_value_to_percentage(value_range, 2)).to_equal(33)
    expect(_ranged_value_to_percentage(value_range, 3)).to_equal(50)
    expect(_ranged_value_to_percentage(value_range, 4)).to_equal(66)
    expect(_ranged_value_to_percentage(value_range, 5)).to_equal(83)
    expect(_ranged_value_to_percentage(value_range, 6)).to_equal(100)


@test
async def percentage_to_ranged_value_small() -> None:
    """Test a small range of low and high values convert a percentage to a single value."""
    value_range = (1, 6)

    expect(math.ceil(_percentage_to_ranged_value(value_range, 16))).to_equal(1)
    expect(math.ceil(_percentage_to_ranged_value(value_range, 33))).to_equal(2)
    expect(math.ceil(_percentage_to_ranged_value(value_range, 50))).to_equal(3)
    expect(math.ceil(_percentage_to_ranged_value(value_range, 66))).to_equal(4)
    expect(math.ceil(_percentage_to_ranged_value(value_range, 83))).to_equal(5)
    expect(math.ceil(_percentage_to_ranged_value(value_range, 100))).to_equal(6)


@test
async def ranged_value_to_percentage_starting_at_one() -> None:
    """Test a range that starts with 1."""
    value_range = (1, 4)

    expect(_ranged_value_to_percentage(value_range, 1)).to_equal(25)
    expect(_ranged_value_to_percentage(value_range, 2)).to_equal(50)
    expect(_ranged_value_to_percentage(value_range, 3)).to_equal(75)
    expect(_ranged_value_to_percentage(value_range, 4)).to_equal(100)


@test
async def ranged_value_to_percentage_starting_high() -> None:
    """Test a range that does not start with 1."""
    value_range = (101, 255)

    expect(_ranged_value_to_percentage(value_range, 101)).to_equal(0)
    expect(_ranged_value_to_percentage(value_range, 139)).to_equal(25)
    expect(_ranged_value_to_percentage(value_range, 178)).to_equal(50)
    expect(_ranged_value_to_percentage(value_range, 217)).to_equal(75)
    expect(_ranged_value_to_percentage(value_range, 255)).to_equal(100)


@test
async def ranged_value_to_percentage_starting_zero() -> None:
    """Test a range that starts with 0."""
    value_range = (0, 3)

    expect(_ranged_value_to_percentage(value_range, 0)).to_equal(25)
    expect(_ranged_value_to_percentage(value_range, 1)).to_equal(50)
    expect(_ranged_value_to_percentage(value_range, 2)).to_equal(75)
    expect(_ranged_value_to_percentage(value_range, 3)).to_equal(100)
