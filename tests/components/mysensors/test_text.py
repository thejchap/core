"""Tryke skip-stubs for mysensors test_text (port deferred)."""
from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def text_node() -> None:
    """Stub for test_text_node (port deferred)."""


