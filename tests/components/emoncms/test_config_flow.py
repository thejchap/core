"""Tryke skip-stubs for emoncms config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure() -> None:
    """Stub for test_reconfigure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_api_error() -> None:
    """Stub for test_reconfigure_api_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_failure() -> None:
    """Stub for test_user_flow_failure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_manual_mode() -> None:
    """Stub for test_user_flow_manual_mode (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_auto_mode() -> None:
    """Stub for test_user_flow_auto_mode (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_flow_failure() -> None:
    """Stub for test_options_flow_failure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def unique_id_exists() -> None:
    """Stub for test_unique_id_exists (port deferred)."""
