"""Tryke skip-stubs for mysensors test_remote (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def ir_transceiver() -> None:
    """Stub for test_ir_transceiver (port deferred)."""


