"""Tryke skip-stubs for foscam config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_valid() -> None:
    """Stub for test_user_valid (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_invalid_auth() -> None:
    """Stub for test_user_invalid_auth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_cannot_connect() -> None:
    """Stub for test_user_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_invalid_response() -> None:
    """Stub for test_user_invalid_response (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_already_configured() -> None:
    """Stub for test_user_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_unknown_exception() -> None:
    """Stub for test_user_unknown_exception (port deferred)."""
