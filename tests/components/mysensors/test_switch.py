"""Tryke skip-stubs for mysensors test_switch (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def relay_node() -> None:
    """Stub for test_relay_node (port deferred)."""


