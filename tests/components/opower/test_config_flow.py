"""Tryke skip-stubs for opower config flow tests.

Original tests use recorder_mock fixture; full port deferred.
"""

from tryke import test

@test.skip("recorder_mock fixture")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_with_totp() -> None:
    """Stub for test_form_with_totp (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_with_invalid_totp() -> None:
    """Stub for test_form_with_invalid_totp (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_with_mfa_challenge() -> None:
    """Stub for test_form_with_mfa_challenge (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_with_mfa_challenge_but_no_mfa_options() -> None:
    """Stub for test_form_with_mfa_challenge_but_no_mfa_options (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_exceptions() -> None:
    """Stub for test_form_exceptions (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_already_configured() -> None:
    """Stub for test_form_already_configured (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_not_already_configured() -> None:
    """Stub for test_form_not_already_configured (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_valid_reauth() -> None:
    """Stub for test_form_valid_reauth (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_valid_reauth_with_totp() -> None:
    """Stub for test_form_valid_reauth_with_totp (port deferred)."""

@test.skip("recorder_mock fixture")
async def reauth_with_mfa_challenge() -> None:
    """Stub for test_reauth_with_mfa_challenge (port deferred)."""
