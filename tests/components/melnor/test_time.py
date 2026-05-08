"""Tryke skip-stubs for melnor time tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def time_placeholder() -> None:
    """Placeholder skipped sibling tests for test_time.py."""
