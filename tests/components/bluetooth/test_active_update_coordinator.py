"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def basic_usage() -> None:
    """Stub for test_basic_usage (port deferred)."""

@test.skip("pending tryke port")
async def bleak_error_during_polling() -> None:
    """Stub for test_bleak_error_during_polling (port deferred)."""

@test.skip("pending tryke port")
async def generic_exception_during_polling() -> None:
    """Stub for test_generic_exception_during_polling (port deferred)."""

@test.skip("pending tryke port")
async def polling_debounce() -> None:
    """Stub for test_polling_debounce (port deferred)."""

@test.skip("pending tryke port")
async def polling_debounce_with_custom_debouncer() -> None:
    """Stub for test_polling_debounce_with_custom_debouncer (port deferred)."""

@test.skip("pending tryke port")
async def polling_rejecting_the_first_time() -> None:
    """Stub for test_polling_rejecting_the_first_time (port deferred)."""

@test.skip("pending tryke port")
async def no_polling_after_stop_event() -> None:
    """Stub for test_no_polling_after_stop_event (port deferred)."""
