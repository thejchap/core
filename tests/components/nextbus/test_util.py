"""Tryke skip-stubs for nextbus util tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def util_placeholder() -> None:
    """Placeholder skipped sibling tests for test_util.py."""
