"""Huawei LTE sensor tests."""

from tryke import expect, test

from homeassistant.components.huawei_lte import sensor
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)


@test.cases(
    test.case("dbm_negative", value="-71 dBm", expected=(-71, SIGNAL_STRENGTH_DECIBELS_MILLIWATT)),
    test.case("db_positive", value="15dB", expected=(15, SIGNAL_STRENGTH_DECIBELS)),
    test.case("dbm_gte_negative", value=">=-51dBm", expected=(-51, SIGNAL_STRENGTH_DECIBELS_MILLIWATT)),
    test.case("db_lt_negative", value="&lt;-20dB", expected=(-20, SIGNAL_STRENGTH_DECIBELS)),
    test.case("db_gte_positive", value="&gt;=30dB", expected=(30, SIGNAL_STRENGTH_DECIBELS)),
)
def format_default(*, value: str, expected: tuple) -> None:
    """Test that default formatter copes with expected values."""
    expect(sensor.format_default(value)).to_equal(expected)
