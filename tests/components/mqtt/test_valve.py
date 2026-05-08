"""Tryke skip-stubs for mqtt valve tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def valve_placeholder() -> None:
    """Placeholder skipped sibling tests for test_valve.py."""
