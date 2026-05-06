"""Tryke skip-stubs for nobo_hub config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def configure_with_discover() -> None:
    """Stub for test_configure_with_discover (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def configure_manual() -> None:
    """Stub for test_configure_manual (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def configure_user_selected_manual() -> None:
    """Stub for test_configure_user_selected_manual (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def configure_invalid_serial_suffix() -> None:
    """Stub for test_configure_invalid_serial_suffix (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def configure_invalid_serial_undiscovered() -> None:
    """Stub for test_configure_invalid_serial_undiscovered (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def configure_invalid_ip_address() -> None:
    """Stub for test_configure_invalid_ip_address (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def configure_cannot_connect() -> None:
    """Stub for test_configure_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""
