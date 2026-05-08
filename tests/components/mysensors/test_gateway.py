"""Tryke skip-stubs for mysensors test_gateway (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def is_serial_port_windows() -> None:
    """Stub for test_is_serial_port_windows (port deferred)."""


