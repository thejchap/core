"""Tryke skip-stubs for netatmo api tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def api_placeholder() -> None:
    """Placeholder skipped sibling tests for test_api.py."""
