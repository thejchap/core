"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_success() -> None:
    """Stub for test_setup_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def create_folder_if_missing() -> None:
    """Stub for test_create_folder_if_missing."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_error() -> None:
    """Stub for test_setup_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_success() -> None:
    """Stub for test_expired_token_refresh_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_failure() -> None:
    """Stub for test_expired_token_refresh_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""

