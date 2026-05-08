"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload_on_title_change() -> None:
    """Stub for test_reload_on_title_change."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_to_version_2() -> None:
    """Stub for test_migration_to_version_2."""

