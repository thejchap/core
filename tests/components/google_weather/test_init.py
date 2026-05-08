"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_not_ready() -> None:
    """Stub for test_config_not_ready."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_auth_failed() -> None:
    """Stub for test_setup_auth_failed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

