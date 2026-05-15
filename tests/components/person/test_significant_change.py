"""Test the Person significant change platform."""

from tryke import expect, test

from homeassistant.components.person.significant_change import (
    async_check_significant_change,
)


@test
async def significant_change() -> None:
    """Detect Person significant changes and ensure that attribute changes do not trigger a significant change."""
    old_attrs = {"source": "device_tracker.wifi_device"}
    new_attrs = {"source": "device_tracker.gps_device"}
    expect(
        async_check_significant_change(None, "home", old_attrs, "home", new_attrs)
    ).to_be_falsy()
    expect(
        async_check_significant_change(None, "home", new_attrs, "not_home", new_attrs)
    ).to_be_truthy()
