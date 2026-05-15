"""Test the sensor significant change platform."""

from tryke import expect, test

from homeassistant.components.switch.significant_change import (
    async_check_significant_change,
)


@test
async def significant_change() -> None:
    """Detect Switch significant change."""
    attrs: dict = {}
    expect(async_check_significant_change(None, "on", attrs, "on", attrs)).to_be_falsy()
    expect(
        async_check_significant_change(None, "off", attrs, "off", attrs)
    ).to_be_falsy()
    expect(
        async_check_significant_change(None, "on", attrs, "off", attrs)
    ).to_be_truthy()
