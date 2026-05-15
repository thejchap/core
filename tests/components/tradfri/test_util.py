"""Tradfri utility function tests."""

from tryke import expect, test

from homeassistant.components.tradfri.fan import _from_fan_percentage, _from_fan_speed


@test.cases(
    test.case("speed_0", fan_speed=0, expected_result=0),
    test.case("speed_2", fan_speed=2, expected_result=2),
    test.case("speed_25", fan_speed=25, expected_result=49),
    test.case("speed_50", fan_speed=50, expected_result=100),
)
def from_fan_speed(fan_speed: int, expected_result: int) -> None:
    """Test that we can convert fan speed to percentage value."""
    expect(_from_fan_speed(fan_speed)).to_equal(expected_result)


@test.cases(
    test.case("pct_1", percentage=1, expected_result=2),
    test.case("pct_100", percentage=100, expected_result=50),
    test.case("pct_50", percentage=50, expected_result=26),
)
def from_percentage(percentage: int, expected_result: int) -> None:
    """Test that we can convert percentage value to fan speed."""
    expect(_from_fan_percentage(percentage)).to_equal(expected_result)
