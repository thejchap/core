"""The tests for the Daikin target temperature conversion."""

from tryke import expect, test

from homeassistant.components.daikin.climate import format_target_temperature


@test
def int_conversion() -> None:
    """Check no decimal are kept when target temp is an integer."""
    formatted = format_target_temperature("16")
    expect(formatted).to_equal("16")


@test
def rounding() -> None:
    """Check 1 decimal is kept when target temp is a decimal."""
    formatted = format_target_temperature("16.1")
    expect(formatted).to_equal("16")
    formatted = format_target_temperature("16.3")
    expect(formatted).to_equal("16.5")
    formatted = format_target_temperature("16.65")
    expect(formatted).to_equal("16.5")
    formatted = format_target_temperature("16.9")
    expect(formatted).to_equal("17")
