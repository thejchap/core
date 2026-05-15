"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def basic_usage() -> None:
    """Stub for test_basic_usage (port deferred)."""

@test.skip("pending tryke port")
async def poll_can_be_skipped() -> None:
    """Stub for test_poll_can_be_skipped (port deferred)."""

@test.skip("pending tryke port")
async def bleak_error_and_recover() -> None:
    """Stub for test_bleak_error_and_recover (port deferred)."""

@test.skip("pending tryke port")
async def poll_failure_and_recover() -> None:
    """Stub for test_poll_failure_and_recover (port deferred)."""

@test.skip("pending tryke port")
async def second_poll_needed() -> None:
    """Stub for test_second_poll_needed (port deferred)."""

@test.skip("pending tryke port")
async def rate_limit() -> None:
    """Stub for test_rate_limit (port deferred)."""

@test.skip("pending tryke port")
async def no_polling_after_stop_event() -> None:
    """Stub for test_no_polling_after_stop_event (port deferred)."""
