"""Tryke skip-stubs for devolo_home_network config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_error() -> None:
    """Stub for test_form_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf() -> None:
    """Stub for test_zeroconf (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_wrong_auth() -> None:
    """Stub for test_zeroconf_wrong_auth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def abort_zeroconf_wrong_device() -> None:
    """Stub for test_abort_zeroconf_wrong_device (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def abort_if_configured() -> None:
    """Stub for test_abort_if_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_reauth() -> None:
    """Stub for test_form_reauth (port deferred)."""
