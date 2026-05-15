"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensor() -> None:
    """Stub for test_sensor (port deferred)."""

@test.skip("pending tryke port")
async def retry_with_no_error() -> None:
    """Stub for test_retry_with_no_error (port deferred)."""

@test.skip("pending tryke port")
async def retry_with_less_than_max_errors() -> None:
    """Stub for test_retry_with_less_than_max_errors (port deferred)."""

@test.skip("pending tryke port")
async def retry_with_more_than_max_errors() -> None:
    """Stub for test_retry_with_more_than_max_errors (port deferred)."""

@test.skip("pending tryke port")
async def retry_with_empty_status() -> None:
    """Stub for test_retry_with_empty_status (port deferred)."""
