"""Tryke skip-stubs for teslemetry/test_cover.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def cover() -> None:
    """Stub for test_cover."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def cover_alt() -> None:
    """Stub for test_cover_alt."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def cover_noscope() -> None:
    """Stub for test_cover_noscope."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def cover_services() -> None:
    """Stub for test_cover_services."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def cover_streaming() -> None:
    """Stub for test_cover_streaming."""

