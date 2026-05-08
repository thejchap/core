"""Tryke skip-stubs for motionblinds_ble select tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def select_placeholder() -> None:
    """Placeholder skipped sibling tests for test_select.py."""
