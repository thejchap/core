"""Tryke skip-stubs for mysensors test_device_tracker (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def gps_sensor() -> None:
    """Stub for test_gps_sensor (port deferred)."""


