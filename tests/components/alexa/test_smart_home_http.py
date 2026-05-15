"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def http_api() -> None:
    """Stub for test_http_api (port deferred)."""

@test.skip("pending tryke port")
async def http_api_disabled() -> None:
    """Stub for test_http_api_disabled (port deferred)."""
