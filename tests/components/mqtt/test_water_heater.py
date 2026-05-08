"""Tryke skip-stubs for mqtt water heater tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def water_heater_placeholder() -> None:
    """Placeholder skipped sibling tests for test_water_heater.py."""
