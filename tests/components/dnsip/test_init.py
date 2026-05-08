"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def port_migration() -> None:
    """Stub for test_port_migration."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remove_unique_id_migration() -> None:
    """Stub for test_remove_unique_id_migration."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_error_from_future() -> None:
    """Stub for test_migrate_error_from_future."""

