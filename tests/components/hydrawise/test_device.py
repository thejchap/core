"""Tryke skip-stubs for test_device.py - sibling port deferred (40 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (40 LOC, 0 parametrize)")
async def zones_in_device_registry() -> None:
    """Stub for test_zones_in_device_registry."""

@test.skip("sibling port deferred (40 LOC, 0 parametrize)")
async def controller_in_device_registry() -> None:
    """Stub for test_controller_in_device_registry."""
