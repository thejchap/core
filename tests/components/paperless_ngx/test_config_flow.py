"""Tryke skip-stubs for paperless_ngx config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def full_config_flow() -> None:
    """Stub for test_full_config_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def full_reauth_flow() -> None:
    """Stub for test_full_reauth_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def full_reconfigure_flow() -> None:
    """Stub for test_full_reconfigure_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def config_flow_error_handling() -> None:
    """Stub for test_config_flow_error_handling (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_flow_error_handling() -> None:
    """Stub for test_reauth_flow_error_handling (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_flow_error_handling() -> None:
    """Stub for test_reconfigure_flow_error_handling (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def config_already_exists() -> None:
    """Stub for test_config_already_exists (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def config_already_exists_reconfigure() -> None:
    """Stub for test_config_already_exists_reconfigure (port deferred)."""
