"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload() -> None:
    """Stub for test_load_unload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def init_failure() -> None:
    """Stub for test_init_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready_auth_error() -> None:
    """Stub for test_config_entry_not_ready_auth_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migration_from() -> None:
    """Stub for test_migration_from."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migration_from_with_error() -> None:
    """Stub for test_migration_from_with_error."""

