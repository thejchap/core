"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_success() -> None:
    """Stub for test_expired_token_refresh_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_failure() -> None:
    """Stub for test_expired_token_refresh_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_init_failure() -> None:
    """Stub for test_coordinator_init_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_implementation_unavailable() -> None:
    """Stub for test_setup_entry_implementation_unavailable."""

