"""Tryke skip-stubs for mqtt binary sensor tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def binary_sensor_placeholder() -> None:
    """Placeholder skipped sibling tests for test_binary_sensor.py."""
