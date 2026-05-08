"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_entry_v1_v2() -> None:
    """Stub for test_migrate_entry_v1_v2."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_entry_v1_v2_invalid_time() -> None:
    """Stub for test_migrate_entry_v1_v2_invalid_time."""

