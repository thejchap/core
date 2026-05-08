"""Tryke skip-stubs for matter update tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def update_placeholder() -> None:
    """Placeholder skipped sibling tests for test_update.py."""
