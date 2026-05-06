"""Tryke skip-stubs for nexia config flow tests.

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
async def form_invalid_auth_http_401() -> None:
    """Stub for test_form_invalid_auth_http_401 (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_cannot_connect_not_found() -> None:
    """Stub for test_form_cannot_connect_not_found (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_broad_exception() -> None:
    """Stub for test_form_broad_exception (port deferred)."""
