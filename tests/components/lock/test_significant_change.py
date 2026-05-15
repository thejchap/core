"""Test the Lock significant change platform."""

from tryke import expect, test

from homeassistant.components.lock.significant_change import (
    async_check_significant_change,
)


@test
async def significant_change() -> None:
    """Detect Lock significant changes."""
    old_attrs = {"attr_1": "a"}
    new_attrs = {"attr_1": "b"}

    expect(
        async_check_significant_change(None, "locked", old_attrs, "locked", old_attrs)
    ).to_be(False)
    expect(
        async_check_significant_change(None, "locked", old_attrs, "locked", new_attrs)
    ).to_be(False)
    expect(
        async_check_significant_change(
            None, "locked", old_attrs, "unlocked", old_attrs
        )
    ).to_be(True)
