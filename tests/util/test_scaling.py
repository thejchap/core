"""Test Home Assistant scaling utils."""

import math

from tryke import expect, test

from homeassistant.util.percentage import (
    scale_ranged_value_to_int_range,
    scale_to_ranged_value,
)


@test.cases(
    test.case("255-100", input_val=255, output_val=100),
    test.case("127-49", input_val=127, output_val=49),
    test.case("10-3", input_val=10, output_val=3),
    test.case("1-0", input_val=1, output_val=0),
)
async def ranged_value_to_int_range_large(input_val: float, output_val: int) -> None:
    """Test a large range of low and high values convert a single value to a percentage."""
    source_range = (1, 255)
    dest_range = (1, 100)

    expect(
        scale_ranged_value_to_int_range(source_range, dest_range, input_val)
    ).to_equal(output_val)


@test.cases(
    test.case("100-255-255", input_val=100, output_val=255, math_ceil=255),
    test.case("50-127.5-128", input_val=50, output_val=127.5, math_ceil=128),
    test.case("4-10.2-11", input_val=4, output_val=10.2, math_ceil=11),
)
async def scale_to_ranged_value_large(
    input_val: float, output_val: float, math_ceil: int
) -> None:
    """Test a large range of low and high values convert an int to a single value."""
    source_range = (1, 100)
    dest_range = (1, 255)

    expect(scale_to_ranged_value(source_range, dest_range, input_val)).to_equal(
        output_val
    )
    expect(
        math.ceil(scale_to_ranged_value(source_range, dest_range, input_val))
    ).to_equal(math_ceil)


@test.cases(
    test.case("1-16", input_val=1, output_val=16),
    test.case("2-33", input_val=2, output_val=33),
    test.case("3-50", input_val=3, output_val=50),
    test.case("4-66", input_val=4, output_val=66),
    test.case("5-83", input_val=5, output_val=83),
    test.case("6-100", input_val=6, output_val=100),
)
async def scale_ranged_value_to_int_range_small(
    input_val: float, output_val: int
) -> None:
    """Test a small range of low and high values convert a single value to a percentage."""
    source_range = (1, 6)
    dest_range = (1, 100)

    expect(
        scale_ranged_value_to_int_range(source_range, dest_range, input_val)
    ).to_equal(output_val)


@test.cases(
    test.case("16-1", input_val=16, output_val=1),
    test.case("33-2", input_val=33, output_val=2),
    test.case("50-3", input_val=50, output_val=3),
    test.case("66-4", input_val=66, output_val=4),
    test.case("83-5", input_val=83, output_val=5),
    test.case("100-6", input_val=100, output_val=6),
)
async def scale_to_ranged_value_small(input_val: float, output_val: int) -> None:
    """Test a small range of low and high values convert an int to a single value."""
    source_range = (1, 100)
    dest_range = (1, 6)

    expect(
        math.ceil(scale_to_ranged_value(source_range, dest_range, input_val))
    ).to_equal(output_val)


@test.cases(
    test.case("1-25", input_val=1, output_val=25),
    test.case("2-50", input_val=2, output_val=50),
    test.case("3-75", input_val=3, output_val=75),
    test.case("4-100", input_val=4, output_val=100),
)
async def scale_ranged_value_to_int_range_starting_at_one(
    input_val: float, output_val: int
) -> None:
    """Test a range that starts with 1."""
    source_range = (1, 4)
    dest_range = (1, 100)

    expect(
        scale_ranged_value_to_int_range(source_range, dest_range, input_val)
    ).to_equal(output_val)


@test.cases(
    test.case("101-0", input_val=101, output_val=0),
    test.case("139-25", input_val=139, output_val=25),
    test.case("178-50", input_val=178, output_val=50),
    test.case("217-75", input_val=217, output_val=75),
    test.case("255-100", input_val=255, output_val=100),
)
async def scale_ranged_value_to_int_range_starting_high(
    input_val: float, output_val: int
) -> None:
    """Test a range that does not start with 1."""
    source_range = (101, 255)
    dest_range = (1, 100)

    expect(
        scale_ranged_value_to_int_range(source_range, dest_range, input_val)
    ).to_equal(output_val)


@test.cases(
    test.case("0-25-25.0", input_val=0.0, output_int=25, output_float=25.0),
    test.case("1-50-50.0", input_val=1.0, output_int=50, output_float=50.0),
    test.case("2-75-75.0", input_val=2.0, output_int=75, output_float=75.0),
    test.case("3-100-100.0", input_val=3.0, output_int=100, output_float=100.0),
)
async def scale_ranged_value_to_scaled_range_starting_zero(
    input_val: float, output_int: int, output_float: float
) -> None:
    """Test a range that starts with 0."""
    source_range = (0, 3)
    dest_range = (1, 100)

    expect(
        scale_ranged_value_to_int_range(source_range, dest_range, input_val)
    ).to_equal(output_int)
    expect(scale_to_ranged_value(source_range, dest_range, input_val)).to_equal(
        output_float
    )
    expect(
        scale_ranged_value_to_int_range(dest_range, source_range, output_float)
    ).to_equal(int(input_val))
    expect(scale_to_ranged_value(dest_range, source_range, output_float)).to_equal(
        input_val
    )


@test.cases(
    test.case("101-100", input_val=101, output_val=100),
    test.case("139-125", input_val=139, output_val=125),
    test.case("178-150", input_val=178, output_val=150),
    test.case("217-175", input_val=217, output_val=175),
    test.case("255-200", input_val=255, output_val=200),
)
async def scale_ranged_value_to_int_range_starting_high_with_offset(
    input_val: float, output_val: int
) -> None:
    """Test a ranges that do not start with 1."""
    source_range = (101, 255)
    dest_range = (101, 200)

    expect(
        scale_ranged_value_to_int_range(source_range, dest_range, input_val)
    ).to_equal(output_val)


@test.cases(
    test.case("0-125", input_val=0, output_val=125),
    test.case("1-150", input_val=1, output_val=150),
    test.case("2-175", input_val=2, output_val=175),
    test.case("3-200", input_val=3, output_val=200),
)
async def scale_ranged_value_to_int_range_starting_zero_with_offset(
    input_val: float, output_val: int
) -> None:
    """Test a range that starts with 0 and an other starting high."""
    source_range = (0, 3)
    dest_range = (101, 200)

    expect(
        scale_ranged_value_to_int_range(source_range, dest_range, input_val)
    ).to_equal(output_val)


@test.cases(
    test.case("0-1-1.0", input_val=0.0, output_int=1, output_float=1.0),
    test.case("1-3-3.0", input_val=1.0, output_int=3, output_float=3.0),
    test.case("2-5-5.0", input_val=2.0, output_int=5, output_float=5.0),
    test.case("3-7-7.0", input_val=3.0, output_int=7, output_float=7.0),
)
async def scale_ranged_value_to_int_range_starting_zero_with_zero_offset(
    input_val: float, output_int: int, output_float: float
) -> None:
    """Test a ranges that start with 0.

    In case a range starts with 0, this means value 0 is the first value,
    and the values shift -1.
    """
    source_range = (0, 3)
    dest_range = (0, 7)

    expect(
        scale_ranged_value_to_int_range(source_range, dest_range, input_val)
    ).to_equal(output_int)
    expect(scale_to_ranged_value(source_range, dest_range, input_val)).to_equal(
        output_float
    )
    expect(
        scale_ranged_value_to_int_range(dest_range, source_range, output_int)
    ).to_equal(int(input_val))
    expect(scale_to_ranged_value(dest_range, source_range, output_float)).to_equal(
        input_val
    )
