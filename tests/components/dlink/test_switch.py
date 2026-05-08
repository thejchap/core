"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def switch_state() -> None:
    """Stub for test_switch_state."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def switch_no_value() -> None:
    """Stub for test_switch_no_value."""

