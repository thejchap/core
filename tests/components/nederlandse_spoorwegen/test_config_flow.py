"""Tryke skip-stubs for nederlandse_spoorwegen config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def creating_route() -> None:
    """Stub for test_creating_route (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_exceptions() -> None:
    """Stub for test_flow_exceptions (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def fetching_stations_failed() -> None:
    """Stub for test_fetching_stations_failed (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def already_configured() -> None:
    """Stub for test_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_success() -> None:
    """Stub for test_reconfigure_success (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_errors() -> None:
    """Stub for test_reconfigure_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_already_configured() -> None:
    """Stub for test_reconfigure_already_configured (port deferred)."""
