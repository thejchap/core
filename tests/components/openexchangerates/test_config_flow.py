"""Tryke skip-stubs for openexchangerates config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_create_entry() -> None:
    """Stub for test_user_create_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_invalid_auth() -> None:
    """Stub for test_form_invalid_auth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_cannot_connect() -> None:
    """Stub for test_form_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_unknown_error() -> None:
    """Stub for test_form_unknown_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def already_configured_service() -> None:
    """Stub for test_already_configured_service (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def no_currencies() -> None:
    """Stub for test_no_currencies (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def currencies_timeout() -> None:
    """Stub for test_currencies_timeout (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def latest_rates_timeout() -> None:
    """Stub for test_latest_rates_timeout (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""
