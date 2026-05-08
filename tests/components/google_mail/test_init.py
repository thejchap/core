"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the google_mail integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.google_mail.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("google_mail")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_success() -> None:
    """Stub for test_setup_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_success() -> None:
    """Stub for test_expired_token_refresh_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_failure() -> None:
    """Stub for test_expired_token_refresh_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_client_error() -> None:
    """Stub for test_expired_token_refresh_client_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_refresh_reauth_error_during_setup() -> None:
    """Stub for test_token_refresh_reauth_error_during_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_refresh_transient_error_during_setup() -> None:
    """Stub for test_token_refresh_transient_error_during_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_refresh_error_during_setup() -> None:
    """Stub for test_token_refresh_error_during_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_info() -> None:
    """Stub for test_device_info."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""

