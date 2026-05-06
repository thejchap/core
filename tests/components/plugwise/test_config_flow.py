"""Tryke skip-stubs for plugwise config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_flow() -> None:
    """Stub for test_zeroconf_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_flow_stretch() -> None:
    """Stub for test_zeroconf_flow_stretch (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zercoconf_discovery_update_configuration() -> None:
    """Stub for test_zercoconf_discovery_update_configuration (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_errors() -> None:
    """Stub for test_flow_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_abort_existing_anna() -> None:
    """Stub for test_user_abort_existing_anna (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_abort_existing_anna() -> None:
    """Stub for test_zeroconf_abort_existing_anna (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_abort_anna_with_existing_config_entries() -> None:
    """Stub for test_zeroconf_abort_anna_with_existing_config_entries (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_abort_anna_with_adam() -> None:
    """Stub for test_zeroconf_abort_anna_with_adam (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow() -> None:
    """Stub for test_reconfigure_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow_smile_mismatch() -> None:
    """Stub for test_reconfigure_flow_smile_mismatch (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow_connect_errors() -> None:
    """Stub for test_reconfigure_flow_connect_errors (port deferred)."""
