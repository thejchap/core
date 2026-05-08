"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_to_version_2() -> None:
    """Stub for test_migration_to_version_2."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_future_version() -> None:
    """Stub for test_migration_from_future_version."""

