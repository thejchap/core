"""Tryke skip-stubs for melnor number tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def number_placeholder() -> None:
    """Placeholder skipped sibling tests for test_number.py."""
