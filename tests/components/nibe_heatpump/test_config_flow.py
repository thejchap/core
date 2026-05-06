"""Tryke skip-stubs for nibe_heatpump config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def nibegw_form() -> None:
    """Stub for test_nibegw_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def modbus_form() -> None:
    """Stub for test_modbus_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def modbus_invalid_url() -> None:
    """Stub for test_modbus_invalid_url (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def nibegw_address_inuse() -> None:
    """Stub for test_nibegw_address_inuse (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def read_timeout() -> None:
    """Stub for test_read_timeout (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def write_timeout() -> None:
    """Stub for test_write_timeout (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def unexpected_exception() -> None:
    """Stub for test_unexpected_exception (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def nibegw_invalid_host() -> None:
    """Stub for test_nibegw_invalid_host (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def model_missing_coil() -> None:
    """Stub for test_model_missing_coil (port deferred)."""
