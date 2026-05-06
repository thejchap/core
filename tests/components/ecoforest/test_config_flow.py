"""Tryke skip-stubs for ecoforest config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_device_already_configured() -> None:
    """Stub for test_form_device_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_fails() -> None:
    """Stub for test_flow_fails (port deferred)."""
