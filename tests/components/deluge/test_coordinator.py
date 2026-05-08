"""Tryke skip stub for test_coordinator.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_count() -> None:
    """Stub for test_get_count."""

