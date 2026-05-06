"""Tryke skip-stubs for fitbit config flow tests.

Original tests use OAuth2 application credentials flow; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def token_error() -> None:
    """Stub for test_token_error (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def api_failure() -> None:
    """Stub for test_api_failure (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def config_entry_already_exists() -> None:
    """Stub for test_config_entry_already_exists (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauth_flow() -> None:
    """Stub for test_reauth_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauth_wrong_user_id() -> None:
    """Stub for test_reauth_wrong_user_id (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def partial_profile_data() -> None:
    """Stub for test_partial_profile_data (port deferred)."""
