"""Tryke skip-stubs for mqtt update tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def update_placeholder() -> None:
    """Placeholder skipped sibling tests for test_update.py."""
