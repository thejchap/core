"""Tryke skip-stubs for mysensors test_binary_sensor (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def door_sensor() -> None:
    """Stub for test_door_sensor (port deferred)."""


