"""Tryke skip-stubs for nuki config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_invalid_auth() -> None:
    """Stub for test_form_invalid_auth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_cannot_connect() -> None:
    """Stub for test_form_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_unknown_exception() -> None:
    """Stub for test_form_unknown_exception (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_already_configured() -> None:
    """Stub for test_form_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def dhcp_flow() -> None:
    """Stub for test_dhcp_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def dhcp_flow_already_configured() -> None:
    """Stub for test_dhcp_flow_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_success() -> None:
    """Stub for test_reauth_success (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_invalid_auth() -> None:
    """Stub for test_reauth_invalid_auth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_cannot_connect() -> None:
    """Stub for test_reauth_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_unknown_exception() -> None:
    """Stub for test_reauth_unknown_exception (port deferred)."""
