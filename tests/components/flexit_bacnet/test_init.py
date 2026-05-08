"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def loading_and_unloading_config_entry() -> None:
    """Stub for test_loading_and_unloading_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def failed_initialization() -> None:
    """Stub for test_failed_initialization."""

