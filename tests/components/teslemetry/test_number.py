"""Tryke skip-stubs for teslemetry/test_number.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def number() -> None:
    """Stub for test_number."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def number_services() -> None:
    """Stub for test_number_services."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def number_streaming() -> None:
    """Stub for test_number_streaming."""

