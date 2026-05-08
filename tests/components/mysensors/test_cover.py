"""Tryke skip-stubs for mysensors test_cover (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def cover_node_percentage() -> None:
    """Stub for test_cover_node_percentage (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def cover_node_binary() -> None:
    """Stub for test_cover_node_binary (port deferred)."""


