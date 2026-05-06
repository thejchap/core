"""Tryke skip-stubs for opentherm_gw config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_user() -> None:
    """Stub for test_form_user (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_duplicate_entries() -> None:
    """Stub for test_form_duplicate_entries (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_connection_timeout() -> None:
    """Stub for test_form_connection_timeout (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_connection_error() -> None:
    """Stub for test_form_connection_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_form() -> None:
    """Stub for test_options_form (port deferred)."""
