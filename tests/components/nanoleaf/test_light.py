"""Tryke skip-stubs for nanoleaf test_light (port deferred)."""
from tryke import test

@test.skip("requires aionanoleaf2 + complex zeroconf+ssdp chain (not in tryke shim)")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("requires aionanoleaf2 + complex zeroconf+ssdp chain (not in tryke shim)")
async def turning_on_or_off_writes_state() -> None:
    """Stub for test_turning_on_or_off_writes_state (port deferred)."""


