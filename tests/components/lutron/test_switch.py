"""Tryke skip-stubs for lutron switch tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def switch_placeholder() -> None:
    """Placeholder skipped sibling tests for test_switch.py."""
