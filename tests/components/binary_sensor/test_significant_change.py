"""Test the Binary Sensor significant change platform."""

from tryke import expect, test

from homeassistant.components.binary_sensor.significant_change import (
    async_check_significant_change,
)


@test
async def significant_change() -> None:
    """Detect Binary Sensor significant changes."""
    old_attrs = {"attr_1": "value_1"}
    new_attrs = {"attr_1": "value_2"}

    expect(
        async_check_significant_change(None, "on", old_attrs, "on", old_attrs)
    ).to_be(False)
    expect(
        async_check_significant_change(None, "on", old_attrs, "on", new_attrs)
    ).to_be(False)
    expect(
        async_check_significant_change(None, "on", old_attrs, "off", old_attrs)
    ).to_be(True)
