"""Tryke skip-stubs for picnic services tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def services_placeholder() -> None:
    """Placeholder skipped sibling tests for test_services.py."""
