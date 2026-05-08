"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_refresh_failure() -> None:
    """Stub for test_token_refresh_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_refresh_success() -> None:
    """Stub for test_token_refresh_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_requires_reauth() -> None:
    """Stub for test_token_requires_reauth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_update_coordinator_failure() -> None:
    """Stub for test_device_update_coordinator_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_update_coordinator_reauth() -> None:
    """Stub for test_device_update_coordinator_reauth."""

