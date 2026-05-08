"""Tryke skip stub for test_update.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_entity() -> None:
    """Stub for test_update_entity."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def no_update_entity() -> None:
    """Stub for test_no_update_entity."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_failure() -> None:
    """Stub for test_update_failure."""

