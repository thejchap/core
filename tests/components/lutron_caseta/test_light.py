"""Tryke skip-stubs for lutron_caseta light tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def light_placeholder() -> None:
    """Placeholder skipped sibling tests for test_light.py."""
