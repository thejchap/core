"""Tryke skip-stubs for tesla_fleet/test_lock.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def lock() -> None:
    """Stub for test_lock."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def lock_offline() -> None:
    """Stub for test_lock_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def lock_services() -> None:
    """Stub for test_lock_services."""

