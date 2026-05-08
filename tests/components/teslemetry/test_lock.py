"""Tryke skip-stubs for teslemetry/test_lock.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def lock() -> None:
    """Stub for test_lock."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def lock_alt() -> None:
    """Stub for test_lock_alt."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def lock_services() -> None:
    """Stub for test_lock_services."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def lock_streaming() -> None:
    """Stub for test_lock_streaming."""

