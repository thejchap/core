"""Tryke skip-stubs for lutron_caseta switch tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def switch_placeholder() -> None:
    """Placeholder skipped sibling tests for test_switch.py."""
