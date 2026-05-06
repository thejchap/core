"""Test variance method."""

from datetime import datetime, timedelta

from tryke import expect, test

from homeassistant.util.variance import ignore_variance as _ignore_variance


@test.cases(
    test.case("1-1-1-1", value_1=1, value_2=1, variance=1, expected=1),
    test.case("1-2-2-1", value_1=1, value_2=2, variance=2, expected=1),
    test.case("1-2-0-2", value_1=1, value_2=2, variance=0, expected=2),
    test.case("2-1-0-1", value_1=2, value_2=1, variance=0, expected=1),
    test.case(
        "value_14-value_24-variance4-expected4",
        value_1=datetime(2020, 1, 1, 0, 0),
        value_2=datetime(2020, 1, 2, 0, 0),
        variance=timedelta(days=2),
        expected=datetime(2020, 1, 1, 0, 0),
    ),
    test.case(
        "value_15-value_25-variance5-expected5",
        value_1=datetime(2020, 1, 2, 0, 0),
        value_2=datetime(2020, 1, 1, 0, 0),
        variance=timedelta(days=2),
        expected=datetime(2020, 1, 2, 0, 0),
    ),
    test.case(
        "value_16-value_26-variance6-expected6",
        value_1=datetime(2020, 1, 1, 0, 0),
        value_2=datetime(2020, 1, 2, 0, 0),
        variance=timedelta(days=1),
        expected=datetime(2020, 1, 2, 0, 0),
    ),
)
def ignore_variance(
    value_1: object, value_2: object, variance: object, expected: object
) -> None:
    """Test ignore_variance."""
    with_ignore = _ignore_variance(lambda x: x, variance)
    expect(with_ignore(value_1)).to_equal(value_1)
    expect(with_ignore(value_2)).to_equal(expected)
