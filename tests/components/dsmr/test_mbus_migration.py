"""Tryke skip stubs for test_mbus_migration - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_gas_to_mbus() -> None:
    """Stub for test_migrate_gas_to_mbus (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_hourly_gas_to_mbus() -> None:
    """Stub for test_migrate_hourly_gas_to_mbus (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_gas_with_devid_to_mbus() -> None:
    """Stub for test_migrate_gas_with_devid_to_mbus (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_gas_to_mbus_exists() -> None:
    """Stub for test_migrate_gas_to_mbus_exists (port deferred)."""


