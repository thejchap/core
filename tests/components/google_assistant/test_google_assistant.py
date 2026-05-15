"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sync_request() -> None:
    """Stub for test_sync_request (port deferred)."""

@test.skip("pending tryke port")
async def query_request() -> None:
    """Stub for test_query_request (port deferred)."""

@test.skip("pending tryke port")
async def query_climate_request() -> None:
    """Stub for test_query_climate_request (port deferred)."""

@test.skip("pending tryke port")
async def query_climate_request_f() -> None:
    """Stub for test_query_climate_request_f (port deferred)."""

@test.skip("pending tryke port")
async def query_humidifier_request() -> None:
    """Stub for test_query_humidifier_request (port deferred)."""

@test.skip("pending tryke port")
async def execute_request() -> None:
    """Stub for test_execute_request (port deferred)."""
