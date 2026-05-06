"""Tryke skip-stubs for ecobee config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def abort_if_already_setup() -> None:
    """Stub for test_abort_if_already_setup (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_step_without_user_input() -> None:
    """Stub for test_user_step_without_user_input (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def pin_request_succeeds() -> None:
    """Stub for test_pin_request_succeeds (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def pin_request_fails() -> None:
    """Stub for test_pin_request_fails (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def token_request_succeeds() -> None:
    """Stub for test_token_request_succeeds (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def token_request_fails() -> None:
    """Stub for test_token_request_fails (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def password_login_succeeds() -> None:
    """Stub for test_password_login_succeeds (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def password_login_error_recovers() -> None:
    """Stub for test_password_login_error_recovers (port deferred)."""
