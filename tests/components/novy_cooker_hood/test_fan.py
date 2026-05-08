"""Tryke skip-stubs for novy_cooker_hood fan tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def fan_placeholder() -> None:
    """Placeholder skipped sibling tests for test_fan.py."""
