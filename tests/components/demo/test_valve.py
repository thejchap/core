"""Tryke skip stub for test_valve.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def closing() -> None:
    """Stub for test_closing."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def opening() -> None:
    """Stub for test_opening."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def set_valve_position() -> None:
    """Stub for test_set_valve_position."""

