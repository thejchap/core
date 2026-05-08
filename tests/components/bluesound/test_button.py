"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def set_sleep_timer() -> None:
    """Stub for test_set_sleep_timer."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def clear_sleep_timer() -> None:
    """Stub for test_clear_sleep_timer."""

