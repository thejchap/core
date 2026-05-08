"""Tryke skip-stubs for powerwall init tests.

Original tests use Powerwall API mocks; full port deferred.
"""

from tryke import test

@test.skip("Powerwall API mocks")
async def update_data_reauthenticate_on_access_denied() -> None:
    """Test if _update_data of PowerwallDataManager reauthenticates on AccessDeniedError."""

@test.skip("Powerwall API mocks")
async def init_uses_cookie_if_present() -> None:
    """Tests if the init will use the auth cookie if present."""

@test.skip("Powerwall API mocks")
async def init_uses_password_if_no_cookies() -> None:
    """Tests if the init will use the password if no auth cookie present."""

@test.skip("Powerwall API mocks")
async def init_saves_the_cookie() -> None:
    """Tests that the cookie is properly saved."""

@test.skip("Powerwall API mocks")
async def retry_ignores_cookie() -> None:
    """Tests that retrying uses the password instead."""

@test.skip("Powerwall API mocks")
async def reauth_ignores_and_clears_cookie() -> None:
    """Tests that the reauth flow uses password and clears the cookie."""

@test.skip("Powerwall API mocks")
async def init_retries_with_password() -> None:
    """Tests that the init retries with password if cookie fails."""
