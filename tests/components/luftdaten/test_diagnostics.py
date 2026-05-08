"""Tryke skip-stubs for luftdaten diagnostics tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def diagnostics_placeholder() -> None:
    """Placeholder skipped sibling tests for test_diagnostics.py."""
