"""Tryke skip-stubs for mysensors test_light (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def dimmer_node() -> None:
    """Stub for test_dimmer_node (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def rgb_node() -> None:
    """Stub for test_rgb_node (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def rgbw_node() -> None:
    """Stub for test_rgbw_node (port deferred)."""


