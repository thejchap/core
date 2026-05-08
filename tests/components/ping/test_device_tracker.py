"""Tryke skip-stubs for ping device tracker tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def device_tracker_placeholder() -> None:
    """Placeholder skipped sibling tests for test_device_tracker.py."""
