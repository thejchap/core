"""Tryke skip-stubs for mqtt fan tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def fan_placeholder() -> None:
    """Placeholder skipped sibling tests for test_fan.py."""
