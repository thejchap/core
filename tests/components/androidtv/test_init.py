"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_version() -> None:
    """Stub for test_migrate_version."""

