"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def successful_config_entry() -> None:
    """Stub for test_successful_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_error() -> None:
    """Stub for test_setup_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

