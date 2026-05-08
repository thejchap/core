"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the google_sheets integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.google_sheets.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("google_sheets")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_success() -> None:
    """Stub for test_setup_success (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def missing_required_scopes_requires_reauth() -> None:
    """Stub for test_missing_required_scopes_requires_reauth (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_success() -> None:
    """Stub for test_expired_token_refresh_success (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_failure() -> None:
    """Stub for test_expired_token_refresh_failure (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_oauth_reauth_error() -> None:
    """Stub for test_setup_oauth_reauth_error (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_oauth_transient_error() -> None:
    """Stub for test_setup_oauth_transient_error (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def append_sheet() -> None:
    """Stub for test_append_sheet (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_sheet() -> None:
    """Stub for test_get_sheet (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def append_sheet_multiple_rows() -> None:
    """Stub for test_append_sheet_multiple_rows (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def append_sheet_api_error() -> None:
    """Stub for test_append_sheet_api_error (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def append_sheet_invalid_config_entry() -> None:
    """Stub for test_append_sheet_invalid_config_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_sheet_invalid_config_entry() -> None:
    """Stub for test_get_sheet_invalid_config_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_sheet_invalid_worksheet() -> None:
    """Stub for test_get_sheet_invalid_worksheet (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available (port deferred)."""


