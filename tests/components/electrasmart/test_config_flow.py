"""Tryke skip-stubs for electrasmart config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def one_time_password() -> None:
    """Stub for test_one_time_password (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def one_time_password_api_error() -> None:
    """Stub for test_one_time_password_api_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def cannot_connect() -> None:
    """Stub for test_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def invalid_phone_number() -> None:
    """Stub for test_invalid_phone_number (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def invalid_auth() -> None:
    """Stub for test_invalid_auth (port deferred)."""
