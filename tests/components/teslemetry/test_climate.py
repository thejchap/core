"""Tryke skip-stubs for teslemetry/test_climate.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def climate() -> None:
    """Stub for test_climate."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def climate_alt() -> None:
    """Stub for test_climate_alt."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def invalid_error() -> None:
    """Stub for test_invalid_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def errors() -> None:
    """Stub for test_errors."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def ignored_error() -> None:
    """Stub for test_ignored_error."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def climate_noscope() -> None:
    """Stub for test_climate_noscope."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def select_streaming() -> None:
    """Stub for test_select_streaming."""

