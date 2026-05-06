"""Tryke skip-stubs for powerfox_local config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def full_user_flow() -> None:
    """Stub for test_full_user_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_discovery() -> None:
    """Stub for test_zeroconf_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_discovery_errors() -> None:
    """Stub for test_zeroconf_discovery_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_already_configured() -> None:
    """Stub for test_zeroconf_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def duplicate_entry() -> None:
    """Stub for test_duplicate_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_exceptions() -> None:
    """Stub for test_user_flow_exceptions (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def step_reauth() -> None:
    """Stub for test_step_reauth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def step_reauth_exceptions() -> None:
    """Stub for test_step_reauth_exceptions (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow() -> None:
    """Stub for test_reconfigure_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow_exceptions() -> None:
    """Stub for test_reconfigure_flow_exceptions (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow_unique_id_mismatch() -> None:
    """Stub for test_reconfigure_flow_unique_id_mismatch (port deferred)."""
