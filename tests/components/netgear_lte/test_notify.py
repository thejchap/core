"""Tryke skip-stubs for netgear_lte notify tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def notify_placeholder() -> None:
    """Placeholder skipped sibling tests for test_notify.py."""
