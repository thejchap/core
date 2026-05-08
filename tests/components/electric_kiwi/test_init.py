"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_multiple_entries() -> None:
    """Stub for test_async_setup_multiple_entries."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def refresh_token_validity_failures() -> None:
    """Stub for test_refresh_token_validity_failures."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unique_id_migration() -> None:
    """Stub for test_unique_id_migration."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unique_id_migration_failure() -> None:
    """Stub for test_unique_id_migration_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unique_id_migration_auth_failure() -> None:
    """Stub for test_unique_id_migration_auth_failure."""

