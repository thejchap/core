"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cannot_access_file() -> None:
    """Stub for test_cannot_access_file."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def not_valid_path_to_file() -> None:
    """Stub for test_not_valid_path_to_file."""

