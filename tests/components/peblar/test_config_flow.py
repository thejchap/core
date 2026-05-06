"""Tryke skip-stubs for peblar config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow() -> None:
    """Stub for test_user_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_errors() -> None:
    """Stub for test_user_flow_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_already_configured() -> None:
    """Stub for test_user_flow_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow() -> None:
    """Stub for test_reconfigure_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_to_different_device() -> None:
    """Stub for test_reconfigure_to_different_device (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow_errors() -> None:
    """Stub for test_reconfigure_flow_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_flow() -> None:
    """Stub for test_zeroconf_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_flow_abort_no_serial() -> None:
    """Stub for test_zeroconf_flow_abort_no_serial (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_flow_errors() -> None:
    """Stub for test_zeroconf_flow_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_flow_not_discovered_again() -> None:
    """Stub for test_zeroconf_flow_not_discovered_again (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_with_zeroconf_in_progress() -> None:
    """Stub for test_user_flow_with_zeroconf_in_progress (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_flow() -> None:
    """Stub for test_reauth_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_flow_errors() -> None:
    """Stub for test_reauth_flow_errors (port deferred)."""
