"""Tryke skip-stubs for teslemetry/test_update.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def update() -> None:
    """Stub for test_update."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def update_alt() -> None:
    """Stub for test_update_alt."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def update_services() -> None:
    """Stub for test_update_services."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def update_streaming() -> None:
    """Stub for test_update_streaming."""

