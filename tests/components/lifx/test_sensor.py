"""Tryke skip-stubs for test_sensor.py - sibling port deferred (139 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (139 LOC, 0 parametrize)")
async def rssi_sensor() -> None:
    """Stub for test_rssi_sensor."""

@test.skip("sibling port deferred (139 LOC, 0 parametrize)")
async def rssi_sensor_old_firmware() -> None:
    """Stub for test_rssi_sensor_old_firmware."""
