"""Tryke skip-stubs for picnic config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_2fa_required() -> None:
    """Stub for test_form_2fa_required (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_2fa_channel_cannot_connect() -> None:
    """Stub for test_form_2fa_channel_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_2fa_channel_exception() -> None:
    """Stub for test_form_2fa_channel_exception (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_2fa_wrong_code() -> None:
    """Stub for test_form_2fa_wrong_code (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_2fa_cannot_connect() -> None:
    """Stub for test_form_2fa_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_2fa_exception() -> None:
    """Stub for test_form_2fa_exception (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_invalid_auth() -> None:
    """Stub for test_form_invalid_auth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_cannot_connect() -> None:
    """Stub for test_form_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_exception() -> None:
    """Stub for test_form_exception (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_already_configured() -> None:
    """Stub for test_form_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def step_reauth() -> None:
    """Stub for test_step_reauth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def step_reauth_failed() -> None:
    """Stub for test_step_reauth_failed (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def step_reauth_different_account() -> None:
    """Stub for test_step_reauth_different_account (port deferred)."""
