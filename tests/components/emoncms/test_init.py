"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def failure() -> None:
    """Stub for test_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_uuid() -> None:
    """Stub for test_migrate_uuid."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_uuid() -> None:
    """Stub for test_no_uuid."""

