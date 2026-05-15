"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def ok_requests() -> None:
    """Stub for test_ok_requests (port deferred)."""

@test.skip("pending tryke port")
async def bad_requests() -> None:
    """Stub for test_bad_requests (port deferred)."""

@test.skip("pending tryke port")
async def bad_requests_with_unsafe_bytes() -> None:
    """Stub for test_bad_requests_with_unsafe_bytes (port deferred)."""
