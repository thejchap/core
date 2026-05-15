"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_not_ready() -> None:
    """Stub for test_setup_not_ready (port deferred)."""

@test.skip("pending tryke port")
async def setup_not_ready_authkey_required() -> None:
    """Stub for test_setup_not_ready_authkey_required (port deferred)."""

@test.skip("pending tryke port")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("pending tryke port")
async def migrate_V0() -> None:
    """Stub for test_migrate_V0 (port deferred)."""

@test.skip("pending tryke port")
async def migrate() -> None:
    """Stub for test_migrate (port deferred)."""

@test.skip("pending tryke port")
async def migrate_v3_to_v4() -> None:
    """Stub for test_migrate_v3_to_v4 (port deferred)."""
