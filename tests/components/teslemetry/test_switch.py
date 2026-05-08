"""Tryke skip-stubs for teslemetry/test_switch.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def switch() -> None:
    """Stub for test_switch."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def switch_alt() -> None:
    """Stub for test_switch_alt."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def switch_services() -> None:
    """Stub for test_switch_services."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def switch_streaming() -> None:
    """Stub for test_switch_streaming."""

