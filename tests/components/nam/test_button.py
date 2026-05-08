"""Tryke skip-stubs for nam button tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def button_placeholder() -> None:
    """Placeholder skipped sibling tests for test_button.py."""
