"""Tryke skip-stubs for mysensors test_climate (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def hvac_node_auto() -> None:
    """Stub for test_hvac_node_auto (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def hvac_node_heat() -> None:
    """Stub for test_hvac_node_heat (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def hvac_node_cool() -> None:
    """Stub for test_hvac_node_cool (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def hvac_node_only_hvac() -> None:
    """Stub for test_hvac_node_only_hvac (port deferred)."""


