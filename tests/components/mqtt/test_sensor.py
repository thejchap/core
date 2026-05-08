"""Tryke skip-stubs for mqtt sensor tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def sensor_placeholder() -> None:
    """Placeholder skipped sibling tests for test_sensor.py."""
