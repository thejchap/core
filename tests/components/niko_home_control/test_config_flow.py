"""Tryke skip-stubs for niko_home_control config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_errors() -> None:
    """Stub for test_flow_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def duplicate_entry() -> None:
    """Stub for test_duplicate_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def duplicate_reconfigure_entry() -> None:
    """Stub for test_duplicate_reconfigure_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure() -> None:
    """Stub for test_reconfigure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_errors() -> None:
    """Stub for test_reconfigure_errors (port deferred)."""
