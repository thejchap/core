"""Tryke skip-stubs for ovo_energy config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_form() -> None:
    """Stub for test_show_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def authorization_error() -> None:
    """Stub for test_authorization_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def connection_error() -> None:
    """Stub for test_connection_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def full_flow_implementation() -> None:
    """Stub for test_full_flow_implementation (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_authorization_error() -> None:
    """Stub for test_reauth_authorization_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_connection_error() -> None:
    """Stub for test_reauth_connection_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_flow() -> None:
    """Stub for test_reauth_flow (port deferred)."""
