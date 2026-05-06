"""Tryke skip-stubs for onewire config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow() -> None:
    """Stub for test_user_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_recovery() -> None:
    """Stub for test_user_flow_recovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_duplicate() -> None:
    """Stub for test_user_duplicate (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow() -> None:
    """Stub for test_reconfigure_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_duplicate() -> None:
    """Stub for test_reconfigure_duplicate (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def hassio_flow() -> None:
    """Stub for test_hassio_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def hassio_duplicate() -> None:
    """Stub for test_hassio_duplicate (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_flow() -> None:
    """Stub for test_zeroconf_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_duplicate() -> None:
    """Stub for test_zeroconf_duplicate (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_options_clear() -> None:
    """Stub for test_user_options_clear (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_options_empty_selection_recovery() -> None:
    """Stub for test_user_options_empty_selection_recovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_options_set_single() -> None:
    """Stub for test_user_options_set_single (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_options_set_multiple() -> None:
    """Stub for test_user_options_set_multiple (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_options_no_devices() -> None:
    """Stub for test_user_options_no_devices (port deferred)."""
