"""Tryke skip-stubs for mqtt lock tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def lock_placeholder() -> None:
    """Placeholder skipped sibling tests for test_lock.py."""
