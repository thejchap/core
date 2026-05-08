"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def relay_button() -> None:
    """Stub for test_relay_button."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def ir_button() -> None:
    """Stub for test_ir_button."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def reset_favorites_button() -> None:
    """Stub for test_reset_favorites_button."""

