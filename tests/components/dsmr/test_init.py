"""Tryke skip stubs for test_init - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_unique_id() -> None:
    """Stub for test_migrate_unique_id (port deferred)."""


