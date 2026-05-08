"""Tryke skip-stubs for philips_js device trigger tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def device_trigger_placeholder() -> None:
    """Placeholder skipped sibling tests for test_device_trigger.py."""
